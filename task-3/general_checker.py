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
import os
import utils.spice_utils as spice_utils
import utils.verilog_utils as verilog_utils
import re
import sys

docExts = ['.rst', '.html','.md','.pdf','.doc','.docx','.odt']

makefileTargets = ['verify', 'clean', 'compress', 'uncompress']

user_power_list = ['vdda1', 'vssa1', 'vccd1', 'vssd1'] # To be changed when we have a final caravel netlist
reserved_power_list = ['vddio', 'vdda', 'vccd'] # To be changed when we have a final caravel netlist

toplevel = 'striVe2a_core' #caravel
user_module = 'digital_pll' #user_project_wrapper

def getListOfFiles(dirName):
    # create a list of file and sub directories
    # names in the given directory
    listOfFile = os.listdir(dirName)
    allFiles = list()
    # Iterate over all the entries
    for entry in listOfFile:
        # Create full path
        fullPath = os.path.join(dirName, entry)
        # If entry is a directory then get the list of files in this directory
        if os.path.isdir(fullPath):
            allFiles = allFiles + getListOfFiles(fullPath)
        else:
            allFiles.append(fullPath)
    return allFiles

def checkMakefile(target_path):
    try:
        makefileOpener = open(target_path+'/Makefile')
        if makefileOpener.mode == 'r':
            makefileContent = makefileOpener.read()
        makefileOpener.close()

        for target in makefileTargets:
            if makefileContent.count(target+':') == 0:
                return False, 'Makfile missing target: ' + target +':'
            if target == 'compress':
                if makefileContent.count(target+':') < 2:
                    return False, 'Makfile missing target: ' + target +':'

        return True, ''
    except OSError:
        return False, 'Makefile not found at top level'


def checkDocumentation(target_path):
    files = getListOfFiles(target_path)
    for f in files:
        extension = os.path.splitext(f)[1]
        if extension in docExts:
            return True
    return False

def basic_spice_hierarchy_checks(spice_netlist, toplevel,user_module):
    check, reason = spice_utils.find_subckt(spice_netlist[0],toplevel)
    if check == False:
        print('Spice Check Failed because:', reason)
        return False, reason
    else:
        print(reason)
        check, reason = spice_utils.find_subckt(spice_netlist[1],user_module)
        if check == False:
            print('Spice Check Failed because:', reason)
            return False, reason
        else:
            print(reason)
            check, reason = spice_utils.confirm_complex_subckt(spice_netlist[0],toplevel,5)  # 5 should be replaced with a more realistic number reflecting the number of PADs, macros and so..
            if check == False:
                print('Spice Check Failed because:', reason)
                return False, reason
            else:
                print(reason)
                check, reason = spice_utils.confirm_complex_subckt(spice_netlist[1],user_module,1)
                if check == False:
                    print('Spice Check Failed because:', reason)
                    return False, reason
                else:
                    print(reason)
                    check, reason = spice_utils.confirm_circuit_hierarchy(spice_netlist[0], toplevel, user_module)
                    if check == False:
                        print('Spice Check Failed because:', reason)
                        return False, reason
                    else:
                        check, connections_map = spice_utils.extract_connections_from_inst(spice_netlist[0],toplevel,user_module)
                        if check == False:
                            print('Spice Check Failed because:', connections_map)
                            return False,connections_map
                        else:
                            print('Spice Consistency Checks Passed.')
                            return True,connections_map


