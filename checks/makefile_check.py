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

MAKEFILE_FILENAME = 'Makefile'
MAKEFILE_TARGETS = ['clean', 'verify']


def main(*args, **kwargs):
    path = Path(kwargs['input_directory'])
    result = True
    makefile_path = path / MAKEFILE_FILENAME if path.is_dir() else path
    try:
        with open(makefile_path, encoding='utf-8') as f:
            makefile_content = f.read()
        for target in MAKEFILE_TARGETS:
            if makefile_content.count(target + ':') == 0:
                result = False
                logging.warning(f"Makefile missing target: {target}:")
            if target == 'compress':
                if makefile_content.count(target + ':') < 2:
                    result = False
                    logging.warning(f"Makefile missing target: {target}:")
    except FileNotFoundError:
        logging.error(f"{{{{MAKEFILE NOT FOUND ERROR}}}} Required Makefile 'Makefile' was not found in path: {path}")
        result = False
    return result


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, format=f"%(asctime)s | %(levelname)-7s | %(message)s", datefmt='%d-%b-%Y %H:%M:%S')
    default_input_directory = Path(__file__).parents[1] / '_default_content'
    parser = argparse.ArgumentParser(description="Runs a makefile check on a given file (looks for 'Makefile' if a directory is provided).")
    parser.add_argument('--input_directory', '-i', required=False, default=default_input_directory, help='Makefile Path')
    args = parser.parse_args()

    logging.info("Makefile Clean") if main(input_directory=args.input_directory) else logging.warning("Makefile Dirty")
