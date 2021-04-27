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

import os
import re
import sys
import argparse
import subprocess
import random
import copy
import urllib3
from pathlib import Path
from utils.utils import *

try:
    import utils.spice_utils as spice_utils
    import utils.verilog_utils as verilog_utils
except ImportError:
    import consistency_checks.utils.spice_utils as spice_utils
    import consistency_checks.utils.verilog_utils as verilog_utils

ignore_list = ["vdda1", "vssd1", "vccd1", "vccd2", "vssd2", "vssa2",
"vdda2", "vssa1"]
user_power_list = ["vdda1", "vssd1", "vccd1", "vccd2", "vssd2", "vssa2", "vdda2", "vssa1"]

reserved_power_list = ["vddio", "vdda", "vccd", "vssa", "vssd", "vssio", "vdda"]

toplevel_name_ignore = ["copyright_block_0", "user_id_textblock_0", "open_source_0"]
toplevel_type_ignore = ["copyright_block", "user_id_textblock", "open_source"]

toplevel = "caravel"
user_module = "user_project_wrapper"
default_logger_path = '/usr/local/bin/full_log.log'
default_target_path = '/usr/local/bin/caravel/'

golden_wrapper = 'user_project_wrapper_empty.lef'
link_prefix = 'https://raw.githubusercontent.com/efabless/caravel/master/lef/'


def fuzzyCheck(target_path, pdk_root, spice_netlist, verilog_netlist, output_directory,
               call_path="/usr/local/bin/consistency_checks", lc=logging_controller(default_logger_path,default_target_path)):

    basic_hierarchy_checks = False
    connections_map = dict()
    instance_name = ""
    top_name_list = list()
    top_type_list = list()
    user_name_list = list()
    user_type_list = list()
    if len(verilog_netlist) != 2 and len(spice_netlist) != 2:
        return False, "No toplevel netlist provided, please provide either a spice netlist or a verilog netlist: -v | -s toplevel user_project_wrapper"
    else:
        if len(spice_netlist) == 2:
            basic_hierarchy_checks, connections_map = basic_spice_hierarchy_checks(spice_netlist, toplevel, user_module, lc)
            if basic_hierarchy_checks:
                basic_hierarchy_checks, tmp = spice_utils.extract_instance_name(spice_netlist[0], toplevel, user_module)
                if basic_hierarchy_checks:
                    instance_name = tmp
                    check, top_name_list, top_type_list = spice_utils.extract_cell_list(spice_netlist[0], toplevel)
                    check, user_name_list, user_type_list = spice_utils.extract_cell_list(spice_netlist[1], user_module)
        if len(verilog_netlist) == 2:
            check, reason = verilog_utils.verify_non_behavioral_netlist(verilog_netlist[0])
            if check:
                check, reason = verilog_utils.verify_non_behavioral_netlist(verilog_netlist[1])
                if check:
                    basic_hierarchy_checks, connections_map = basic_verilog_hierarchy_checks(verilog_netlist, toplevel, user_module, lc)
                    if basic_hierarchy_checks:
                        basic_hierarchy_checks, tmp = verilog_utils.extract_instance_name(verilog_netlist[0], toplevel, user_module)
                        if basic_hierarchy_checks:
                            instance_name = tmp
                            check, top_name_list, top_type_list = verilog_utils.extract_cell_list(verilog_netlist[0], toplevel)
                            check, user_name_list, user_type_list = verilog_utils.extract_cell_list(verilog_netlist[1], user_module)
                else:
                    return False, reason
            else:
                return False, reason

    if basic_hierarchy_checks:
        lc.print_control("{{PROGRESS}} Basic Hierarchy Checks Passed.")
    else:
        return False, "Basic Hierarchy Checks Failed."

    lc.print_control("{PROGRESS} Running Pins and Power Checks...")
    check, user_project_wrapper_pin_list = extract_user_project_wrapper_pin_list(link_prefix+golden_wrapper)
    if check == False:
        return False, user_project_wrapper_pin_list
    # use lef view to extract user pin list
    check, user_pin_list =  extract_user_pin_list(target_path+"/lef/"+"user_project_wrapper.lef") 
    # [verilog_utils.remove_backslashes(k) for k in connections_map.keys()]
    if check == False:
        return False, user_pin_list

    pin_name_diffs = diff_lists(list(user_pin_list), user_project_wrapper_pin_list)
    pin_name_diffs = one_side_diff_lists(pin_name_diffs, ignore_list)
    if len(pin_name_diffs):
        return False, "Pins check failed. The user is using different pins: " + ", ".join(pin_name_diffs)
    else:
        lc.print_control("Pins check passed")
        check, power_reason = internal_power_checks(user_module,user_type_list, user_power_list, spice_netlist, verilog_netlist)
        if check:
            lc.print_control(power_reason)
            check, power_reason = check_power_pins(connections_map, reserved_power_list, user_power_list)
            if check:
                lc.print_control(power_reason)
            else:
                return False, power_reason
        else:
            return False, power_reason
    
    check, reason = check_source_gds_consitency(target_path+'/gds/', pdk_root, toplevel, user_module, instance_name, output_directory, top_type_list, top_name_list,
                                                user_type_list, user_name_list, lc, call_path)
    if check:
        lc.print_control(reason + "\nGDS Checks Passed")
    else:
        return False, "GDS Checks Failed: " + reason

    return True, "Fuzzy Checks Passed!"