def basic_verilog_hierarchy_checks(verilog_netlist, toplevel,user_module):
    print(verilog_netlist)
    check, reason = verilog_utils.find_module(verilog_netlist[0],toplevel)
    if check == False:
        print('verilog Check Failed because:', reason, ' in netlist: ', verilog_netlist[0])
        return False, reason
    else:
        print(reason)
        check, reason = verilog_utils.find_module(verilog_netlist[1],user_module)
        if check == False:
            print('verilog Check Failed because:', reason, ' in netlist: ', verilog_netlist[1])
            return False,reason
        else:
            print(reason)
            check, reason = verilog_utils.confirm_complex_module(verilog_netlist[0],toplevel,5)  # 5 should be replaced with a more realistic number reflecting the number of PADs, macros and so..
            if check == False:
                print('verilog Check Failed because:', reason, ' in netlist: ', verilog_netlist[0])
                return False,reason
            else:
                print(reason)
                check, reason = verilog_utils.confirm_complex_module(verilog_netlist[1],user_module,1)
                if check == False:
                    print('verilog Check Failed because:', reason, ' in netlist: ', verilog_netlist[1])
                    return False,reason
                else:
                    print(reason)
                    check, reason = verilog_utils.confirm_circuit_hierarchy(verilog_netlist[0], toplevel, user_module)
                    if check == False:
                        print('verilog Check Failed because:', reason, ' in netlist: ', verilog_netlist[0])
                        return False,reason
                    else:
                        check, connections_map = verilog_utils.extract_connections_from_inst(verilog_netlist[0],toplevel,user_module)
                        if check == False:
                            print('verilog Check Failed because:', connections_map, ' in netlist: ', verilog_netlist[0])
                            return False,connections_map
                        else:
                        
                            print('verilog Consistency Checks Passed.')
                            return True,connections_map


def match_pin_names(benchmark_pins, user_pins):
    return (list(list(set(benchmark_pins)-set(user_pins)) + list(set(benchmark_pins)-set(user_pins))))
 
def check_power_pins(connections_map, forbidden_list, check_list):
    for key in connections_map:
        con = connections_map[key]
        if type(con) == type(str()):
            if con in check_list:
                check_list.remove(con)
            if con in forbidden_list:
                return False, 'The user is using a management area power/ground net: '+ con
        else:
            for c in con:
                if c in check_list:
                    check_list.remove(c)
                if c in forbidden_list:
                    return False, 'The user is using a management area power/ground net: '+ c
    if len(check_list):
        return False, "The user didn't use the following power/ground nets: " + " ".join(check_list)
    else:
        return True, 'Power Checks Passed'


def diff_lists(li1, li2):
    return (list(list(set(li1)-set(li2)) + list(set(li2)-set(li1))))
 
