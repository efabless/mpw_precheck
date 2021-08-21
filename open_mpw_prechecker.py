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
import os.path
import subprocess
from pathlib import Path

import base_checks.check_documentation as check_documentation
import base_checks.check_license as check_license
import base_checks.check_makefile as check_makefile
import base_checks.check_manifest as check_manifest
import base_checks.check_yaml as check_yaml
import base_checks.check_defaults as check_defaults
import config
import consistency_checks.consistency_checker as consistency_checker
import klayout_drc_checks.klayout_drc_checker as klayout_drc_checker
import drc_checks.gds_drc_checker as gds_drc_checker
import xor_checks.xor_checker as xor_checker
from utils.utils import logger

default_logger_path = '/usr/local/bin/full_log.log'
default_target_path = '/usr/local/bin/caravel/'
default_content_path = './base_checks/_default_content'


def parse_netlists(target_path, top_level_netlist, user_level_netlist, lc=logger(default_logger_path, default_target_path)):
    spice_netlist = []
    verilog_netlist = []
    toplvl_extension = os.path.splitext(top_level_netlist)[1]
    userlvl_extension = os.path.splitext(user_level_netlist)[1]

    if str(toplvl_extension) == '.v' and str(userlvl_extension) == '.v':
        verilog_netlist = ['%s/%s' % (target_path, top_level_netlist), '%s/%s' % (target_path, user_level_netlist)]
    elif str(toplvl_extension) == '.spice' and str(userlvl_extension) == '.spice':
        spice_netlist =   ['%s/%s' % (target_path, top_level_netlist), '%s/%s' % (target_path, user_level_netlist)]
    else:
        lc.print_control("{{FAIL}} The provided top and user level netlists are neither .spice or .v files. Please adhere to the required input types.")

    return verilog_netlist, spice_netlist


def get_project_type(top_level_netlist, user_level_netlist, lc=logger(default_logger_path, default_target_path)):
    if "caravel.v" in top_level_netlist and "user_project_wrapper.v" in user_level_netlist:
        project_type = "digital"
        return project_type
    elif "caravan.v" in top_level_netlist and "user_analog_project_wrapper.v" in user_level_netlist:
        project_type = "analog"
        return project_type
    else:
        lc.print_control(
            "{{FAIL}} the provided top level and user level netlists are not correct. \n \
            The top level netlist should point to caravel.v if your project is digital or caravan.v if your project is analog. \n \
            The user_level_netlist should point to user_project_wrapper.v if your project is digital or user_analog_project_wrapper.v if your project is analog.")


