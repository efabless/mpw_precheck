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
import os.path
import base_checks.check_license as check_license
import base_checks.check_yaml as check_yaml
import consistency_checks.consistency_checker as consistency_checker
import drc_checks.gds_drc_checker as gds_drc_checker
from utils.utils import *

def run_check_sequence(target_path, top_level_netlist, user_level_netlist, output_directory=None,waive_fuzzy_checks=False,skip_drc=False):
    if output_directory is None:
        output_directory = str(target_path)+ '/checks'

    verilog_netlist = []
    spice_netlist = []

    toplvl_extension = os.path.splitext(top_level_netlist)[1]
    userlvl_extension = os.path.splitext(user_level_netlist)[1]
    if str(toplvl_extension) == '.v' and str(userlvl_extension) == '.v':
        verilog_netlist = [ str(target_path) + '/'+str(top_level_netlist),  str(target_path) + '/'+str(user_level_netlist)]
    elif str(toplvl_extension) == '.spice' and str(userlvl_extension) == '.spice':
        spice_netlist = [ str(target_path) + '/'+str(top_level_netlist),  str(target_path) + '/'+str(user_level_netlist)]
    else:
        print_control("{{ERROR}} the provided top level and user level netlists are neither a .spice or a .v files. Please adhere to the required input type.")
        exit_control(255)

    steps = 4 - int(skip_drc) - int(waive_fuzzy_checks)
    stp_cnt = 0

    print_control("{{PROGRESS}} Executing Step "+ str(stp_cnt)+ " of "+ str(steps)+ ": Uncompressing the gds files")
    # Decompress project items and copies all GDS-II files to top level.
    run_prep_cmd = "cd {target_path}; make uncompress; cp */*.gds .;".format(
        target_path = target_path
    )

    process = subprocess.Popen(run_prep_cmd,stdout=subprocess.PIPE, shell=True)
    proc_stdout = process.communicate()[0].strip()
    print_control("{{PROGRESS}} Step "+ str(stp_cnt)+ " done without fatal errors.")
    stp_cnt+=1

    # Step 1: Check LICENSE.
    print_control("{{PROGRESS}} Executing Step "+ str(stp_cnt)+ " of "+ str(steps)+ ": Checking License files.")
    if check_license.check_main_license(target_path):
        print_control("{{PROGRESS}} APACHE-2.0 LICENSE exists in target path")
    else:
        print_control("{{ERROR}} APACHE-2.0 LICENSE is Not Found in target path\nTEST FAILED AT STEP "+ str(stp_cnt))
        exit_control(255)

    third_party_licenses=  check_license.check_lib_license(str(target_path)+'/third-party/')

    if len(third_party_licenses):
        for key in third_party_licenses:
            if third_party_licenses[key] == False:
                print_control("{{ERROR}} Third Party"+ str(key),"License Not Found\nTEST FAILED AT STEP "+ str(stp_cnt))
                exit_control(255)
        print_control("{{PROGRESS}} Third Party Licenses Found.\nStep "+ str(stp_cnt)+ " done without fatal errors.")
    else:
        print_control("{{PROGRESS}} No third party libraries found.\nStep "+ str(stp_cnt)+ " done without fatal errors.")
    stp_cnt+=1


    # Step 2: Check YAML description.
    print_control("{{PROGRESS}} Executing Step "+ str(stp_cnt)+ " of "+ str(steps)+ ": Checking YAML description.")
    if check_yaml.check_yaml(target_path):
        print_control("{{PROGRESS}} YAML file valid!\nStep "+ str(stp_cnt)+ " done without fatal errors.")
    else:
        print_control("{{ERROR}} YAML file not valid in target path\nTEST FAILED AT STEP "+ str(stp_cnt))
        exit_control(255)
    stp_cnt+=1


    # Step 3: Check Fuzzy Consistency.
    print_control("{{PROGRESS}} Executing Step "+ str(stp_cnt)+ " of "+ str(steps)+ ": Executing Fuzzy Consistency Checks.")
    check, reason = consistency_checker.fuzzyCheck(target_path=target_path,spice_netlist=spice_netlist,verilog_netlist=verilog_netlist,output_directory=output_directory,waive_consistency_checks=waive_fuzzy_checks)
    if check:
        print_control("{{PROGRESS}} Fuzzy Consistency Checks Passed!\nStep "+ str(stp_cnt)+ " done without fatal errors.")
    else:
        print_control("{{ERROR}} Consistency Checks Failed+ Reason: "+ reason,"\nTEST FAILED AT STEP "+ str(stp_cnt))
        exit_control(255)
    stp_cnt+=1

    # Step 4: Not Yet Implemented.

    # Step 5: Perform DRC checks on the GDS.
    # assumption that we'll always be using a caravel top module based on what's on step 3
    print_control("{{PROGRESS}} Executing Step "+ str(stp_cnt)+ " of "+ str(steps)+ ": Checking DRC Violations.")
    if skip_drc:
        print_control("{{WARNING}} Skipping DRC Checks...")
    else:
        check, reason = gds_drc_checker.gds_drc_check(target_path, 'caravel', output_directory)

        if check:
            print_control("{{PROGRESS}} DRC Checks on GDS-II Passed!\nStep "+ str(stp_cnt)+ " done without fatal errors.")
        else:
            print_control("{{ERROR}} DRC Checks on GDS-II Failed, Reason: "+ reason+ "\nTEST FAILED AT STEP "+ str(stp_cnt))
            exit_control(255)
    stp_cnt+=1

    # Step 6: Not Yet Implemented.
    # Step 7: Not Yet Implemented.
    print_control("{{SUCCESS}} All Checks PASSED!")
    dump_full_log()




if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Runs the precheck tool by calling the various checks in order.')

    parser.add_argument('--target_path', '-t', required=True,
                        help='Absolute Path to the project.')

    parser.add_argument('--top_level_netlist', '-tn', required=True,
                        help="Netlist: toplvl.spice or toplvl.v should be in /target_path and could be spice or verilog (.spice or .v) as long as it's of the same type as user_level_netlist.")

    parser.add_argument('--user_level_netlist', '-un',  required=True,
                        help="Netlist: user_level_netlist.spice or user_level_netlist.v should be in /target_path and could be spice or verilog (.spice or .v) as long as it's of the same type as top_level_netlist.")

    parser.add_argument('--output_directory', '-o', required=False,
                        help='Output Directory, defaults to /target_path/checks')

    parser.add_argument('--waive_fuzzy_checks', '-wfc',action='store_true', default=False,
                    help="Specifies whether or not to waive fuzzy consistency checks.")

    parser.add_argument('--skip_drc', '-sd',action='store_true', default=False,
                    help="Specifies whether or not to skip DRC checks.")


    args = parser.parse_args()
    target_path = args.target_path
    top_level_netlist = args.top_level_netlist
    user_level_netlist =args.user_level_netlist
    skip_drc = args.skip_drc
    waive_fuzzy_checks = args.waive_fuzzy_checks

    run_check_sequence(target_path, top_level_netlist, user_level_netlist, args.output_directory,waive_fuzzy_checks,skip_drc)