def internal_power_checks(user_module,user_type_list,user_power_list, spice_netlists, verilog_netlists):
    spice_netlist = None
    verilog_netlist = None
    if len(spice_netlists) == 2:
        spice_netlist = spice_netlists[1]

    if len(verilog_netlists) == 2:
        verilog_netlist = verilog_netlists[1]

    cnt = 0
    while cnt < 20 and cnt < len(user_type_list):
        inst =  str(random.choice(user_type_list))
        if spice_netlist is not None:
            check, connections_map = spice_utils.extract_connections_from_inst(spice_netlist, user_module, inst)
            if check == False:
                return False, connections_map
            else:
                flag = False
                for key in connections_map.keys():
                    if connections_map[key] in user_power_list:
                        flag = True
                        break
                if not flag:
                    return False, "Instance "+inst+" was not connected to any power in "+str(spice_netlist)
        elif verilog_netlist is not None:
            check, connections_map = verilog_utils.extract_connections_from_inst(verilog_netlist, user_module, inst)
            if check == False:
                return False, connections_map
            else:
                flag = False
                for key in connections_map.keys():
                    if connections_map[key] in user_power_list:
                        flag = True
                        break
                if not flag:
                    return False, "Instance "+inst+" was not connected to any power in "+str(verilog_netlist)
        else:
            return False, "No netlist was passed to internal power checks!"
        cnt+=1
    return True, "Internal Power Checks Passed!"

def extract_user_project_wrapper_pin_list(lef_url):
    try:
        http = urllib3.PoolManager()
        lef_request = http.request('GET', lef_url)
        if lef_request.status != 200:
            return False, 'Unable to fetch {0}. Make sure you have an internet connection...'.format(lef_url)
        lefContent = lef_request.data.decode('utf-8')
        pattern = re.compile(r"\s*\bPIN\b\s*\b[\S+]+\s*")
        pins = re.findall(pattern, lefContent)
        if len(pins):
            ret_pins = [pin.strip().split()[-1] for pin in pins]
            return True, ret_pins
        else:
            return False, "No Pins found in LEF"
    except OSError:
        return False, "LEF file not found"

def extract_user_pin_list(lef_file):
    path=Path(lef_file)
    if not os.path.exists(path):
        return False, "LEF file not found"
    lefFileOpener = open(path)
    if lefFileOpener.mode == "r":
        lefContent = lefFileOpener.read()
    lefFileOpener.close()
    pattern = re.compile(r"\s*\bPIN\b\s*\b[\S+]+\s*")
    pins = re.findall(pattern, lefContent)
    if len(pins):
        ret_pins = [pin.strip().split()[-1] for pin in pins]
        return True, ret_pins
    else:
        return False, "No Pins found in LEF"

def basic_spice_hierarchy_checks(spice_netlist, toplevel, user_module, lc=logging_controller(default_logger_path,default_target_path)):
    path=Path(spice_netlist[0])
    if not os.path.exists(path):
        return False, "top level netlist not found"
    path=Path(spice_netlist[1])
    if not os.path.exists(path):
        return False, "user level netlist not found"

    check, reason = spice_utils.find_subckt(spice_netlist[0], toplevel)
    if check == False:
        lc.print_control("{{ERROR}} Spice Check Failed because: " + reason)
        return False, reason
    else:
        lc.print_control(reason)
        check, reason = spice_utils.find_subckt(spice_netlist[1], user_module)
        if check == False:
            lc.print_control("{{ERROR}} Spice Check Failed because:" + reason)
            return False, reason
        else:
            lc.print_control(reason)
            check, reason = spice_utils.confirm_complex_subckt(spice_netlist[0], toplevel,
                                                               8)
            if check == False:
                lc.print_control("{{ERROR}} Spice Check Failed because: " + reason)
                return False, reason
            else:
                lc.print_control(reason)
                check, reason = spice_utils.confirm_complex_subckt(spice_netlist[1], user_module, 1)
                if check == False:
                    lc.print_control("{{ERROR}} Spice Check Failed because: " + reason)
                    return False, reason
                else:
                    lc.print_control(reason)
                    check, reason = spice_utils.confirm_circuit_hierarchy(spice_netlist[0], toplevel, user_module)
                    if check == False:
                        lc.print_control("{{ERROR}} Spice Check Failed because: " + reason)
                        return False, reason
                    else:
                        check, connections_map = spice_utils.extract_connections_from_inst(spice_netlist[0], toplevel, user_module)
                        if check == False:
                            lc.print_control("{{ERROR}} Spice Check Failed because: " + connections_map)
                            return False, connections_map
                        else:
                            lc.print_control("Spice Consistency Checks Passed.")
                            return True, connections_map


