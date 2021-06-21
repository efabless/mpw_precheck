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
import os
import subprocess
import sys
from pathlib import Path

import config
from utils.utils import *

default_logger_path = '/usr/local/bin/full_log.log'
default_target_path = '/usr/local/bin/caravel/'


def gds_xor_check(target_path, pdk_root, output_directory, lc=logger(default_logger_path, default_target_path), call_path='/usr/local/bin/xor_checks'):
    gds_path = target_path + "/" + config.user_module + ".gds"
    if not os.path.exists(Path(gds_path)):
        return False, "GDS not found"

    golden_wrapper_gds = config.golden_wrapper + ".gds"
    link_prefix_gds = config.link_prefix + "/gds"

    call_path = os.path.abspath(call_path)
    run_xor_check_cmd = ['sh', '%s/run_xor_checks.sh' % call_path, target_path, '%s.gds' % config.user_module, golden_wrapper_gds, link_prefix_gds, config.user_module, output_directory, pdk_root, call_path]

    lc.print_control("{{PROGRESS}} Running XOR Checks...")

    process = subprocess.Popen(run_xor_check_cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
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

    if process.returncode == 99:
        return False, "Top cell name not found."

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
        return False, "Either you didn't mount the docker, or you ran out of RAM. Otherwise, magic is broken and it segfaulted. Please check: " + str(output_directory) + "/magic_xor.log"
    except OSError:
        return False, "Either you didn't mount the docker, or you ran out of RAM. Otherwise, magic is broken and it segfaulted. Please check: " + str(output_directory) + "/magic_xor.log"


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

    print("{{RESULT}} ", gds_xor_check(target_path, design_name, output_directory, logger(str(output_directory) + '/full_log.log', target_path), '.'))
