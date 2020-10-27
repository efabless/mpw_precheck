# Copyright 2020 Efabless Corporation
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

import argparse
import subprocess
import sys
import base_checks.check_license as check_license
import base_checks.check_yaml as check_yaml
import consistency_checks.consistency_checker as consistency_checker
import drc_checks.gds_drc_checker as gds_drc_checker


parser = argparse.ArgumentParser(
    description='Runs the precheck tool by calling the various checks in order.')

parser.add_argument('--target_path', '-t', required=True,
                    help='Absolute Path to the project.')

parser.add_argument('--spice_netlist', '-s', nargs='+', default=[],
                    help='Spice Netlists: toplvl.spice user_module.spice, both should be in /target_path')

parser.add_argument('--verilog_netlist', '-v', nargs='+', default=[],
                    help='Verilog Netlist: toplvl.v user_module.v , both should be in /target_path')

parser.add_argument('--output_directory', '-o', required=False,
                    help='Output Directory, defaults to /target_path/checks')

parser.add_argument('--waive_fuzzy_checks', '-wfs',action='store_true', default=False,
                help="Specifies whether or not to waive fuzzy consistency checks.")

parser.add_argument('--skip_drc', '-sd',action='store_true', default=False,
                help="Specifies whether or not to skip DRC checks.")


args = parser.parse_args()
target_path = args.target_path
verilog_netlist = args.verilog_netlist
spice_netlist = args.spice_netlist
if args.output_directory is None:
    output_directory = str(target_path)+ '/checks'
else:
    output_directory = args.output_directory

if verilog_netlist is not None:
    verilog_netlist = [str(target_path)+'/'+str(v) for v in verilog_netlist]
if spice_netlist is not None:
    spice_netlist = [str(target_path)+'/'+str(s) for s in spice_netlist]

# Decompress project items and copies all GDS-II files to top level.
run_prep_cmd = "cd {target_path}; make uncompress; cp */*.gds .;".format(
    target_path = target_path
)

process = subprocess.Popen(run_prep_cmd,stdout=subprocess.PIPE, shell=True)
proc_stdout = process.communicate()[0].strip()

# Step 1: Check LICENSE.
if check_license.check_main_license(target_path):
    print("APACHE-2.0 LICENSE exists in target path")
else:
    print("APACHE-2.0 LICENSE is Not Found in target path")
    exit(255)

third_party_licenses=  check_license.check_lib_license(str(target_path)+'/third-party/')

if len(third_party_licenses):
    for key in third_party_licenses:
        if third_party_licenses[key] == False:
            print("Third Party", str(key),"License Not Found")
            exit(255)
    print("Third Party Licenses Found")
else:
    print("No third party libraries found.")

# Step 2: Check YAML description.
if check_yaml.check_yaml(target_path):
    print("YAML file valid!")
else:
    print("YAML file not valid in target path")
    exit(255)

# Step 3: Check Fuzzy Consistency.
check, reason = consistency_checker.fuzzyCheck(target_path=target_path,spice_netlist=spice_netlist,verilog_netlist=verilog_netlist,output_directory=output_directory,waive_consistency_checks=args.waive_fuzzy_checks)
if check:
    print("Fuzzy Consistency Checks Passed!")
else:
    print("Fuzzy Consistency Checks Failed, Reason: ", reason)
    exit(255)

# Step 4: Not Yet Implemented.

# Step 5: Perform DRC checks on the GDS.
# assumption that we'll always be using a caravel top module based on what's on step 3
if args.skip_drc:
    print("Skipping DRC Checks...")
else:
    check, reason = gds_drc_checker.gds_drc_check(target_path, 'caravel', output_directory)

    if check:
        print("DRC Checks on GDS-II Passed!")
    else:
        print("DRC Checks on GDS-II Failed, Reason: ", reason)
        exit(255)

# Step 6: Not Yet Implemented.
# Step 7: Not Yet Implemented.
print("All Checks PASSED!")