def basic_verilog_hierarchy_checks(verilog_netlist, toplevel, user_module, lc=logging_controller(default_logger_path,default_target_path)):
    path=Path(verilog_netlist[0])
    if not os.path.exists(path):
        return False, "top level netlist not found"
    path=Path(verilog_netlist[1])
    if not os.path.exists(path):
        return False, "user level netlist not found"

    check, reason = verilog_utils.find_module(verilog_netlist[0], toplevel)
    if check == False:
        lc.print_control("{{ERROR}} verilog Check Failed because: " + reason+ " in netlist: " + verilog_netlist[0])
        return False, reason
    else:
        lc.print_control(reason)
        check, reason = verilog_utils.find_module(verilog_netlist[1], user_module)
        if check == False:
            lc.print_control("{{ERROR}} verilog Check Failed because: " + reason + " in netlist: " + verilog_netlist[1])
            return False, reason
        else:
            lc.print_control(reason)
            check, reason = verilog_utils.confirm_complex_module(verilog_netlist[0], toplevel,
                                                                 8)
            if check == False:
                lc.print_control("{{ERROR}} verilog Check Failed because: " + reason + " in netlist: " + verilog_netlist[0])
                return False, reason
            else:
                lc.print_control(reason)
                check, reason = verilog_utils.confirm_complex_module(verilog_netlist[1], user_module, 1)
                if check == False:
                    lc.print_control("{{ERROR}} verilog Check Failed because: " + reason + " in netlist: " + verilog_netlist[1])
                    return False, reason
                else:
                    lc.print_control(reason)
                    check, reason = verilog_utils.confirm_circuit_hierarchy(verilog_netlist[0], toplevel, user_module)
                    if check == False:
                        lc.print_control("{{ERROR}} verilog Check Failed because:" + reason + " in netlist: " + verilog_netlist[0])
                        return False, reason
                    else:
                        check, connections_map = verilog_utils.extract_connections_from_inst(verilog_netlist[0], toplevel, user_module)
                        if check == False:
                            lc.print_control("{{ERROR}} verilog Check Failed because:" + connections_map + " in netlist: " + verilog_netlist[0])
                            return False, connections_map
                        else:
                            lc.print_control("verilog Consistency Checks Passed.")
                            return True, connections_map


def check_power_pins(connections_map, forbidden_list, check_list):
    check_list_copy = copy.deepcopy(check_list)
    for key in connections_map:
        con = connections_map[key]
        if con in check_list_copy:
            check_list_copy.remove(con)
        if con in forbidden_list:
            return False, "The user is using a management area power/ground net: " + con
    if len(check_list_copy):
        return False, "The user didn't use the following power/ground nets: " + " ".join(check_list_copy)
    else:
        return True, "Power Checks Passed"


def diff_lists(li1, li2):
    return (list(list(set(li1) - set(li2)) + list(set(li2) - set(li1))))

def one_side_diff_lists(li1, li2):
    return (list(set(li1) - set(li2)))


def clean_gds_list(cells):
    cells = cells.replace("{", "")
    cells = cells.replace("}", "")
    return cells.replace("\\", "")


