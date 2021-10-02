# SPDX-FileCopyrightText: 2020 Efabless Corporation
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

import argparse
import logging
import os
import sys
from pathlib import Path

try:
    from checks.consistency_check.netlist_checker import NetlistChecker, NetlistChecks
    from checks.consistency_check.parsers.layout_parser import LayoutParser
    from checks.consistency_check.parsers.netlist_parser import DataError, get_netlist_parser, VerilogParser
except ImportError:
    from netlist_checker import NetlistChecker, NetlistChecks
    from parsers.layout_parser import LayoutParser
    from parsers.netlist_parser import DataError, get_netlist_parser, VerilogParser

# pdk specific
PDK = "sky130_fd_sc"
PREPROCESS_DEFINES = ["USE_POWER_PINS"]
LIBS = ["hd", "hdll", "hs", "lp", "ls", "ms", "hvl"]

# caravel specific
IGNORED_POWER_CELLS = ["caravan_power_routing", "caravel_power_routing"]
IGNORED_TEXT_BLOCKS = ["copyright_block", "copyright_block_a", "open_source", "user_id_textblock"]
CORE_SIDE_POWER = [net + "_core" for net in ["vccd", "vccd1", "vccd2", "vdda1", "vdda2", "vssa", "vssa1", "vssa2", "vssd", "vssd1", "vssd2"]]
MGMT_POWER = ["vccd", "vdda", "vddio", "vssa", "vssd", "vssio"]
USER_BANNED_POWER = MGMT_POWER + [net + "_core" for net in MGMT_POWER]
USER_POWER_PINS = ["vccd1", "vccd2", "vdda1", "vdda2", "vssa1", "vssa2", "vssd1", "vssd2"]
PHYSICAL_CELLS = ["decap", "diode", "fakediode", "fill", "fill_diode", "tapvpwrvgnd"]


