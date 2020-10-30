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
import os
from utils.utils import *

def gds_drc_check(target_path, design_name, output_directory, call_path='/usr/local/bin/drc_checks'):
    call_path = os.path.abspath(call_path)
    run_drc_check_cmd = "sh {call_path}/run_drc_checks.sh {target_path} {design_name} {output_directory} {call_path}".format(
        call_path = call_path,
        target_path = target_path,
        design_name = design_name,
        output_directory = output_directory
    )

    print_control ("{{PROGRESS}} Running DRC Checks...")

    process = subprocess.Popen(run_drc_check_cmd.split(), stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    try:
        while True:
            output = process.stdout.readline()
            if not output:
                break
            if output:
                print_control ("\r"+str(output.strip())[2:-1])
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.decode(sys.getfilesystemencoding())
        return False, str(error_msg)

    drcFileOpener = open(output_directory+'/'+design_name+'.magic.drc')
    if drcFileOpener.mode == 'r':
        drcContent = drcFileOpener.read()
    drcFileOpener.close()

    splitLine = '----------------------------------------'


    # design name
    # violation message
    # list of violations
    # Total Count:
    if drcContent is None:
        return False, "No DRC report generated..."
    else:
        drcSections = drcContent.split(splitLine)
        if (len(drcSections) == 2):
            return True, "0 DRC Violations"
        else:
            vioDict = dict()
            for i in range(1,len(drcSections)-1,2):
                vioDict[drcSections[i]]=len(drcSections[i+1].split("\n"))
            cnt = 0
            for key in vioDict:
                val = vioDict[key]
                cnt+=val
                print_control("{{PROGRESS}} Violation Message \""+key.strip()+ " \"found "+val+ " Times.")
            return False, "Total # of DRC violations is "+ str(cnt)



if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Runs a magic drc check on a given GDSII.')

    parser.add_argument('--target_path', '-t', required=True,
                        help='Design Path')

    parser.add_argument('--design_name', '-d', required=True,
                        help='Design Name')

    parser.add_argument('--output_directory', '-o', required=False,
                        help='Output Directory')

    args = parser.parse_args()
    target_path = args.target_path
    design_name = args.design_name
    if args.output_directory is None:
        output_directory = str(target_path)+ '/drc_checks'
    else:
        output_directory = args.output_directory

    print("{{RESULT}} ", gds_drc_check(target_path, design_name, output_directory,'.'))