def check_source_gds_consitency(target_path, pdk_root, toplevel, user_module, user_module_name, output_directory, top_type_list, top_name_list, user_type_list,
                                user_name_list, lc=logging_controller(default_logger_path,default_target_path), call_path="/usr/local/bin/consistency_checks"):
    path=Path(target_path+"/"+toplevel+".gds")
    if not os.path.exists(path):
        return False,"Integrated Caravel GDS not found"
    call_path = os.path.abspath(call_path)
    run_instance_list_cmd = "sh {call_path}/run_instances_listing.sh {target_path} {pdk_root} {design_name} {sub_design_name} {output_directory} {call_path}".format(
        call_path=call_path,
        target_path=target_path,
        pdk_root=pdk_root,
        design_name=toplevel,
        sub_design_name=user_module_name,
        output_directory=output_directory
    )

    lc.print_control("{{PROGRESS}} Running Magic Extractions From GDS...")

    process = subprocess.Popen(run_instance_list_cmd.split(), stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    try:
        while True:
            output = process.stdout.readline()
            if not output:
                break
            if output:
                continue
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.decode(sys.getfilesystemencoding())
        lc.print_control("{{ERROR}} " + str(error_msg))
        lc.exit_control(255)
    try:
        logFileOpener = open(output_directory+'/magic_extract.log')
        if logFileOpener.mode == 'r':
            logContent = logFileOpener.read()
        logFileOpener.close()

        if logContent.find("was used but not defined.") != -1:
            return False, "The GDS is not valid/corrupt contains cells that are used but not defined. Please check `"+str(output_directory)+"/magic_extract.log` in the output directory for more details."

        toplevelFileOpener = open(output_directory + "/" + toplevel + ".magic.typelist")
        if toplevelFileOpener.mode == "r":
            toplevelContent = toplevelFileOpener.read()
        toplevelFileOpener.close()
        toplvlCells = clean_gds_list(toplevelContent).split()
        toplevelFileOpener = open(output_directory + "/" + toplevel + ".magic.namelist")
        if toplevelFileOpener.mode == "r":
            toplevelContent = toplevelFileOpener.read()
        toplevelFileOpener.close()
        toplvlInsts = clean_gds_list(toplevelContent).split()
        if toplvlCells.count(user_module) == 1:
            user_moduleFileOpener = open(output_directory + "/" + user_module_name + ".magic.typelist")
            if user_moduleFileOpener.mode == "r":
                user_moduleContent = user_moduleFileOpener.read()
            user_moduleFileOpener.close()
            userCells = clean_gds_list(user_moduleContent).split()
            user_moduleFileOpener = open(output_directory + "/" + user_module_name + ".magic.namelist")
            if user_moduleFileOpener.mode == "r":
                user_moduleContent = user_moduleFileOpener.read()
            user_moduleFileOpener.close()
            userInsts = clean_gds_list(user_moduleContent).split()

            user_name_diff = diff_lists(userInsts, user_name_list)
            user_type_diff = diff_lists(userCells, user_type_list)

            top_name_diff = diff_lists(toplvlInsts, top_name_list)
            top_type_diff = diff_lists(toplvlCells, top_type_list)
            top_name_diff = one_side_diff_lists(top_name_diff, toplevel_name_ignore)
            top_type_diff = one_side_diff_lists(top_type_diff, toplevel_type_ignore)

            lc.print_control("user wrapper cell names differences: ")
            lc.print_control(user_name_diff)
            lc.print_control("user wrapper cell type differences: ")
            lc.print_control(user_type_diff)
            lc.print_control("toplevel cell names differences: ")
            lc.print_control(top_name_diff)
            lc.print_control("toplevel cell type differences: ")
            lc.print_control(top_type_diff)
            if (len(userInsts) + len(userCells) + len(top_name_diff) + len(top_type_diff)) == 0:
                return False, "GDS Top level Hierarchy Check Passed. But, user_project_wrapper is empty in gds/caravel.gds. You are probably using the template caravel.gds and didn't add your integrated caravel chip. Thus, Hierarchy Matching Failed."
            if len(user_name_diff) + len(user_type_diff) + len(top_name_diff) + len(top_type_diff):
                return False, "Hierarchy Matching Failed"
            return True, "GDS Hierarchy Check Passed"
        else:
            return False, "GDS Hierarchy Check Failed"
    except FileNotFoundError:
        return False, "Either you didn't mount the docker, or you ran out of RAM. Otherwise, magic is broken. Please check `"+str(output_directory)+"/magic_extract.log` in the output directory for potentially more details."
    except OSError:
        return False, "Either you didn't mount the docker, or you ran out of RAM. Otherwise, magic is broken. Please check `"+str(output_directory)+"/magic_extract.log` in the output directory for potentially more details."

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Runs a couple of consistency fuzzy checks on a given folder.")

    parser.add_argument("--target_path", "-t", required=True,
                        help="Design Path")

    parser.add_argument("--spice_netlist", "-s", nargs="+", default=[],
                        help="Spice Netlists: toplvl.spice user_module.spice")

    parser.add_argument("--verilog_netlist", "-v", nargs="+", default=[],
                        help="Verilog Netlist: toplvl.v user_module.v")

    parser.add_argument("--output_directory", "-o", required=False,
                        help="Output Directory")

    args = parser.parse_args()
    target_path = args.target_path
    verilog_netlist = args.verilog_netlist
    spice_netlist = args.spice_netlist
    if args.output_directory is None:
        output_directory = str(target_path) + "/checks"
    else:
        output_directory = args.output_directory

    print("{{RESULT}} ", fuzzyCheck(target_path, spice_netlist, verilog_netlist, output_directory, "."))