def main(*args, **kwargs):
    input_directory = kwargs["input_directory"]
    output_directory = kwargs["output_directory"]
    project_config = kwargs["project_config"]
    golden_wrapper_netlist = kwargs["golden_wrapper_netlist"]
    defines_file_path = kwargs["defines_file_path"]

    for path in [input_directory, project_config['user_netlist'], project_config['top_netlist'], golden_wrapper_netlist, defines_file_path]:
        if not path.exists():
            logging.warning(f"{{{{CONSISTENCY CHECK FAILED}}}} {path.name} file was not found.")
            return False

    include_files = [str(defines_file_path)]
    netlist_type = project_config['netlist_type']
    user_netlist = project_config['user_netlist']
    top_netlist = project_config['top_netlist']
    user_module = project_config['user_module']
    top_module = project_config['top_module']

    top_module_checks = [NetlistChecks.power, NetlistChecks.hierarchy, NetlistChecks.complexity, NetlistChecks.modeling, NetlistChecks.submodule_hooks]
    user_module_checks = [NetlistChecks.power, NetlistChecks.ports, NetlistChecks.complexity, NetlistChecks.modeling, NetlistChecks.layout]

    if netlist_type == "verilog":
        # Filter physical cells from the verilog netlist to speed up parsing
        filtered_user_netlist = output_directory / 'outputs' / f"{user_module}.filtered.v"
        VerilogParser.remove_cells(user_netlist, filtered_user_netlist, PHYSICAL_CELLS)
        user_netlist = filtered_user_netlist
        # The port type check is enabled only for verilog netlists
        user_module_checks.append(NetlistChecks.port_types)

    # Parse netlists (spice/verilog)
    try:
        top_netlist_parser = get_netlist_parser(top_netlist, top_module, netlist_type, include_files=include_files, preprocess_define=PREPROCESS_DEFINES)
        user_netlist_parser = get_netlist_parser(user_netlist, user_module, netlist_type, include_files=include_files, preprocess_define=PREPROCESS_DEFINES)
        golden_wrapper_parser = VerilogParser(golden_wrapper_netlist, user_module, include_files=include_files, preprocess_define=PREPROCESS_DEFINES)
    except DataError as e:
        logging.fatal(f"{{{{PARSING NETLISTS FAILED}}}} The provided {netlist_type} netlists fail parsing because: {str(e)}")
        return False

    # Parse layout
    user_wrapper_gds = input_directory / "gds" / f"{user_module}.gds"
    try:
        user_layout_parser = LayoutParser(user_wrapper_gds, user_module)
    except (DataError, RuntimeError) as e:
        logging.fatal(f"{{{{PARSING LAYOUT FAILED}}}} The {user_module} layout fails parsing because: {str(e)}")
        return False

    # Run Consistency Checks
    top_module_ignored_cells = IGNORED_POWER_CELLS + IGNORED_TEXT_BLOCKS
    user_module_ignored_cells = [f"{PDK}_{lib}__{cell}_{n}" for cell in PHYSICAL_CELLS for lib in LIBS for n in range(0, 13)]

    top_netlist_checker = NetlistChecker(top_netlist_parser, golden_wrapper_parser=golden_wrapper_parser)
    user_netlist_checker = NetlistChecker(user_netlist_parser, user_layout_parser, golden_wrapper_parser)

    top_netlist_check = top_netlist_checker.check(checks=top_module_checks, min_instances=8,
                                                  power_nets=CORE_SIDE_POWER, ignored_instances=top_module_ignored_cells, submodule=user_module,
                                                  submodule_power=USER_POWER_PINS, submodule_banned_power=USER_BANNED_POWER)
    user_netlist_check = user_netlist_checker.check(checks=user_module_checks, min_instances=1,
                                                    power_nets=USER_POWER_PINS, ignored_instances=user_module_ignored_cells)

    result = top_netlist_check and user_netlist_check
    return result


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format=f"%(asctime)s | %(levelname)-7s | %(message)s", datefmt='%d-%b-%Y %H:%M:%S')
    parser = argparse.ArgumentParser(description="Runs consistency checks on the top and the user structural netlists.")
    parser.add_argument("--input_directory", "-i", required=True, help="Path to the project folder")
    parser.add_argument("--output_directory", "-o", required=True, help="Path to the output directory")
    parser.add_argument("--top_netlist", "-tn", required=True, help="User structural netlist (.v or .spice)")
    parser.add_argument("--user_netlist", "-un", required=True, help="User structural netlist (.v or .spice)")
    parser.add_argument("--golden_netlist", "-gn", required=True, help="Golden user wrapper structural netlist (.v)")
    parser.add_argument("--top_module", "-tm", required=True, help="Top module name")
    parser.add_argument("--user_module", "-um", required=True, help="User module name")
    parser.add_argument("--include_files", "-inc", required=False, help="Extra (.v) files to include for preprocessing the netlist.")
    parser.add_argument("--run_gds_fc", "-rf", required=False, action='store_true', help="Run gds consistency checks.")
    args = parser.parse_args()

    top_netlist = Path(args.top_netlist)
    user_netlist = Path(args.user_netlist)
    top_module = args.top_module
    user_module = args.user_module
    top_netlist_extension = os.path.splitext(top_netlist)[1]
    user_netlist_extension = os.path.splitext(user_netlist)[1]
    if top_netlist_extension == ".v" and user_netlist_extension == ".v":
        netlist_type = "verilog"
    elif top_netlist_extension == ".spice" and user_netlist_extension == ".spice":
        netlist_type = "spice"
    else:
        logging.fatal("Please provide a verilog (.v) / a spice (.spice) structural netlist.")
        sys.exit(1)

    project_config = {
        'top_netlist': top_netlist,
        'user_netlist': user_netlist,
        'top_module': top_module,
        'user_module': user_module,
        'netlist_type': netlist_type
    }
    result = main(input_directory=Path(args.input_directory),
                  output_directory=Path(args.output_directory),
                  project_config=project_config,
                  golden_wrapper_netlist=Path(args.golden_netlist),
                  defines_file_path=args.include_files,
                  run_gds_fc=args.run_gds_fc)

    if result:
        logging.info("The provided netlists pass consistency checks.")
    else:
        logging.warning("The provided netlists fail consistency checks.")
