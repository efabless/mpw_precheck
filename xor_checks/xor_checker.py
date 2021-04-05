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
import sys
import argparse
import subprocess
from pathlib import Path
from utils.utils import *

default_logger_path = '/usr/local/bin/full_log.log'
default_target_path = '/usr/local/bin/caravel/'
golden_wrapper = 'user_project_wrapper_empty.gds'
link_prefix = 'https://raw.githubusercontent.com/efabless/caravel/master/gds'
design_name = 'user_project_wrapper'

def gds_xor_check(target_path, pdk_root, output_directory, lc=logging_controller(default_logger_path,default_target_path), call_path='/usr/local/bin/xor_checks'):
    gds_path=target_path+"/"+design_name+".gds"
    if not os.path.exists(Path(gds_path)):
        return False,"GDS not found"

    call_path = os.path.abspath(call_path)
    run_xor_check_cmd = \
        "sh {call_path}/run_xor_checks.sh {target_path} {user_gds} {golden_wrapper} {link_prefix} {design_name} {out_dir} {pdk_root} {call_path}".format(
        target_path=target_path,
        user_gds=design_name+'.gds',
        golden_wrapper=golden_wrapper,
        link_prefix=link_prefix,
        call_path=call_path,
        pdk_root=pdk_root,
        design_name=design_name,
        out_dir=output_directory
    )

    lc.print_control("{{PROGRESS}} Running XOR Checks...")

    process = subprocess.Popen(run_xor_check_cmd.split(), stderr=subprocess.PIPE, stdout=subprocess.PIPE)
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
        xorFileOpener = open(output_directory + '/xor_total.txt')
        if xorFileOpener.mode == 'r':
            xorContent = xorFileOpener.read()
        xorFileOpener.close()
        lc.print_control(xorContent)
        if len(xorContent):
            xor_cnt = xorContent.split('=')[1].strip()
            if xor_cnt == '0':
                return True, "XOR Checks Passed"
            else:
                return False, "XOR Differences count is {0}. Please view {1}/*.xor.* for more details.".format(xor_cnt, output_directory)
        else:
            return False, "No xor Result retreived. Please view the full_log.log and xor.log for more details."
    except FileNotFoundError:
        return False, "Either you didn't mount the docker, or you ran out of RAM. Otherwise, magic is broken and it segfaulted. Please check: "+str(output_directory)+"/magic_xor.log"
    except OSError:
        return False, "Either you didn't mount the docker, or you ran out of RAM. Otherwise, magic is broken and it segfaulted. Please check: "+str(output_directory)+"/magic_xor.log"

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Runs a magic xor check on a given GDS.')

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
        output_directory = str(target_path) + '/xor_checks'
    else:
        output_directory = args.output_directory

    print("{{RESULT}} ", gds_xor_check(target_path, design_name, output_directory, logging_controller(str(output_directory) + '/full_log.log',target_path), '.'))
