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
import yaml
from typing import NamedTuple

_yaml_filename = 'info.yaml'

class YamlStructure(NamedTuple):
    name: str
    description: str
    git_url: str
    version: int = 1
    top_level_netlist: str
    user_level_netlist: str


def check_yaml(path):
    try:
        content = yaml.load(open(os.path.join(path, _yaml_filename)).read())
        obj = YamlStructure(**content)
        return True, content["top_level_netlist"], content["user_level_netlist"]
    except TypeError as e:
        return False, None, None
    except FileNotFoundError as e:
        return False, None, None


if __name__ == "__main__":
    if check_yaml('.'):
        print("{{RESULT}} YAML file valid!")
    else:
        print("{{FAIL}} YAML file not valid!")
