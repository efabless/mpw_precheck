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

from strsimpy.sorensen_dice import SorensenDice

try:
    from checks.utils.utils import is_binary_file, file_hash, is_not_binary_file
except ImportError:
    from utils.utils import is_binary_file, file_hash, is_not_binary_file

EXCLUDES = []
VIEWS = ['gds']
VERILOG_VIEWS = ['verilog/gl']


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
        return True

    similarity = 1 - SorensenDice().distance(df_readme_content, readme_content)
    if similarity > 0.75:
        logging.warning("The provided 'README.md' is identical to the default 'README.md'")
        return True
    return False


def has_default_content(input_directory, default_content_path):
    result = False
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
                                result = True
                        elif is_binary_file(default_file) and is_binary_file(target_file):
                            if file_hash(default_file) == file_hash(target_file):
                                logging.warning(f"The provided {target_file.name} is identical to the default file {default_file.name}")
                                result = True
        except FileNotFoundError as not_found_error:
            logging.error(f"File '{not_found_error.filename}' not found in {input_directory}/{view}")
            continue
    return result


def has_default_verilog(input_directory, default_content_path):
    """ Returns true if all files in the default_content_path/VERILOG_VIEWS directories match those in the input_directory
    """
    result = True
    for view in VERILOG_VIEWS:
        try:
            for default_file in get_default_view(default_content_path, view):
                default_file = Path(default_file)
                this_file_found = False
                for target_file in get_updated_view(input_directory, view):
                    target_file = Path(target_file)
                    if str(default_file) not in EXCLUDES and str(target_file) not in EXCLUDES:
                        if file_hash(default_file) == file_hash(target_file):
                            logging.warning(f"The provided {target_file.name} is identical to the default file {default_file.name}")
                            this_file_found = True
                result = result and this_file_found
        except FileNotFoundError as not_found_error:
            logging.error(f"File '{not_found_error.filename}' not found in {input_directory}/{view}")
            continue
    return result


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, format=f"%(asctime)s | %(levelname)-7s | %(message)s", datefmt='%d-%b-%Y %H:%M:%S')
    default_input_directory = Path(__file__).parents[1] / '_default_content'
    parser = argparse.ArgumentParser(description="Runs a makefile check on a given file (looks for 'Makefile' if a directory is provided).")
    parser.add_argument('--input_directory', '-i', required=False, default=default_input_directory, help='Input Directory')
    parser.add_argument('--defaults_path', '-d', required=False, default=default_input_directory, help='Defaults Path')
    args = parser.parse_args()

    if has_default_readme(Path(args.input_directory), Path(args.defaults_path)):
        logging.info("README Dirty")
    else:
        logging.info("README Clean")

    if has_default_content(Path(args.input_directory), Path(args.defaults_path)):
        logging.info("Content Dirty")
    else:
        logging.info("Content Clean")

    if has_default_verilog(Path(args.input_directory), Path(args.defaults_path)):
        logging.info("Verilog Dirty")
    else:
        logging.info("Verilog Clean")
