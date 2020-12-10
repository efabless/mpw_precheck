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
import yaml
from typing import NamedTuple

_yaml_filename = 'info.yaml'


class YamlStructure(NamedTuple):
    description: str
    foundry: str
    git_url: str
    organization: str
    organization_url: str
    owner: str
    process: str
    project_name: str
    tags: list
    category: str
    top_level_netlist: str
    user_level_netlist: str
    version: str
    cover_image: str


class MainYamlStructure(NamedTuple):
    project: YamlStructure


sample = YamlStructure(description='A template SoC for Google sponsored Open MPW shuttles for SKY130.', foundry='SkyWater',
                       git_url='https://github.com/efabless/caravel.git', organization='Efabless', organization_url='http://efabless.com',
                       owner='Tim Edwards', process='SKY130', project_name='Caravel', tags=['Open MPW', 'Test Harness'], category='Test Harness',
                       top_level_netlist='verilog/gl/caravel.v', user_level_netlist='verilog/gl/user_project_wrapper.v', version='1.00',
                       cover_image='doc/ciic_harness.png')


def diff_lists(li1, li2):
    return (list(list(set(li1) - set(li2)) + list(set(li2) - set(li1))))


def check_yaml(path):
    try:
        content = yaml.load(open(os.path.join(path, _yaml_filename),'r+',encoding='utf-8').read(), Loader=yaml.FullLoader)
        obj = MainYamlStructure(**content)
        yamlKeys = [a for a in dir(sample) if not a.startswith('_') and not callable(getattr(sample, a))]
        inKeys = list(content["project"].keys())
        diff = diff_lists(inKeys, yamlKeys)
        if len(diff):
            return False, None, None
        else:
            return True, content["project"]["top_level_netlist"], content["project"]["user_level_netlist"]
    except TypeError as e:
        return False, None, None
    except FileNotFoundError as e:
        return False, None, None
    except UnicodeDecodeError as e:
        print(e)
        return False, None, None


if __name__ == "__main__":
    check, a, b = check_yaml('.')
    if check:
        print("{{RESULT}} YAML file valid!")
    else:
        print("{{FAIL}} YAML file not valid!")
