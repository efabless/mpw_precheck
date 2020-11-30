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

import os
import sys
import argparse
import subprocess
from pathlib import Path
from utils.utils import *

default_logger_path = '/usr/local/bin/full_log.log'
default_target_path = '/usr/local/bin/caravel/'

def gds_drc_check(target_path, design_name, output_directory, lc=logging_controller(default_logger_path,default_target_path), call_path='/usr/local/bin/drc_checks'):
    path=Path(target_path+"/"+design_name+".gds")
    if not os.path.exists(path):
        return False,"GDS not found"
    call_path = os.path.abspath(call_path)
    run_drc_check_cmd = "sh {call_path}/run_drc_checks.sh {target_path} {design_name} {output_directory} {call_path}".format(
        call_path=call_path,
        target_path=target_path,
        design_name=design_name,
        output_directory=output_directory
    )

    lc.print_control("{{PROGRESS}} Running DRC Checks...")

    process = subprocess.Popen(run_drc_check_cmd.split(), stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    try:
        while True:
            output = process.stdout.readline()
            if not output:
                break
            if output:
                continue
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.decode(sys.getfilesystemencoding())
        return False, str(error_msg)

    try:
        logFileOpener = open(output_directory+'/magic_drc.log')
        if logFileOpener.mode == 'r':
            logContent = logFileOpener.read()
        logFileOpener.close()

        if logContent.find("was used but not defined.") != -1:
            return False, "The GDS is not valid/corrupt contains cells that are used but not defined. Please check `checks/magic_drc.log` in the output directory for more details."

        drcFileOpener = open(output_directory + '/' + design_name + '.magic.drc')
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
            elif (len(drcSections) < 2):
                return False, "magic segfaulted. You ran out of RAM. Please check: "+str(output_directory)+"/checks/magic_drc.log"
            else:
                vioDict = dict()
                for i in range(1, len(drcSections) - 1, 2):
                    vioDict[drcSections[i]] = len(drcSections[i + 1].split("\n"))
                cnt = 0
                for key in vioDict:
                    val = vioDict[key]
                    cnt += val
                    lc.print_control("Violation Message \"" + str(key.strip()) + " \"found " + str(val) + " Times.")
                return False, "Total # of DRC violations is " + str(cnt)
    except FileNotFoundError:
        return False, "Either you didn't mount the docker, or you ran out of RAM. Otherwise, magic is broken and it segfaulted. Please check: "+str(output_directory)+"/checks/magic_drc.log"
    except OSError:
        return False, "Either you didn't mount the docker, or you ran out of RAM. Otherwise, magic is broken and it segfaulted. Please check: "+str(output_directory)+"/checks/magic_drc.log"

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
        output_directory = str(target_path) + '/drc_checks'
    else:
        output_directory = args.output_directory

    print("{{RESULT}} ", gds_drc_check(target_path, design_name, output_directory, logging_controller(str(output_directory) + '/full_log.log',target_path), '.'))