def run_check_sequence(target_path, caravel_root, pdk_root, output_directory=None,  run_fuzzy_checks=False, run_gds_fc=False,
        skip_drc=False, skip_xor=False, drc_only=False, dont_compress=False, manifest_source="master", run_klayout_drc=False,
        run_klayout_fom_density_check=False, no_klayout_offgrid_check=False, no_klayout_metal_density_check=False, no_klayout_zero_area_check=False, private=False):
    if not output_directory:
        output_directory = str(target_path) + '/checks'

    # Create the logging controller
    lc = logger('%s/full_log.log' % output_directory, target_path, dont_compress)
    lc.create_full_log()
    _, top_level_netlist, user_level_netlist = check_yaml.check_yaml(target_path)
    project_type = get_project_type(top_level_netlist, user_level_netlist, lc)
    config.init(project_type)
    user_wrapper_path = Path(f"{target_path}/gds/{config.user_module}.gds")
    steps = 6
    if not private:
        steps += 1
    if drc_only:
        steps -= 4
    elif run_fuzzy_checks or run_klayout_drc:
        steps += int(run_fuzzy_checks) + int(run_klayout_drc)
    stp_cnt = 0

    lc.print_control("{{PROGRESS}} Executing Step %s of %s: Extracting GDS Files" % (stp_cnt, steps))

    # Decompress project items.
    run_prep_cmd = "cd {target_path}; make uncompress;".format(target_path=target_path)
    process = subprocess.Popen(run_prep_cmd, stdout=subprocess.PIPE, shell=True)
    process.communicate()[0].strip()

    lc.print_control("Step %s done without fatal errors." % stp_cnt)
    stp_cnt += 1



    if not drc_only:
        if not private:
            # NOTE: Step 1: Check LICENSE.
            lc.print_control("{{PROGRESS}} Executing Step %s of %s: Project License Check" % (stp_cnt, steps))
            lcr = check_license.check_main_license(target_path)
            if lcr:
                if not lcr["approved"]:
                    lc.print_control("{{LICENSE COMPLIANCE FAILED}} A prohibited LICENSE (%s) was found in project root." % lcr["license_key"])
                    lc.print_control("TEST FAILED AT STEP %s" % stp_cnt)
                elif lcr["approved"]:
                    if lcr["license_key"]:
                        lc.print_control("{{LICENSE COMPLIANCE PASSED}} %s LICENSE file was found in project root" % lcr["license_key"])
                    else:
                        lc.print_control("{{LICENSE COMPLIANCE WARNING}} A unidentified LICENSE file was found in project root")
            else:
                lc.print_control("{{LICENSE COMPLIANCE FAILED}} A LICENSE file was not found in project root.")
                lc.print_control("TEST FAILED AT STEP %s" % stp_cnt)

            submodules_licenses = check_license.check_submodules_license('%s' % target_path)
            for asubmodule_license in submodules_licenses:
                license_approved = asubmodule_license["approved"]
                license_key = asubmodule_license["license_key"]
                submodule = os.path.dirname(asubmodule_license["path"])
                if not license_approved:
                    lc.print_control("{{ERROR}} A prohibited LICENSE (%s) was found in submodule %s." % (license_key, submodule))
                    lc.print_control("TEST FAILED AT STEP %s" % stp_cnt)
                elif license_approved:
                    if license_key:
                        lc.print_control("{{PROGRESS}} %s compilant LICENSE file was found in submodule %s" %(license_key, submodule))
                    else:
                        lc.print_control("{{WARNING}} A unidentified LICENSE file was found in submodule %s" %submodule)

            third_party_licenses = check_license.check_lib_license('%s/third_party/' % target_path)

            for athird_party_license in third_party_licenses:
                license_approved = athird_party_license["approved"]
                license_key = athird_party_license["license_key"]
                third_party_lib = os.path.dirname(athird_party_license["path"])
                if not license_approved:
                    lc.print_control("{{ERROR}} A prohibited LICENSE (%s) was found in third_party lib %s." % (license_key, third_party_lib))
                    lc.print_control("TEST FAILED AT STEP %s" % stp_cnt)
                elif license_approved:
                    if license_key:
                        lc.print_control("{{PROGRESS}} %s compilant LICENSE file was found in third_party lib %s" %(license_key, third_party_lib))
                    else:
                        lc.print_control("{{WARNING}} A unidentified LICENSE file was found in third_party lib %s" %third_party_lib)

            spdx_non_compliant_list = check_license.check_dir_spdx_compliance([], target_path, lcr["license_key"])
            if spdx_non_compliant_list:
                paths = spdx_non_compliant_list[:20] if spdx_non_compliant_list.__len__() >= 20 else spdx_non_compliant_list
                lc.print_control("{{WARNING}} SPDX COMPLIANCE Found %s non-compliant files with the SPDX Standard. "
                                 "Check full log for more information" % spdx_non_compliant_list.__len__())
                lc.print_control("SPDX COMPLIANCE: NON-COMPLIANT FILES PREVIEW: %s" % paths)

                lc.switch_log('%s/spdx_compliance_report.log' % output_directory)
                lc.create_full_log()
                lc.print_control("SPDX NON-COMPLIANT FILES")
                [lc.print_control(x) for x in spdx_non_compliant_list]
                lc.switch_log('%s/full_log.log' % output_directory)
            else:
                lc.print_control("{{PROGRESS}} SPDX COMPLIANCE PASSED Project is compliant with SPDX Standard")

            stp_cnt += 1

        # NOTE: Step 2: Check YAML description.
        lc.print_control("{{PROGRESS}} Executing Step %s of %s: YAML File Check" % (stp_cnt, steps))
        check, top_level_netlist, user_level_netlist = check_yaml.check_yaml(target_path)
        if check:
            lc.print_control("{{PROGRESS}} YAML file valid!\nStep %s done without fatal errors." % stp_cnt)
        else:
            lc.print_control("{{FAIL}} YAML file not valid in target path, please check the README.md for more info on the structure\nTEST FAILED AT STEP %s" % stp_cnt)
        stp_cnt += 1

        verilog_netlist, spice_netlist = parse_netlists(target_path, top_level_netlist, user_level_netlist, lc)

        project_type = get_project_type(top_level_netlist, user_level_netlist, lc)
        config.init(project_type)
        lc.print_control("{{PROGRESS}} Detected Project Type is \"%s\"" % project_type)

        # NOTE: Step 3: Check Complaince.
        lc.print_control("{{PROGRESS}} Executing Step %s of %s: Project Compliance Checks" % (stp_cnt, steps))

        # Manifest Checks:
        check, reason, fail_lines = check_manifest.check_manifests(target_path=caravel_root, output_file='%s/manifest_check' % output_directory, manifest_source=manifest_source, lc=lc)
        if check:
            lc.print_control("{{PROGRESS}} %s" % reason)
        else:
            lc.print_control("{{FAIL}} %s" % reason)
            lc.print_control("\n".join(fail_lines))

        # Makefile Checks:
        makefileCheck, makefileReason = check_makefile.checkMakefile(target_path)
        if makefileCheck:
            lc.print_control("{{PROGRESS}} Makefile Checks Passed.")
        else:
            lc.print_control("{{FAIL}} Makefile checks failed because: %s" % makefileReason)

        if not private:
            default_README, reason = check_defaults.has_default_README(target_path,
                                                                        default_content_path)
            if default_README:
                lc.print_control("{{WARNING}} Default README.md checks failed because: %s" % reason)

            default_config, reason = check_defaults.has_default_project_config(target_path,
                                                                                default_content_path)
            if default_config:
                lc.print_control("{{FAIL}} Default config checks failed because: %s" % reason)

            default_content, reason = check_defaults.has_default_content(target_path,
                                                                        default_content_path)
            if default_content:
                lc.print_control("{{FAIL}} Default Content checks failed because: %s" % reason)
            # Documentation Checks:

            documentationCheck, reason = check_documentation.checkDocumentation(target_path)
            if documentationCheck:
                lc.print_control("{{PROGRESS}} Documentation Checks Passed.")
            else:
                lc.print_control("{{FAIL}} Documentation checks failed because: %s" % reason)

        stp_cnt += 1

        # NOTE: Step 4: Check Fuzzy Consistency.
        if run_fuzzy_checks:
            lc.print_control("{{PROGRESS}} Executing Step %s of %s: Fuzzy Consistency Checks" % (stp_cnt, steps))

            # Fuzzy Checks:
            check, reason = consistency_checker.fuzzyCheck(target_path=target_path, pdk_root=pdk_root, run_gds_fc=run_gds_fc, spice_netlist=spice_netlist, verilog_netlist=verilog_netlist,
                                                           output_directory=output_directory, lc=lc)
            if check:
                lc.print_control("{{PROGRESS}} Fuzzy Consistency Checks Passed!\nStep %s done without fatal errors." % stp_cnt)
            else:
                lc.print_control("{{WARNING}} Consistency Checks Failed+ Reason: %s" % reason)
            stp_cnt += 1

        # NOTE: Step 5: Perform XOR checks on the GDS.
        if skip_xor:
            lc.print_control("{{WARNING}} Skipping XOR Checks...")
            stp_cnt += 1
        else:
            lc.print_control("{{PROGRESS}} Executing Step %s of %s: XOR Consistency Checks" % (stp_cnt, steps))

            # Manifest Checks:
            check, reason = xor_checker.gds_xor_check('%s/gds/' % target_path, pdk_root, output_directory, lc)
            if check:
                lc.print_control("{{PROGRESS}} XOR Checks on User Project GDS Passed!\nStep %s done without fatal errors." % stp_cnt)
            else:
                lc.print_control("{{FAIL}} XOR Checks on GDS Failed, Reason: %s\nTEST FAILED AT STEP %s" % (reason, stp_cnt))
            stp_cnt += 1

    # NOTE: Step 6: Perform DRC checks on the GDS.
    # assumption that we'll always be using a caravel top module based on what's on step 3
    if skip_drc:
        lc.print_control("{{WARNING}} Skipping Step %s of %s: DRC Violations Checks..." % (stp_cnt, steps))
        stp_cnt += 1
    else:
        lc.print_control("{{PROGRESS}} Executing Step %s of %s: DRC Violations Checks" % (stp_cnt, steps))
        if not os.path.exists(user_wrapper_path):
            lc.print_control("{{FAIL}} DRC Checks on GDS Failed, Reason: ./gds/%s.gds(.gz) not found can't run DRC\nTEST FAILED AT STEP %s" % (config.user_module, stp_cnt))
        else:
            check, reason = gds_drc_checker.magic_gds_drc_check('%s/gds/' % target_path, config.user_module, pdk_root, output_directory, lc)
            if check:
                lc.print_control("{{PROGRESS}} DRC Checks on User Project GDS Passed!\nStep %s done without fatal errors." % stp_cnt)
            else:
                lc.print_control("{{FAIL}} DRC Checks on GDS Failed, Reason: %s\nTEST FAILED AT STEP %s" % (reason, stp_cnt))

        stp_cnt += 1

        # NOTE: Step 7: Perform KLayout DRC checks on the GDS.
        if run_klayout_drc:
            lc.print_control("{{PROGRESS}} Executing Step %s of %s: KLayout DRC Violations Check" % (stp_cnt, steps))
            if not os.path.exists(user_wrapper_path):
                lc.print_control("{{FAIL}} Klayout DRC Checks on GDS Failed, Reason: ./gds/%s.gds(.gz) not found can't run DRC\nTEST FAILED AT STEP %s" % (config.user_module, stp_cnt))
            else:
                check, reason = gds_drc_checker.klayout_gds_drc_check('%s/gds/' % target_path, config.user_module, pdk_root, output_directory, lc)
                if check:
                    lc.print_control("{{PROGRESS}} Klayout DRC Checks on User Project GDS Passed!\nStep %s done without fatal errors." % stp_cnt)
                else:
                    lc.print_control("{{FAIL}} Klayout DRC Checks on GDS Failed, Reason: %s\nTEST FAILED AT STEP %s" % (reason, stp_cnt))
            stp_cnt += 1

        if not no_klayout_offgrid_check:
            report_file = Path(output_directory) / "offgrid_check.xml"
            lc.print_control("{{PROGRESS}} Executing Klayout offgrid check.")
            failed, errors, warnings = klayout_drc_checker.offgrid_checker(user_wrapper_path,
                                                                        report_file, output_directory)
            if not failed:
                lc.print_control("{{PROGRESS}} Klayout offgrid Checks on User Project GDS Passed!\nStep " + str(stp_cnt) + " done without fatal errors.")
            else:
                lc.print_control("{{FAIL}} Klayout offgrid Checks on GDS Failed, Errors are: %s"%('\n'.join(errors)))
        if not no_klayout_metal_density_check:
            report_file = Path(output_directory) / "met_min_ca_density_check.xml"
            failed, errors, warnings = klayout_drc_checker.met_min_ca_density_checker(user_wrapper_path,
                                                                        report_file, output_directory)
            if not failed:
                lc.print_control("{{PROGRESS}} Klayout metal minimum clear area density Checks on User Project GDS Passed!\nStep " + str(stp_cnt) + " done without fatal errors.")
            else:
                lc.print_control("{{FAIL}} Klayout metal minimum clear area density Checks on GDS Failed, Errors are: %s"%('\n'.join(errors)))
    if run_klayout_fom_density_check:
        lc.print_control("{{PROGRESS}} Executing Step " + str(stp_cnt) + " of " + str(steps) + ": Checking Klayout FOM density.")
        report_file = Path(output_directory) / "fom_density_check.xml"
        failed, errors, warnings = klayout_drc_checker.fom_density_checker(user_wrapper_path,
                                                                report_file, output_directory)
        if not failed:
            lc.print_control("{{PROGRESS}} Klayout FOM density Checks on User Project GDS Passed!\nStep " + str(stp_cnt) + " done without fatal errors.")
        else:
            lc.print_control("{{FAIL}} Klayout FOM density Checks on GDS Failed, Errors are: %s"%('\n'.join(errors)))

            stp_cnt += 1
    if not no_klayout_zero_area_check:
        lc.print_control("{{PROGRESS}} Executing Step " + str(stp_cnt) + " of " + str(steps) + ": Checking zero area shapes in GDS.")
        zero_area_check_xml_report_path = Path(f"{output_directory}/zero_area_check.xml")
        zero_area_check_total_path = Path(f"{output_directory}/zero_area_check_total.txt")
        zero_area_check_cmd = ['bash', Path('./scripts/gdsArea0.rb'), user_wrapper_path, zero_area_check_xml_report_path]
        with open(lc.log, "w") as log:
            process = subprocess.run(zero_area_check_cmd, stdout=log, stderr=log)
        failed = (process.returncode != 0)
        with open(zero_area_check_xml_report_path) as zero_area_check_xml_report, open(zero_area_check_total_path, "w") as total_file_path:
            xml_content = zero_area_check_xml_report.read()
            zero_area_check_error_count = xml_content.count("<item>")
            total_file_path.write(str(zero_area_check_error_count))

        if not failed:
            lc.print_control("{{PROGRESS}} Klayout Zero Area check on User Project GDS Passed!\nStep " + str(stp_cnt) + " done without fatal errors.")
        else:
            lc.print_control("{{FAIL}} Klayout Zero Area check on GDS Failed. Read report database %s using klayout" % zero_area_check_xml_report_path)

            stp_cnt += 1

    # NOTE: Step 8: Not Yet Implemented.
    if "FAIL" not in lc.internal_log:
        lc.print_control("{{SUCCESS}} All Checks PASSED !!!")
        exit_code = 0
    else:
        lc.print_control("{{FAIL}} SOME Checks FAILED !!!")
        exit_code = 2
    lc.exit_control(exit_code)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Runs the precheck tool by calling the various checks in order.')

    parser.add_argument('--target_path', '-t', required=True,
                        help='Absolute Path to the project.')

    parser.add_argument('--caravel_root', '-c', required=True,
                        help='Absolute Path to caravel.')

    parser.add_argument('--output_directory', '-o', required=False,
                        help='Output Directory, defaults to /target_path/checks')

    parser.add_argument('--pdk_root', '-p', required=True,
                        help='PDK_ROOT, points to pdk installation path')

    # This is different a bit because it might be inside the container
    parser.add_argument('--manifest_source', '-ms', default="master",
                        help='The manifest files source branch: master or develop. Defaults to master')

    parser.add_argument('--run_fuzzy_checks', '-rfc', action='store_true', default=False,
                        help="Specifies whether or not to run fuzzy consistency checks. Default: False")

    parser.add_argument('--run_gds_fc', '-rgfc', action='store_true', default=False,
                        help="Specifies whether or not to run gds fuzzy consistency checks. Default: False")

    parser.add_argument('--skip_drc', '-sd', action='store_true', default=False,
                        help="Specifies whether or not to skip DRC checks. Default: False")

    parser.add_argument('--skip_xor', '-sxor', action='store_true', default=False,
                        help="Specifies whether or not to skip XOR checks. Default: False")

    parser.add_argument('--drc_only', '-do', action='store_true', default=False,
                        help="Specifies whether or not to only run DRC checks. Default: False")

    parser.add_argument('--dont_compress', '-dc', action='store_true', default=False,
                        help="If enabled, compression won't happen at the end of the run. Default: False")

    parser.add_argument('--run_klayout_drc', '-rkd', action='store_true', default=True,
                        help="Specifies whether or not to run Klayout DRC checks after Magic. Default: True")

    parser.add_argument('--run_klayout_fom_density_check', '-rkfdc', action='store_true', default=False,
                        help="Specifies whether or not to run Klayout field oxide mask density checks after Magic. Default: False")

    parser.add_argument('--no_klayout_offgrid_check', '-nkogc', action='store_true', default=False,
                        help="Specifies whether or not to run Klayout offgrid density checks. Default: False")

    parser.add_argument('--no_klayout_metal_density_check', '-nkmdc', action='store_true', default=False,
                        help="Specifies whether or not to run Klayout metal density checks. Default: False")

    parser.add_argument('--no_klayout_zero_area_check', '-nkza', action='store_true', default=False,
                        help="Specifies whether or not to run Klayout Zero Area Checks. Default: False")

    parser.add_argument('--private', action='store_true', default=False,
                        help="Specifies whether or not to run licensing & readme checks. Default: False")

    args = parser.parse_args()

    run_check_sequence(args.target_path, args.caravel_root, args.pdk_root, args.output_directory, args.run_fuzzy_checks,
            args.run_gds_fc, args.skip_drc, args.skip_xor, args.drc_only, args.dont_compress, args.manifest_source,
            args.run_klayout_drc, args.run_klayout_fom_density_check, args.no_klayout_offgrid_check, args.no_klayout_metal_density_check,
            args.no_klayout_zero_area_check, args.private)
