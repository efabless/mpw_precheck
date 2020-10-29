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

if __name__ == "__main__":
    if check_main_license('.'):
        print("{{RESULT}} License there!")
    else:
        print("{{FAIL}}License not there or empty!")

    print("{{RESULT}} ", check_lib_license('.'))
