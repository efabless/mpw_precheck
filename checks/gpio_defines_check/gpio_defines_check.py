# SPDX-FileCopyrightText: 2022 Efabless Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# SPDX-License-Identifier: Apache-2.0

#
# How it works:
#
# We 'sandwich' User's verilog/rtl/user_defines.v between two asset files: 
#      gpio_modes_base.v, verilog/rtl/user_defines.v gpio_modes_observe.v
# and parse this triplet of files.
#
# 1. The base has: hex-value `defines GPIO_MODE_*, and: for <int> 5...37:
#      `define USER_CONFIG_GPIO_<int>_INIT  `GPIO_MODE_INVALID
#
# 2. User's user_defines.v (in the middle) REQUIRED to re-define USER_CONFIG_GPIO_<int>_INIT
#    to real hex-values.
#
# 3. Then the observe.v has wires initialized to corresponding USER_CONFIG_GPIO_<int>_INIT defines:
#      wire [12:0]USER_CONFIG_GPIO_<int>_INIT  = `USER_CONFIG_GPIO_<int>_INIT;
#
# By parsing the triplet of files (which pass thru iverilog preprocessor), and walking the wires
# that result, we can check if the values assigned are still the illegal/placeholder or a valid hex.
#

import argparse
import logging
import os
import re
import sys
from pathlib import Path
from pyverilog.vparser.parser import ParseError, parse

# Choosen illegal value for `USER_CONFIG_GPIO_<int>_INIT directives.
VAL_ILLEGAL = "13'hXXXX"  # consistent with, in gpio_modes_base.v : `define GPIO_MODE_INVALID 13'hXXXX
VAL_ILLEGAL_CF = VAL_ILLEGAL.casefold()
LEGALREX = re.compile("^13'[hH][0-9a-fA-F]+$")  # matches a 'good' 13-bit hex-literal (no X's)

# compile REX just once.
MODREX = re.compile("^__gpioModeObserve[0-9]+$")
WIRREX = re.compile("^USER_CONFIG_GPIO_([0-9]+)_INIT$")  # get index by: .match().group(1)

# local assets, the outsides of the sandwich.
PRE_V = [Path(__file__).parent / "verilog_assets/gpio_modes_base.v"]
POST_V = [Path(__file__).parent / "verilog_assets/gpio_modes_observe.v"]


