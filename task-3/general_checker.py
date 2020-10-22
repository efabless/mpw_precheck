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

docExts = ['.rst', '.html','.md','.pdf','.doc','.docx','.odt']

makefileTargets = ['verify', 'clean', 'compress', 'uncompress']

toplevel = 'striVe2a' #caravel
user_module = 'striVe2a_core' #user_project_wrapper

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

def check_source_gds_consitency(target_path, design_name):
    pass

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Runs a couple of checks on a given folder.')

    parser.add_argument('--target_path', '-t', required=True,
                        help='Design Path')

    parser.add_argument('--spice_netlist', '-s', nargs='+', default=[],
                        help='Spice Netlist')

    parser.add_argument('--verilog_netlist', '-v', nargs='+', default=[],
                        help='Verilog Netlist')

    parser.add_argument('--design_name', '-d', required=True,
                        help='Design Name')

    parser.add_argument('--output_directory', '-o', required=False,
                        help='Output Directory')

    args = parser.parse_args()
    target_path = args.target_path
    design_name = args.design_name
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

    if len(verilog_netlist) != 2 and len(spice_netlist) != 2:
        print ("No toplevel netlist provided, please provide either a spice netlist or a verilog netlist")
    else:
        if len(spice_netlist) == 2:
            check, reason = spice_utils.find_subckt(spice_netlist[0],toplevel)
            if check == False:
                print('Spice Check Failed because:', reason)
            else:
                print(reason)
                check, reason = spice_utils.find_subckt(spice_netlist[1],user_module)
                if check == False:
                    print('Spice Check Failed because:', reason)
                else:
                    print(reason)
                    check, reason = spice_utils.confirm_complex_subckt(spice_netlist[0],toplevel,5)  # 5 should be replaced with a more realistic number reflecting the number of PADs, macros and so..
                    if check == False:
                        print('Spice Check Failed because:', reason)
                    else:
                        print(reason)
                        check, reason = spice_utils.confirm_complex_subckt(spice_netlist[1],user_module,1)
                        if check == False:
                            print('Spice Check Failed because:', reason)
                        else:
                            print(reason)
                            check, reason = spice_utils.confirm_circuit_hierarchy(spice_netlist[0], toplevel, user_module)
                            if check == False:
                                print('Spice Check Failed because:', reason)
                            else:
                                print(reason)
                                print('Spice Consistency Checks Passed.')
        if len(verilog_netlist) == 2:
                    check, reason = verilog_utils.find_module(verilog_netlist[0],toplevel)
                    if check == False:
                        print('verilog Check Failed because:', reason, ' in netlist: ', verilog_netlist[0])
                    else:
                        print(reason)
                        check, reason = verilog_utils.find_module(verilog_netlist[1],user_module)
                        if check == False:
                            print('verilog Check Failed because:', reason, ' in netlist: ', verilog_netlist[1])
                        else:
                            print(reason)
                            check, reason = verilog_utils.confirm_complex_module(verilog_netlist[0],toplevel,5)  # 5 should be replaced with a more realistic number reflecting the number of PADs, macros and so..
                            if check == False:
                                print('verilog Check Failed because:', reason, ' in netlist: ', verilog_netlist[0])
                            else:
                                print(reason)
                                check, reason = verilog_utils.confirm_complex_module(verilog_netlist[1],user_module,1)
                                if check == False:
                                    print('verilog Check Failed because:', reason, ' in netlist: ', verilog_netlist[1])
                                else:
                                    print(reason)
                                    check, reason = verilog_utils.confirm_circuit_hierarchy(verilog_netlist[0], toplevel, user_module)
                                    if check == False:
                                        print('verilog Check Failed because:', reason, ' in netlist: ', verilog_netlist[0])
                                    else:
                                        print(reason)
                                        print('verilog Consistency Checks Passed.')