def check_source_gds_consitency(target_path, toplevel, user_module,user_module_name,output_directory, top_type_list,top_name_list, user_type_list, user_name_list):
    run_instance_list_cmd = "sh run_instances_listing.sh {target_path} {design_name} {sub_design_name} {output_directory}".format(
        target_path = target_path,
        design_name = toplevel,
        sub_design_name = user_module_name,
        output_directory = output_directory
    )

    print ("Starting Magic Extractions From GDS...")

    process = subprocess.Popen(run_instance_list_cmd.split(), stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    try:
        while True:
            output = process.stdout.readline()
            if not output:
                break
            if output:
                print ('\r'+str(output.strip())[2:-1])
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.decode(sys.getfilesystemencoding())
        print(str(error_msg))

    toplevelFileOpener = open(output_directory+'/'+toplevel+'.magic.typelist')
    if toplevelFileOpener.mode == 'r':
        toplevelContent = toplevelFileOpener.read()
    toplevelFileOpener.close()
    
    toplvlCells = toplevelContent.split()
    
    toplevelFileOpener = open(output_directory+'/'+toplevel+'.magic.namelist')
    if toplevelFileOpener.mode == 'r':
        toplevelContent = toplevelFileOpener.read()
    toplevelFileOpener.close()
    
    toplvlInsts = toplevelContent.split()
    
    if toplvlCells.count(user_module)==1:
        user_moduleFileOpener = open(output_directory+'/'+user_module_name+'.magic.typelist')
        if user_moduleFileOpener.mode == 'r':
            user_moduleContent = user_moduleFileOpener.read()
        user_moduleFileOpener.close()
        
        userCells = user_moduleContent.split()
        
        user_moduleFileOpener = open(output_directory+'/'+user_module_name+'.magic.namelist')
        if user_moduleFileOpener.mode == 'r':
            user_moduleContent = user_moduleFileOpener.read()
        user_moduleFileOpener.close()

        userInsts = user_moduleContent.split()
        
        user_name_diff= diff_lists(userInsts, user_name_list)
        user_type_diff= diff_lists(userCells, user_type_list)

        top_name_diff= diff_lists(toplvlInsts, top_name_list)
        top_type_diff= diff_lists(toplvlCells, top_type_list)


        print('user wrapper cell names differences: ')
        print(user_name_diff)
        print('user wrapper cell type differences: ')
        print(user_type_diff)
        print('toplevel cell names differences: ')
        print(top_name_diff)
        print('toplevel cell names differences: ')
        print(top_type_diff)
        if len(user_name_diff)+len(user_type_diff)+len(top_name_diff)+len(top_type_diff):
            return False, 'Hierarchy Matching Failed'
        return True, 'GDS Hierarchy Check Passed'
    else:
        return False, 'GDS Hierarchy Check Failed'


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Runs a couple of checks on a given folder.')

    parser.add_argument('--target_path', '-t', required=True,
                        help='Design Path')

    parser.add_argument('--spice_netlist', '-s', nargs='+', default=[],
                        help='Spice Netlist')

    parser.add_argument('--verilog_netlist', '-v', nargs='+', default=[],
                        help='Verilog Netlist')

    parser.add_argument('--output_directory', '-o', required=False,
                        help='Output Directory')

    args = parser.parse_args()
    target_path = args.target_path
    verilog_netlist = args.verilog_netlist
    spice_netlist = args.spice_netlist
    if args.output_directory is None:
        output_directory = str(target_path)+ '/checks'
    else:
        output_directory = args.output_directory

    if checkDocumentation(target_path):
        print("Documentation Exists")
    else:
        print("Documentation Not Found")

    makefileCheck, makefileReason = checkMakefile(target_path)
    if makefileCheck:
        print("Makefile checks passed")
    else:
        print("Makefile checks failed because: ", makefileReason)
    basic_hierarchy_checks = False    

    connections_map = dict()
    instance_name = ''
    top_name_list = list()
    top_type_list = list()
    user_name_list = list()
    user_type_list = list()
    if len(verilog_netlist) != 2 and len(spice_netlist) != 2:
        print ("No toplevel netlist provided, please provide either a spice netlist or a verilog netlist: -v | -s toplevel user_project_wrapper")
    else:
        if len(spice_netlist) == 2:
            basic_hierarchy_checks, connections_map = basic_spice_hierarchy_checks(spice_netlist,toplevel,user_module)
            if basic_hierarchy_checks:
                basic_hierarchy_checks, tmp = spice_utils.extract_instance_name(spice_netlist[0],toplevel,user_module)
                if basic_hierarchy_checks:
                    instance_name = tmp
                    print(instance_name)
        if len(verilog_netlist) == 2:
            check, reason = verilog_utils.verify_non_behavioral_netlist(verilog_netlist[0])
            if check:
                check, reason = verilog_utils.verify_non_behavioral_netlist(verilog_netlist[1])
                if check:
                    basic_hierarchy_checks, connections_map = basic_verilog_hierarchy_checks(verilog_netlist,toplevel,user_module)
                    if basic_hierarchy_checks:
                        basic_hierarchy_checks, tmp = verilog_utils.extract_instance_name(verilog_netlist[0],toplevel,user_module)
                        if basic_hierarchy_checks:
                            instance_name = tmp
                            check, top_name_list,top_type_list= verilog_utils.extract_cell_list(verilog_netlist[0],toplevel)
                            check, user_name_list,user_type_list= verilog_utils.extract_cell_list(verilog_netlist[1],user_module)
                            print(instance_name)
                            print(top_name_list)
                            print(top_type_list)
                            print(user_name_list)
                            print(user_type_list)
                else:
                    print(reason)
            else:
                print(reason)

    if basic_hierarchy_checks:
        print("Basic Hierarchy Checks Passed.")
        pin_name_diffs= match_pin_names(list(connections_map.keys()), list(connections_map.keys())) # replace with the true benchmark list of pins once acquired
        if len(pin_name_diffs):
            print ("Pins check failed. The user is using different pins: ", pin_name_diffs)
        else:
            print("Pins check passed")
            print(check_power_pins(connections_map,reserved_power_list,user_power_list))
    else:
        print("Basic Hierarchy Checks Failed.")

check, reason = check_source_gds_consitency(target_path, toplevel, user_module,instance_name,output_directory,top_type_list,top_name_list, user_type_list, user_name_list)
if check:
    print(reason)
    print('GDS Checks Passed')
else:
    print('GDS Checks Failed: ', reason)
