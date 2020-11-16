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
import hashlib
from urllib.request import urlopen

_license_filename = 'LICENSE'
_lib_license_filename = 'LICENSE'
_apache_license_url = 'http://www.apache.org/licenses/LICENSE-2.0.txt'

_spdx_copyright_header = 'SPDX-FileCopyrightText'
_spdx_license_header = 'SPDX-License-Identifier'

# Directories ignored for license check
IGNORED_DIRS=['third_party', '.git']

# Files ignored for license check
IGNORED_FILES=['LICENSE']

# File extentions to be ignored for license check
IGNORED_EXTS=['.mag', '.lef', '.def']

def check_main_license(path):
    data = urlopen(_apache_license_url).read().strip()
    remote_hash = hashlib.md5(data)
    try:
        local_hash = hashlib.md5(open(os.path.join(path, _license_filename), 'rb').read().strip())
        return remote_hash.hexdigest() == local_hash.hexdigest()
    except OSError:
        return False


def check_lib_license(path):
    libs = []
    if os.path.exists(path):
        for lib_path in next(os.walk(path))[1]:
            try:
                size = os.path.getsize(os.path.join(lib_path, _lib_license_filename))
                libs.append((lib_path, bool(size)))
            except OSError:
                libs.append((lib_path, False))
    return libs


def check_dir_spdx_compliance(non_compliant_list, path):
    if os.path.exists(path):
        root, dirs, files = next(os.walk(path))
        for file in files:
            try:
                result = check_file_spdx_compliance(os.path.join(root, file))
                if result:
                    non_compliant_list.append(result)
            except Exception as e:
                print("DIRECTORY (%s) ERROR: %s" % (root, e))
        for dr in dirs:
            # NOTE: ignoring third party directory for SPDX compliance
            if dr in IGNORED_DIRS:
                continue
            try:
                check_dir_spdx_compliance(non_compliant_list, os.path.join(root, dr))
            except Exception as e:
                print("DIRECTORY (%s) ERROR: %s" % (dr, e))

    return non_compliant_list


def check_file_spdx_compliance(file_path):
    spdx_compliant = False
    spdx_cp_compliant = False
    spdx_ls_compliant = False

    # Filter out ignored files and extensions
    file_base = os.path.basename(file_path)
    if file_base in IGNORED_FILES:
        return None
    _, file_ext = os.path.splitext(file_base)
    if file_ext in IGNORED_EXTS:
        return None

    try:
        with open(file_path, "tr") as f:
            lines = [x.rstrip() for x in f.readlines()]
        f.close()

        if lines and list(filter(None, lines)):
            header_char = list(filter(None, lines))[0][0]
            for line in lines:
                if line and line[0] == header_char:
                    if _spdx_copyright_header in line:
                        spdx_cp_compliant = True
                    if _spdx_license_header in line:
                        spdx_ls_compliant = True
                else:
                    break
                if spdx_cp_compliant and spdx_ls_compliant:
                    spdx_compliant = True
                    break
            return file_path if not spdx_compliant else None

    except UnicodeDecodeError:
        pass
    except Exception as e:
        print("FILE (%s) ERROR: %s" % (file_path, e))
    return None


if __name__ == "__main__":
    if check_main_license('.'):
        print("{{RESULT}} License there!")
    else:
        print("{{FAIL}} License not there or empty!")

    spdx_compliance_list = []
    spdx_compliance_list = check_dir_spdx_compliance(spdx_compliance_list, '.')
    if spdx_compliance_list:
        print("{{SPDX COMPLIANCE WARNING}} We found %s files that are not compliant with the SPDX Standard" % [x for x in spdx_compliance_list if
                                                                                                               not x.get("compliant")].__len__())
    else:
        print("{{SPDX COMPLIANCE PASSED}} Project is compliant with SPDX Standard")

    print("{{RESULT}} ", check_lib_license('.'))