def main(*args, **kwargs):
    input_directory = kwargs["input_directory"]
    output_directory = kwargs["output_directory"]
    project_type = kwargs["project_type"]
    user_defines_v = kwargs["user_defines_v"]
    include_extras_v = kwargs["include_extras"]
    errs = 0

    gpio_defines_report = output_directory / 'outputs/reports/gpio_defines.report'

    # for includes_extras_v & user_defines_v: if relative: make absolute RELATIVE TO INPUT_DIRECTORY (user project root)
    # (For pathlib the / (join) ignores the left-operand if right-operand already absolute.)
    user_defines_vf = input_directory / user_defines_v
    include_extras_vf = [input_directory / Path(f) for f in include_extras_v]

    # Verify/report if files not-readable in separate catagories: user's main defines, extra-includes, assets of the check.
    if not user_defines_vf.is_file() or not os.access(str(user_defines_vf), os.R_OK):
        logging.warning(f"{{{{GPIO-DEFINES: MAIN USER DEFINES FAIL}}}} {user_defines_vf} not readable.")
        errs += 1

    bad_files = []
    for p in include_extras_v:
        if not p.is_file() or not os.access(str(p), os.R_OK):
            bad_files.append(p)
    if bad_files:
        logging.warning(f"{{{{GPIO-DEFINES: INCLUDE EXTRAS FAIL}}}} {bad_files} file(s) not readable.")
        errs += len(bad_files)

    bad_files = []
    for p in [*PRE_V, *POST_V]:
        if not p.is_file() or not os.access(str(p), os.R_OK):
            bad_files.append(p)
    if bad_files:
        logging.warning(f"{{{{GPIO-DEFINES: ASSETS INTERNAL-FAIL}}}} {bad_files} check asset-file(s) not readable.")
        errs += len(bad_files)

    # any errors till now?: Stop/return now. No point in parsing known bad data.
    if errs:
        logging.fatal(f"{{{{GPIO-DEFINES: CHECK FAILED}}}} Fail due to {errs} error(s) reported above. No report generated.")
        return False

    # order the files to parse
    file_list = [*PRE_V, *include_extras_vf, user_defines_vf, *POST_V]
    file_list_p = [str(f) for f in file_list]
    logging.info(f"GPIO-DEFINES: to check {user_defines_v} parsing files: {file_list_p}")

    try:
        ast, _ = parse(file_list)
    except ParseError as e:
        # raise DataError(f"Parsing netlist(s) {file_list_p} failed2 because {str(e)}")
        logging.warning(f"{{{{GPIO-DEFINES: PARSE NETLISTS FAILED}}}} The files fail parsing(2) because: {{{str(e)}}}, did you?: `undef USER_CONFIG_GPIO_<int>_INIT")
        errs += 1
    except RuntimeError as e:
        # raise DataError(f"Parsing netlist(s) {file_list_p} failed because {str(e)}")
        logging.warning(f"{{{{GPIO-DEFINES: PARSE NETLISTS FAILED}}}} The files fail parsing because: {{{str(e)}}}")
        errs += 1
    except Exception as e:  # any other exception...
        # raise DataError(f"Parsing netlist(s) {file_list_p} failed3 because {str(e)}")
        logging.warning(f"{{{{GPIO-DEFINES: PARSE NETLISTS FAILED}}}} The files netlists fail parsing(3) because: {{{str(e)}}}")
        errs += 1

    # any errors till now?: Stop/return now. No useful parse-result.
    if errs:
        logging.fatal(f"{{{{GPIO-DEFINES: CHECK FAILED}}}} Fail due to {errs} error(s) reported above. No report generated.")
        return False

    # ast, directives = parse(...)
    # ast.show()
    ## Directives not useful: very few retained after preprocessor. e.g. `timescale ...
    # for lineno, directive in directives:
    #   print('Line %d : %s' % (lineno, directive))

    # search for all modules matching names: "^__gpioModeObserve[0-9]+$"
    mods = []
    modsNm = []
    for d in ast.description.definitions:
        def_type = type(d).__name__
        if def_type == 'ModuleDef':
            if MODREX.match(d.name):
                mods.append(d)
                modsNm.append(d.name)
    # print(f"module matches found: {modsNm}")

    # Sample parse-dumps for one line (but after preprocessor replaced directives):
    #   `define USER_CONFIG_GPIO_15_INIT 13'h0000
    #    wire [12:0]USER_CONFIG_GPIO_15_INIT = `USER_CONFIG_GPIO_15_INIT;
    # ->
    #      Decl:  (at 101)
    #        Wire: USER_CONFIG_GPIO_15_INIT, False (at 101)
    #          Width:  (at 101)
    #            IntConst: 12 (at 101)
    #            IntConst: 0 (at 101)
    #        Assign:  (at 101)
    #          Lvalue:  (at 101)
    #            Identifier: USER_CONFIG_GPIO_15_INIT (at 101)
    #          Rvalue:  (at 101)
    #            IntConst: 13'h0000 (at 101)
    #
    # `define USER_CONFIG_GPIO_18_INIT some_sig
    #  wire [12:0]USER_CONFIG_GPIO_18_INIT = `USER_CONFIG_GPIO_18_INIT;
    # ->
    #      Decl:  (at 163)
    #        Wire: USER_CONFIG_GPIO_18_INIT, False (at 163)
    #          Width:  (at 163)
    #            IntConst: 12 (at 163)
    #            IntConst: 0 (at 163)
    #        Assign:  (at 163)
    #          Lvalue:  (at 163)
    #            Identifier: USER_CONFIG_GPIO_18_INIT (at 163)
    #          Rvalue:  (at 163)
    #            Identifier: some_sig (at 163)

    # Form set of the USER_CONFIG_GPIO_*_INIT indexes we require. Different for caravel vs caravan.
    want = {i for i in range(5, 38)}
    if project_type['type'] == 'analog':
        # For caravan, the span 15...25 is a don't care.
        list(want.remove(i) for i in range(15, 26))

    wantLen = len(want)
    ills = []
    valids = {}

    # walk items in each found module; look for target wires: Check right-hand value of wire intialization.
    for d in mods:
        for i in d.items:
            if 'Decl' == type(i).__name__ and len(i.list) == 2:
                i0 = i.list[0]  # Wire   ...
                i1 = i.list[1]  # Assign ...
                if 'Wire' == type(i0).__name__ and 'Assign' == type(i1).__name__:
                    wname = i0.name
                    match = WIRREX.match(wname)  # match to?: USER_CONFIG_GPIO_<int>_INIT
                    if match:
                        windexS = match.group(1)  # get the "<int>"
                        windex = int(windexS)
                        if windex in want:  # Is it an index we're looking for?
                            want.remove(windex)
                            val = "<error-unrecognized>"
                            # trap AttributeError "... has no attribute 'value'" like from:
                            try:
                                val = i1.right.var.value
                            except:
                                try:
                                    val = str(i1.right.var)
                                except:
                                    pass

                            # print(f"wire.name={i0.name}  index={windex}  val={val}  type(val)={type(val)}")
                            if val.casefold() == VAL_ILLEGAL_CF:  # 13'h0000
                                ills.append(f"{wname}={val}")
                            elif not LEGALREX.match(val):
                                ills.append(f"{wname}={val}")
                            else:
                                valids[windex] = [wname, val]

    missing_length = len(want)  # remaining wires we did not find
    illegals_length = len(ills)  # wires found with illegal initialization value.
    # print(f"wanted:{wantLen}  missing:{missing_length}  illegal:{illegals_length}")

    msgs = []
    if missing_length:
        # print(f"missing:{want}")
        missWires = list(f"USER_CONFIG_GPIO_{i}_INIT" for i in want)
        msgs += [f"Internal-error, parse didn't yield expected wires({missing_length}) for: " + ' '.join(missWires) + "."]

    if illegals_length:
        # print(f"illegals:{ills}")
        msgs += [f"Directives({illegals_length}) still placeholder ({VAL_ILLEGAL}) or not hex-literal: " + ' '.join(ills) + "."]
    if msgs:
        msg = ' '.join(msgs)
        # print( "ERROR: user_defines.v: " + msg, file=sys.stderr)
        logging.fatal(f"{{{{GPIO-DEFINES: ERROR IN {user_defines_v}}}}} {msg}. No report generated.")
        return False

    # generate report. simply lines like: USER_CONFIG_GPIO_<int>_INIT  <val>
    w0 = 26  # pad column-1 to this width; to align values in col-2
    try:
        with open(gpio_defines_report, 'w') as rpt:
            for i in range(5, 38):
                if i in valids:
                    pair = valids[i]
                    rpt.write(f"{pair[0]: <{w0}} {pair[1]}\n")
    except Exception as e:  # any other exception...
        logging.fatal(f"{{{{GPIO-DEFINES: ERROR IN writing report {gpio_defines_report}}}}} because: {{{str(e)}}}")
        return False

    logging.info(f"{{{{GPIO-DEFINES: wrote report {gpio_defines_report}}}}}")
    return True  # pass


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format=f"%(asctime)s | %(levelname)-7s | %(message)s", datefmt='%d-%b-%Y %H:%M:%S')
    parser = argparse.ArgumentParser(description="Runs gpio defines (verilog directives) check on the user project 'verilog/rtl/user_defines.v' netlist.")
    parser.add_argument("--input_directory", "-i", required=True, help="Path to the project folder")
    parser.add_argument("--output_directory", "-o", required=True, help="Path to the output directory")
    parser.add_argument("--project_type", "-um", required=True, help="Project type (analog/digital)")

    # Define the MAIN TARGET of the check (with a default):
    parser.add_argument("--user_defines_file", "-udef", required=False, default="verilog/rtl/user_defines.v",
                        help="Main user-project file of `defines to check. If relative, it's relative to input_directory (user project root).")

    # Due action='append' the include_file is an array.
    # We DO NOT exploit default=... here (in place of above user_defines_file option). The action='append' reportedly
    # would just add to the existing default; but then no way to override/replace the default.
    parser.add_argument("--include_file", "-inc", action='append', required=False,
                        help="Extra .v file to include BEFORE user_defines_file, relative to input_directory (user project root). Repeatable as needed.")
    args = parser.parse_args()

    result = main(input_directory=Path(args.input_directory),
                  output_directory=Path(args.output_directory),
                  project_type=args.project_type,
                  user_defines_v=Path(args.user_defines_file),
                  include_extras=args.include_file)

    if result:
        logging.info("The provided netlist passes GPIO-DEFINES check.")
    else:
        logging.warning("The provided netlist fails GPIO-DEFINES check.")
