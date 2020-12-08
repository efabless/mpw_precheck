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
import subprocess
from pathlib import Path
from utils.utils import *

manifest_file_name="manifest"
rtl_manifest_git_url="https://raw.githubusercontent.com/efabless/caravel/develop/verilog/rtl/manifest"
maglef_manifest_git_url="https://raw.githubusercontent.com/efabless/caravel/develop/maglef/manifest"
mag_manifest_git_url="https://raw.githubusercontent.com/efabless/caravel/develop/mag/manifest"

default_logger_path = '/usr/local/bin/full_log.log'
default_target_path = '/usr/local/bin/caravel/'

def check_manifest(target_path, output_file, git_url, lc=logging_controller(default_logger_path,default_target_path),call_path='/usr/local/bin/base_checks'):
    path=Path(target_path)
    if not os.path.exists(path):
        return False,str(target_path)+" not found", list()
    call_path = os.path.abspath(call_path)
    
    run_manifest_check_cmd = "sh {call_path}/shasum_manifest.sh {target_path} {manifest_file_name} {git_url} {output_file}".format(
        call_path=call_path,
        target_path=target_path,
        manifest_file_name=manifest_file_name,
        git_url=git_url,
        output_file=output_file
    )

    try:
        process = subprocess.Popen(run_manifest_check_cmd.split(), stderr=subprocess.PIPE, stdout=subprocess.PIPE)
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
            fail_lines= [line for line in logLines if pattern in line]
            if len(fail_lines):
                return False, "Manifest Checks Failed. Please rebase your Repository to the latest Caravel master.", fail_lines
            else:
                return True, "Manifest Checks Passed. RTL Version Matches.", fail_lines
        else:
            return False, "Manifest Check Failed. Make sure you mounted the docker or you're using the docker version that has sha1sum installed. Also, The manifest file might be deleted from caravel master at the moment.",list()
    except FileNotFoundError:
        return False, "Manifest Check Failed. Make sure you mounted the docker or you're using the docker version that has sha1sum installed. Also, The manifest file might be deleted from caravel master at the moment.",list()
    except OSError:
        return False, "Manifest Check Failed. Make sure you mounted the docker or you're using the docker version that has sha1sum installed. Also, The manifest file might be deleted from caravel master at the moment.", list()


def check_manifests(target_path, output_file,lc=logging_controller(default_logger_path,default_target_path),call_path='/usr/local/bin/base_checks'):
    check, reason, fail_lines = check_manifest(target_path+'/verilog/rtl', str(output_file)+'.rtl.log', rtl_manifest_git_url, lc, call_path)
    if check:
        check, reason, fail_lines = check_manifest(target_path+'/maglef', str(output_file)+'.maglef.log', maglef_manifest_git_url, lc, call_path)
        if check:
            check, reason, fail_lines = check_manifest(target_path+'/mag', str(output_file)+'.mag.log', mag_manifest_git_url, lc, call_path)    
    return check, reason, fail_lines

