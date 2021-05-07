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

import sys
import os.path
import argparse
import subprocess
from utils.utils import *
import config
import base_checks.check_yaml as check_yaml
import base_checks.check_license as check_license
import base_checks.check_manifest as check_manifest
import base_checks.check_makefile as check_makefile
import base_checks.check_documentation as check_documentation
import drc_checks.gds_drc_checker as gds_drc_checker
import xor_checks.xor_checker as xor_checker
import consistency_checks.consistency_checker as consistency_checker

default_logger_path = '/usr/local/bin/full_log.log'
default_target_path = '/usr/local/bin/caravel/'


def parse_netlists(target_path, top_level_netlist, user_level_netlist, lc=logging_controller(default_logger_path, default_target_path)):
    verilog_netlist = []
    spice_netlist = []
    toplvl_extension = os.path.splitext(top_level_netlist)[1]
    userlvl_extension = os.path.splitext(user_level_netlist)[1]
    if str(toplvl_extension) == '.v' and str(userlvl_extension) == '.v':
        verilog_netlist = [str(target_path) + '/' + str(top_level_netlist), str(target_path) + '/' + str(user_level_netlist)]
    elif str(toplvl_extension) == '.spice' and str(userlvl_extension) == '.spice':
        spice_netlist = [str(target_path) + '/' + str(top_level_netlist), str(target_path) + '/' + str(user_level_netlist)]
    else:
        lc.print_control(
            "{{FAIL}} the provided top level and user level netlists are neither a .spice or a .v files. Please adhere to the required input type.")
        lc.exit_control(2)
    return verilog_netlist, spice_netlist

def get_project_type(top_level_netlist, user_level_netlist):
    if "caravel.v" in top_level_netlist and "user_project_wrapper.v" in user_level_netlist: 
        project_type = "digital"
    elif "caravan.v" in top_level_netlist and "user_analog_project_wrapper.v" in user_level_netlist: 
        project_type = "analog"
    else: 
        lc.print_control(
            "{{FAIL}} the provided top level and user level netlists are not correct. \n \
            The top level netlist should point to caravel.v if your project is digital or caravan.v if your project is analog. \n \
            The user_level_netlist should point to user_project_wrapper.v if your project is digital or user_analog_project_wrapper.v if your project is analog.")
        lc.exit_control(2)
    return project_type

