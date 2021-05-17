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
import subprocess
import sys
from pathlib import Path

from utils.utils import *

manifest_file_name = "manifest"

default_logger_path = '/usr/local/bin/full_log.log'
default_target_path = '/usr/local/bin/caravel/'


def check_manifest(target_path, output_file, git_url, lc=logger(default_logger_path, default_target_path), call_path='/usr/local/bin/base_checks'):
    path = Path(target_path)
    if not os.path.exists(path):
        return False, str(target_path) + " not found", list()
    call_path = os.path.abspath(call_path)

    run_manifest_check_cmd = ['sh', '%s/shasum_manifest.sh' % call_path, target_path, manifest_file_name, git_url, output_file]

    try:
        process = subprocess.Popen(run_manifest_check_cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        while True:
            output = process.stdout.readline()
            if not output:
                break
            if output:
                lc.print_control(output.strip())
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.decode(sys.getfilesystemencoding())
        return False, str(error_msg)

    try:
        logFileOpener = open(output_file)
        if logFileOpener.mode == 'r':
            logContent = logFileOpener.read()
        logFileOpener.close()
        logLines = logContent.split("\n")
        if len(logLines) > 1:
            pattern = 'FAILED'
            fail_lines = [line for line in logLines if pattern in line]
            if len(fail_lines):
                return False, "Manifest Checks Failed. Please rebase your Repository to the latest Caravel master.", fail_lines
            else:
                return True, "Manifest Checks Passed. Version Matches.", fail_lines
        else:
            return False, "Manifest Check Failed. Make sure you mounted the docker or you're using the docker version that has sha1sum installed. Also, The manifest file might be deleted from caravel master at the moment.", list()
    except FileNotFoundError:
        return False, "Manifest Check Failed. Make sure you mounted the docker or you're using the docker version that has sha1sum installed. Also, The manifest file might be deleted from caravel master at the moment.", list()
    except OSError:
        return False, "Manifest Check Failed. Make sure you mounted the docker or you're using the docker version that has sha1sum installed. Also, The manifest file might be deleted from caravel master at the moment.", list()


def check_manifests(target_path, output_file, manifest_source="master", lc=logger(default_logger_path, default_target_path), call_path='/usr/local/bin/base_checks'):
    manifest_git_url = "https://raw.githubusercontent.com/efabless/caravel/{0}/manifest".format(manifest_source)
    total_check = True
    total_lines = []
    real_reason = "Manifest Checks Passed. Caravel Version Matches."
    check, reason, fail_lines = check_manifest(target_path, str(output_file) + '.log', manifest_git_url, lc, call_path)
    if not check:
        total_check = False
        total_lines = total_lines + fail_lines
        real_reason = reason
    return total_check, real_reason, total_lines
