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

import re


def print_control(message, log='/usr/local/bin/logs/full_log.log'):
    if re.search(r'{{(\w+)}}(.*)', message):
        print(message)
        message = message.split("}}")[1]
    try:
        f=open(log,'a')
        f.write(str(message)+'\n')
        f.close()
    except OSError:
        print("{{EXCEPTION}} unable to print notification.")
        exit_control(255)

def dump_full_log(log='/usr/local/bin/logs/full_log.log'):
    try:
        f=open(log,"r")
        content = f.read()
        f.close()
        print("{{FULL LOG}} ", content)
    except OSError:
        print("{{EXCEPTION}} unable to print full log.")
        exit(255)


def exit_control(code,log='/usr/local/bin/logs/full_log.log'):
    dump_full_log(log)
    exit(255)