def run_check_sequence(target_path, caravel_root, pdk_root, output_directory=None, run_fuzzy_checks=False, run_gds_fc=False, skip_drc=False, drc_only=False, dont_compress=False, manifest_source="master", run_klayout_drc=False):
    if output_directory is None:
        output_directory = str(target_path) + '/checks'
    # Create the logging controller
    lc = logging_controller(str(output_directory) + '/full_log.log', target_path, dont_compress)
    lc.create_full_log()

    steps = 5
    if drc_only:
        steps = 1
    elif run_fuzzy_checks or run_klayout_drc:
        steps += int(run_fuzzy_checks) + int(run_klayout_drc)
    stp_cnt = 0

    lc.print_control("{{PROGRESS}} Uncompressing the gds files")
    # Decompress project items.
    run_prep_cmd = "cd {target_path}; make uncompress;".format(
        target_path=target_path
    )

    process = subprocess.Popen(run_prep_cmd, stdout=subprocess.PIPE, shell=True)
    process.communicate()[0].strip()
    lc.print_control("Step " + str(stp_cnt) + " done without fatal errors.")
    stp_cnt += 1

    if not drc_only:
        # NOTE: Step 1: Check LICENSE.
        lc.print_control("{{PROGRESS}} Executing Step " + str(stp_cnt) + " of " + str(steps) + ": Checking License files.")
        lcr = check_license.check_main_license(target_path)
        if lcr:
            if not lcr["approved"]:
                lc.print_control("{{LICENSE COMPLIANCE FAILED}} A prohibited LICENSE (%s) was found in project root." % lcr["license_key"])
                lc.print_control("TEST FAILED AT STEP %s" % str(stp_cnt))
                lc.exit_control(2)
            elif lcr["approved"]:
                if lcr["license_key"]:
                    lc.print_control("{{LICENSE COMPLIANCE PASSED}} %s LICENSE file was found in project root" % lcr["license_key"])
                else:
                    lc.print_control("{{LICENSE COMPLIANCE WARNING}} A unidentified LICENSE file was found in project root")
        else:
            lc.print_control("{{LICENSE COMPLIANCE FAILED}} A LICENSE file was not found in project root.")
            lc.print_control("TEST FAILED AT STEP %s" % str(stp_cnt))
            lc.exit_control(2)

        third_party_licenses = check_license.check_lib_license(target_path + '/third-party/')

        if len(third_party_licenses):
            for key in third_party_licenses:
                if not third_party_licenses[key]:
                    lc.print_control("{{FAIL}} Third Party" + str(key) + "License Not Found\nTEST FAILED AT STEP " + str(stp_cnt))
                    lc.exit_control(2)
            lc.print_control("{{PROGRESS}} Third Party Licenses Found.\nStep " + str(stp_cnt) + " done without fatal errors.")
        else:
            lc.print_control("{{PROGRESS}} No third party libraries found.\nStep " + str(stp_cnt) + " done without fatal errors.")

        spdx_non_compliant_list = check_license.check_dir_spdx_compliance([], target_path, lcr["license_key"])
        if spdx_non_compliant_list:
            paths = spdx_non_compliant_list[:20] if spdx_non_compliant_list.__len__() >= 20 else spdx_non_compliant_list
            lc.print_control("{{SPDX COMPLIANCE WARNING}} Found %s non-compliant files with the SPDX Standard. "
                             "Check full log for more information" % spdx_non_compliant_list.__len__())
            lc.print_control("SPDX COMPLIANCE: NON-COMPLIANT FILES PREVIEW: %s" % paths)

            lc.switch_log('%s/spdx_compliance_report.log' % output_directory)
            lc.create_full_log()
            lc.print_control("SPDX NON-COMPLIANT FILES")
            [lc.print_control(x) for x in spdx_non_compliant_list]
            lc.switch_log('%s/full_log.log' % output_directory)

        else:
            lc.print_control("{{SPDX COMPLIANCE PASSED}} Project is compliant with SPDX Standard")

        stp_cnt += 1

        # NOTE: Step 2: Check YAML description.
        lc.print_control("{{PROGRESS}} Executing Step " + str(stp_cnt) + " of " + str(steps) + ": Checking YAML description.")
        check, top_level_netlist, user_level_netlist = check_yaml.check_yaml(target_path)
        if check:
            lc.print_control("{{PROGRESS}} YAML file valid!\nStep " + str(stp_cnt) + " done without fatal errors.")
        else:
            lc.print_control(
                "{{FAIL}} YAML file not valid in target path, please check the README.md for more info on the structure\nTEST FAILED AT STEP " + str(
                    stp_cnt))
            lc.exit_control(2)
        stp_cnt += 1

        verilog_netlist, spice_netlist = parse_netlists(target_path, top_level_netlist, user_level_netlist, lc)
        
        project_type = get_project_type(top_level_netlist, user_level_netlist)
        config.init(project_type)
        lc.print_control("{{PROGRESS}} Detected Project Type is \"" + project_type + "\"")

        # NOTE: Step 3: Check Complaince.
        lc.print_control("{{PROGRESS}} Executing Step " + str(stp_cnt) + " of " + str(steps) + ": Executing Complaince Checks.")

        # Manifest Checks:
        check, reason, fail_lines = check_manifest.check_manifests(target_path=caravel_root,output_file=output_directory+'/manifest_check', manifest_source=manifest_source,lc=lc)
        if check:
            lc.print_control("{{PROGRESS}} " + reason)
        else:
            lc.print_control("{{FAIL}} " + reason)
            lc.print_control("\n".join(fail_lines))
            lc.exit_control(2)

        # Makefile Checks:
        makefileCheck, makefileReason = check_makefile.checkMakefile(target_path)
        if makefileCheck:
            lc.print_control("{{PROGRESS}} Makefile Checks Passed.")
        else:
           lc.print_control("{{FAIL}} Makefile checks failed because: " + makefileReason)
           lc.exit_control(2)

        # Documentation Checks:
        documentationCheck, reason = check_documentation.checkDocumentation(target_path)
        if documentationCheck:
            lc.print_control("{{PROGRESS}} Documentation Checks Passed.")
        else:
            lc.print_control("{{FAIL}} Documentation checks failed because: " + reason)
            lc.exit_control(2)
        stp_cnt += 1

        # NOTE: Step 4: Check Fuzzy Consistency.
        if run_fuzzy_checks:
            lc.print_control("{{PROGRESS}} Executing Step " + str(stp_cnt) + " of " + str(steps) + ": Executing Fuzzy Consistency Checks.")

            # Fuzzy Checks:
            check, reason = consistency_checker.fuzzyCheck(target_path=target_path, pdk_root=pdk_root, run_gds_fc=run_gds_fc, spice_netlist=spice_netlist, verilog_netlist=verilog_netlist,
                                                        output_directory=output_directory, lc=lc)
            if check:
                lc.print_control("{{PROGRESS}} Fuzzy Consistency Checks Passed!\nStep " + str(stp_cnt) + " done without fatal errors.")
            else:
                lc.print_control("{{WARNING}} Consistency Checks Failed+ Reason: " + reason)
            stp_cnt += 1

        # NOTE: Step 5: Perform XOR checks on the GDS.
        lc.print_control("{{PROGRESS}} Executing Step " + str(stp_cnt) + " of " + str(steps) + ": Executing XOR Consistency Checks.")
        # Manifest Checks:
        check, reason = xor_checker.gds_xor_check(str(target_path) + '/gds/', pdk_root, output_directory, lc)
        if check:
            lc.print_control("{{PROGRESS}} XOR Checks on User Project GDS Passed!\nStep " + str(stp_cnt) + " done without fatal errors.")
        else:
            lc.print_control("{{FAIL}} XOR Checks on GDS Failed, Reason: " + reason + "\nTEST FAILED AT STEP " + str(stp_cnt))
            lc.exit_control(2); # Removing the first `#` from this line will make the XOR test a fail/success condition
        stp_cnt += 1


    # NOTE: Step 6: Perform DRC checks on the GDS.
    # assumption that we'll always be using a caravel top module based on what's on step 3
    lc.print_control("{{PROGRESS}} Executing Step " + str(stp_cnt) + " of " + str(steps) + ": Checking DRC Violations.")
    if skip_drc:
        lc.print_control("{{WARNING}} Skipping DRC Checks...")
    else:
        user_wrapper_path=Path(str(target_path) + "/gds/" + config.user_module + ".gds")
        if not os.path.exists(user_wrapper_path):
            lc.print_control("{{FAIL}} DRC Checks on GDS Failed, Reason: ./gds/" + config.user_module + ".gds(.gz) not found can't run DRC\nTEST FAILED AT STEP " + str(stp_cnt))
            lc.exit_control(2)
        else:
            check, reason = gds_drc_checker.magic_gds_drc_check(str(target_path) + '/gds/', config.user_module, pdk_root, output_directory, lc)
            if check:
                lc.print_control("{{PROGRESS}} DRC Checks on User Project GDS Passed!\nStep " + str(stp_cnt) + " done without fatal errors.")
            else:
                lc.print_control("{{FAIL}} DRC Checks on GDS Failed, Reason: " + reason + "\nTEST FAILED AT STEP " + str(stp_cnt))
                lc.exit_control(2)
        stp_cnt += 1
        if run_klayout_drc:
            lc.print_control("{{PROGRESS}} Executing Step " + str(stp_cnt) + " of " + str(steps) + ": Checking Klayout DRC Violations.")
            if not os.path.exists(user_wrapper_path):
                lc.print_control("{{FAIL}} Klayout DRC Checks on GDS Failed, Reason: ./gds/" + config.user_module + ".gds(.gz) not found can't run DRC\nTEST FAILED AT STEP " + str(stp_cnt))
                lc.exit_control(2)
            else:
                check, reason = gds_drc_checker.klayout_gds_drc_check(str(target_path) + '/gds/', config.user_module, pdk_root, output_directory, lc)
                if check:
                    lc.print_control("{{PROGRESS}} Klayout DRC Checks on User Project GDS Passed!\nStep " + str(stp_cnt) + " done without fatal errors.")
                else:
                    lc.print_control("{{FAIL}} Klayout DRC Checks on GDS Failed, Reason: " + reason + "\nTEST FAILED AT STEP " + str(stp_cnt))
                    lc.exit_control(2)
            stp_cnt += 1

    # NOTE: Step 7: Not Yet Implemented.
    lc.print_control("{{SUCCESS}} All Checks PASSED!")
    lc.dump_full_log()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Runs the precheck tool by calling the various checks in order.')

    parser.add_argument('--target_path', '-t', required=True,
                        help='Absolute Path to the project.')

    parser.add_argument('--caravel_root', '-c', required=True,
                        help='Absolute Path to caravel.')

    parser.add_argument('--output_directory', '-o', required=False,
                        help='Output Directory, defaults to /target_path/checks')

    parser.add_argument('--pdk_root', '-p', required=True,
                        help='PDK_ROOT, points to pdk installation path')

    parser.add_argument('--manifest_source', '-ms', default="master",
                        help='The manifest files source branch: master or develop. Defaults to master')

    parser.add_argument('--run_fuzzy_checks', '-rfc', action='store_true', default=False,
                        help="Specifies whether or not to run fuzzy consistency checks. Default: False")

    parser.add_argument('--run_gds_fc', '-rgfc', action='store_true', default=False,
                        help="Specifies whether or not to run gds fuzzy consistency checks. Default: False")

    parser.add_argument('--skip_drc', '-sd', action='store_true', default=False,
                        help="Specifies whether or not to skip DRC checks. Default: False")

    parser.add_argument('--drc_only', '-do', action='store_true', default=False,
                        help="Specifies whether or not to only run DRC checks. Default: False")

    parser.add_argument('--dont_compress', '-dc', action='store_true', default=False,
                        help="If enabled, compression won't happen at the end of the run. Default: False")

    parser.add_argument('--run_klayout_drc', '-rkd', action='store_true', default=False,
                        help="Specifies whether or not to run Klayout DRC checks after Magic. Default: False")

    args = parser.parse_args()
    target_path = args.target_path
    pdk_root = args.pdk_root
    caravel_root = args.caravel_root
    manifest_source = args.manifest_source
    skip_drc = args.skip_drc
    run_fuzzy_checks = args.run_fuzzy_checks
    run_gds_fc = args.run_gds_fc
    drc_only = args.drc_only
    dont_compress = args.dont_compress
    run_klayout_drc = args.run_klayout_drc

    run_check_sequence(target_path, caravel_root, pdk_root, args.output_directory, run_fuzzy_checks, run_gds_fc, skip_drc, drc_only, dont_compress, manifest_source, run_klayout_drc)
