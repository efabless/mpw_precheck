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

manifest_file_name="manifest"
manifest_git_url="https://github.com/efabless/caravel/blob/develop/verilog/rtl/manifest"

def check_manifest(target_path, output_file,call_path='/usr/local/bin/base_checks')
    path=Path(target_path)
    if not os.path.exists(path):
        return False,"./verilog/rtl/ not found"
    call_path = os.path.abspath(call_path)
    
    run_manifest_check_cmd = "sh {call_path}/shasum_manifest.sh {target_path} {manifest_file_name} {manifest_git_url} {output_file}".format(
        call_path=call_path,
        target_path=target_path,
        manifest_file_name=manifest_file_name,
        manifest_git_url=manifest_git_url,
        output_file=output_file
    )

    try:
        process = subprocess.Popen(run_drc_check_cmd.split(), stderr=subprocess.PIPE, stdout=subprocess.PIPE)
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
        logFileOpener = open(output_file)
        if logFileOpener.mode == 'r':
            logContent = logFileOpener.read()
        logFileOpener.close()

        pattern = '251212'
        fail_lines= [line for line in logContent.split("\n") if pattern in line]
        if len(fail_lines):
            return False, "Manifest Checks Failed. Please Rebase your Repository to the latest Caravel master.", fail_lines
        else:
            return True, "Manifest Checks Passed. RTL Version Matches.", fail_lines

    except FileNotFoundError:
        return False, "Manifest Check Failed. Make sure you mounted the docker or you're using the docker version that has sha1sum installed.",list()
    except OSError:
        return False, "Manifest Check Failed. Make sure you mounted the docker or you're using the docker version that has sha1sum installed.", list()




if __name__ == "__main__":
    check, _, _ = check_manifest('.')
    if check:
        print("{{RESULT}} Manifest checks passed!")
    else:
        print("{{FAIL}} Manifest checks failed")
