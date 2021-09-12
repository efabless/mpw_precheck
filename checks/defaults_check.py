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
from glob import glob
from pathlib import Path

import yaml
from strsimpy.sorensen_dice import SorensenDice

try:
    from checks.utils.utils import is_binary_file, file_hash, is_not_binary_file
except ImportError:
    from utils.utils import is_binary_file, file_hash, is_not_binary_file

EXCLUDES = []
MUST_CHANGE = ['description', 'git_url', 'organization', 'organization_url', 'owner', 'project_name']
VIEWS = ['gds']
YAML_FILENAME = 'info.yaml'


def get_view(name, directory):
    return glob(str(Path(directory, name, '*')))


def get_default_view(default_content_path, name):
    return get_view(name, default_content_path)


def get_updated_view(input_directory, name):
    return get_view(name, input_directory)


def has_default_readme(input_directory, default_content_path):
    default_content_path = default_content_path / 'README.md'
    input_directory = input_directory / 'README.md'
    try:
        df_readme_content = default_content_path.open(encoding='utf-8').read()
        readme_content = input_directory.open(encoding='utf-8').read()
    except FileNotFoundError:
        logging.error(f"File 'README.md' not found in {input_directory}")
        return False

    similarity = 1 - SorensenDice().distance(df_readme_content, readme_content)
    if similarity > 0.75:
        logging.warning("The provided 'README.md' is identical to the default 'README.md'")
        return False
    return True


def has_default_project_config(input_directory, default_content_path):
    result = True
    default_config = user_prj_config = {}
    try:
        default_config = yaml.load(open(default_content_path / YAML_FILENAME, encoding='utf-8'), Loader=yaml.FullLoader)['project']
        user_prj_config = yaml.load(open(input_directory / YAML_FILENAME, encoding='utf-8'), Loader=yaml.FullLoader)['project']
    except FileNotFoundError:
        logging.error(f"File 'info.yaml' not found in {input_directory}")
        result = False

    for key in user_prj_config.keys():
        if key in MUST_CHANGE and user_prj_config[key] == default_config[key]:
            logging.warning(f"The parameter {key} in the provided 'info.yaml' is identical to the one in the default 'info.yaml'")
            result = False
    return result


def has_default_content(input_directory, default_content_path):
    result = True

    for view in VIEWS:
        try:
            for target_file in get_updated_view(input_directory, view):
                target_file = Path(target_file)
                for default_file in get_default_view(default_content_path, view):
                    default_file = Path(default_file)
                    if str(default_file) not in EXCLUDES and str(target_file) not in EXCLUDES:
                        if is_not_binary_file(default_file) and is_not_binary_file(target_file):
                            default_file_content = default_file.open(encoding='utf-8').read()
                            target_file_content = target_file.open(encoding='utf-8').read()
                            similarity = 1 - SorensenDice().distance(default_file_content, target_file_content)
                            if similarity > 0.75:
                                logging.warning(f"The provided {target_file.name} is too similar to the default file {default_file.name}")
                                result = False
                        elif is_binary_file(default_file) and is_binary_file(target_file):
                            if file_hash(default_file) == file_hash(target_file):
                                logging.warning(f"The provided {target_file.name} is identical to the default file {default_file.name}")
                                result = False
        except FileNotFoundError as not_found_error:
            logging.error(f"File '{not_found_error.filename}' not found in {input_directory}/{view}")
            continue
    return result


if __name__ == '__main__':
    default_input_directory = Path(__file__).parents[1] / '_default_content'
    logging.basicConfig(level=logging.DEBUG, format=f'%(message)s')
    parser = argparse.ArgumentParser(description="Runs a makefile check on a given file (looks for 'Makefile' if a directory is provided).")
    parser.add_argument('--input_directory', '-i', required=False, default=default_input_directory, help='Input Directory')
    parser.add_argument('--defaults_path', '-d', required=False, default=default_input_directory, help='Defaults Path')
    args = parser.parse_args()

    if has_default_readme(Path(args.input_directory), Path(args.defaults_path)):
        logging.info("README Clean")
    else:
        logging.info("README Dirty")

    if has_default_project_config(Path(args.input_directory), Path(args.defaults_path)):
        logging.info("Project Config Clean")
    else:
        logging.info("Project Config Dirty")

    if has_default_content(Path(args.input_directory), Path(args.defaults_path)):
        logging.info("Content Clean")
    else:
        logging.info("Content Dirty")
