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
import csv
import logging
from pathlib import Path

import requests

try:
    from checks.utils.utils import file_hash
except ImportError:
    from utils.utils import file_hash


def check_manifest(input_directory, manifest_check_log, manifest_git_url):
    result = True
    mismatches = []
    if input_directory.exists():
        hashes = requests.get(manifest_git_url).text
        hashes_filepaths_pairs = csv.reader(hashes.split('\n'), delimiter=' ', skipinitialspace=True)
        with open(manifest_check_log, 'w') as f:
            for row in hashes_filepaths_pairs:
                if len(row):
                    hash_of_file, file_path = row
                    file_path = input_directory / file_path
                    try:
                        if hash_of_file != file_hash(file_path):
                            f.write(f"{file_path}: FAILED\n")
                            mismatches.append(str(file_path))
                            result = False
                        else:
                            f.write(f"{file_path}: OK\n")
                    except FileNotFoundError:
                        logging.error(f"Manifest file {file_path.name} was not found in path: {file_path},")
                        f.write(f"{file_path}: NOT FOUND\n")
                        mismatches.append(str(file_path))
                        result = False
    else:
        logging.warning(f"Manifest path ({input_directory}) was not found")
        result = False

    if result:
        logging.info(f"Caravel version matches, for the full report check: {manifest_check_log}")
    else:
        logging.warning(f"Caravel version mismatched, found {len(mismatches)} mismatches, for the full report check: {manifest_check_log}")
    return result


def main(*args, **kwargs):
    path = kwargs['input_directory']
    output_directory = kwargs['output_directory'] / 'logs' / 'manifest_check.log'
    manifest_git_url = f"https://raw.githubusercontent.com/efabless/caravel/{kwargs['manifest_source']}/manifest"

    return check_manifest(path, output_directory, manifest_git_url)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, format=f"%(asctime)s | %(levelname)-7s | %(message)s", datefmt='%d-%b-%Y %H:%M:%S')
    parser = argparse.ArgumentParser(description='Runs a manifest check on a given directory.')
    parser.add_argument('--input_directory', '-i', required=True, help='Input Directory')
    parser.add_argument('--output_directory', '-o', required=True, help='Output Directory')
    args = parser.parse_args()
    if main(input_directory=Path(args.input_directory), output_directory=Path(args.output_directory), manifest_source='master'):
        logging.info("Manifest Clean")
    else:
        logging.warning("Manifest Dirty")
