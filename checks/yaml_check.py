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
import logging
from pathlib import Path
from typing import NamedTuple

import yaml

YAML_FILENAME = 'info.yaml'


# MUST_CHANGE = ['description', 'git_url', 'organization', 'organization_url', 'owner', 'project_name']


class YamlStructure(NamedTuple):
    category: str
    cover_image: str
    description: str
    foundry: str
    git_url: str
    organization: str
    organization_url: str
    owner: str
    process: str
    project_name: str
    tags: list
    top_level_netlist: str
    user_level_netlist: str
    version: str


sample = YamlStructure(project_name="Caravel", owner="Tim Edwards", version="1.00", process="SKY130", foundry="SkyWater",
                       category="Test Harness", organization="Efabless", organization_url="https://efabless.com",
                       tags=["Open MPW", "Test Harness"], git_url="https://github.com/efabless/caravel.git",
                       description="A template SoC for Google sponsored Open MPW shuttles for SKY130.",
                       top_level_netlist="verilog/gl/caravel.v", user_level_netlist="verilog/gl/user_project_wrapper.v",
                       cover_image="doc/ciic_harness.png")


def main(*args, **kwargs):
    result = True
    user_yaml_path = Path(kwargs.get('user_yaml_path'))
    default_yaml_path = Path(kwargs.get('default_yaml_path'))
    try:
        user_yaml_path = user_yaml_path / YAML_FILENAME if user_yaml_path.is_dir() else user_yaml_path
        user_yaml_content = yaml.load(open(user_yaml_path, encoding='utf-8'), Loader=yaml.FullLoader)
    except FileNotFoundError:
        logging.error(f"{{{{YAML NOT FOUND ERROR}}}} Required YAML file 'info.yaml' was not found in path: {user_yaml_path}")
        raise SystemExit(252)

    if sorted(list(user_yaml_content['project'].keys())) == sorted(list(sample._fields)):
        result = False

    # TODO: DAY 2 enable default check inside yaml
    # default_yaml_path = default_yaml_path / YAML_FILENAME if default_yaml_path.is_dir() else default_yaml_path
    # default_yaml_content = yaml.load(open(default_yaml_path, encoding='utf-8'), Loader=yaml.FullLoader)
    # for key in user_yaml_content.keys():
    #     if key in MUST_CHANGE and user_yaml_content[key] == default_yaml_content[key]:
    #         logging.warning(f"The parameter {key} in the provided 'info.yaml' is identical to the one in the default 'info.yaml'")
    #         result = False
    return result


if __name__ == '__main__':
    default_input_directory = Path(__file__).parents[1] / '_default_content'
    logging.basicConfig(level=logging.DEBUG, format=f'%(message)s')
    parser = argparse.ArgumentParser(description="Runs a yaml check on a given file (looks for 'info.yaml' if a directory is provided).")
    parser.add_argument('--input_directory', '-i', required=False, default=default_input_directory, help='Yaml Path')
    args = parser.parse_args()

    logging.info("YAML File Clean") if main(input_directory=args.input_directory) else logging.warning("YAML File Dirty")
