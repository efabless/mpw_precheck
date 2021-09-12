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
import os
from pathlib import Path

BANNED_WORDS = ['blacklist', 'slave', 'whitelist']  # Banned Keywords
DOCUMENTATION_EXTS = ['.doc', '.docx', '.html', '.md', '.odt', '.rst']  # Valid Document Extensions
IGNORED_DIRS = ['.git', 'third_party']  # Directories ignored for documentation check

DOCUMENTATION_FILENAME = 'README'


def check_inclusive_language(file):
    with open(file, encoding='utf-8') as f:
        content = f.read()
    for word in BANNED_WORDS:
        if word in content:
            logging.warning(f"The documentation file ({file}) contains the non-inclusive word: {word}")
            return False
    return True


def main(*args, **kwargs):
    path = kwargs['input_directory']
    found = False
    result = True
    readme_path = Path(path) / DOCUMENTATION_FILENAME
    if not readme_path.exists():
        for ext in DOCUMENTATION_EXTS:
            readme_ext_path = Path(path) / f'{DOCUMENTATION_FILENAME}{ext}'
            if readme_ext_path.exists():
                found = True
                break

    if found:
        for root, dirs, files in os.walk(path):
            for file in files:
                file_path = Path(root) / file
                if file_path.parent not in IGNORED_DIRS and file_path.suffix in DOCUMENTATION_EXTS:
                    extension = file_path.suffix
                    if extension in DOCUMENTATION_EXTS:
                        check = check_inclusive_language(file_path)
                        if not check:
                            result = False
        return result
    else:
        logging.warning(f"No documentation file(s) was found")
        result = False
        return result


if __name__ == '__main__':
    default_input_directory = Path(__file__).parents[1] / '_default_content'
    logging.basicConfig(level=logging.DEBUG, format=f'%(message)s')
    parser = argparse.ArgumentParser(description="Runs a documentation check on a given directory.")
    parser.add_argument('--input_directory', '-i', required=False, default=default_input_directory, help='Input Directory')
    args = parser.parse_args()

    logging.info("Documentation Clean") if main(input_directory=args.input_directory) else logging.warning("Documentation Dirty")
