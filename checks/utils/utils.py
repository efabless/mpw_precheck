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

import gzip
import hashlib
import logging
import shutil
import subprocess
import sys
from pathlib import Path

import requests


def download_gzip_file_from_url(target_url, download_path):
    with open(download_path, 'wb') as f:
        status_code = None
        while status_code != 200:
            logging.info(f"Trying to get file {target_url}")
            response = requests.get(target_url, headers={'accept-encoding': 'gzip'}, stream=True)
            status_code = response.status_code
        logging.info(f"Got file {target_url}")
        gzip_file = gzip.GzipFile(fileobj=response.raw)
        shutil.copyfileobj(gzip_file, f)


def compress_gds(gds_path):
    cmd = f"cd {gds_path}; make compress;"
    try:
        logging.info(f"{{{{COMPRESSING GDS}}}} Compressing GDS files in {gds_path}")
        subprocess.run(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
    except subprocess.CalledProcessError as error:
        logging.info(f"{{{{COMPRESSING GDS ERROR}}}} Make 'compress' Error: {error}")
        sys.exit(252)


def uncompress_gds(gds_path):
    cmd = f"cd {gds_path}; make uncompress;"
    try:
        logging.info(f"{{{{EXTRACTING GDS}}}} Extracting GDS files in: {gds_path}")
        subprocess.run(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
    except subprocess.CalledProcessError as error:
        logging.info(f"{{{{EXTRACTING GDS ERROR}}}} Make 'uncompress' Error: {error}")
        sys.exit(252)


def is_binary_file(filename):
    file_extensions = Path(filename).suffix
    return 'gds' in file_extensions or 'gz' in file_extensions


def is_not_binary_file(filename):
    return not is_binary_file(filename)


def file_hash(filename):
    def is_compressed(filename):
        with open(filename, 'rb') as f:
            return f.read(2) == b'\x1f\x8b'

    BSIZE = 65536
    sha1 = hashlib.sha1()
    f = gzip.open(filename, 'rb') if is_compressed(filename) else open(filename, 'rb')

    while True:
        data = f.read(BSIZE)
        if not data:
            break
        sha1.update(data)
    f.close()
    return sha1.hexdigest()


def get_project_config(project_path):
    project_config = {}
    gds_path = project_path / 'gds'
    # note: commit id below points to mpw-3b tag
    project_config['link_prefix'] = "https://raw.githubusercontent.com/efabless/caravel/ca9025570d8180598301d874117a63d372d4243c"
    if [str(x.name) for x in gds_path.glob('user_analog_project_wrapper*')]:
        project_config['type'] = 'analog'
        project_config['top_module'] = 'caravan'
        project_config['user_module'] = 'user_analog_project_wrapper'
        project_config['golden_wrapper'] = 'user_analog_project_wrapper_empty'
        project_config['netlist_type'] = 'spice'
        project_config['top_netlist'] = project_path / "caravel/spi/lvs/caravan.spice"
        project_config['user_netlist'] = project_path / "netgen/user_analog_project_wrapper.spice"
    elif [str(x.name) for x in gds_path.glob('user_project_wrapper*')]:
        project_config['type'] = 'digital'
        project_config['top_module'] = 'caravel'
        project_config['user_module'] = 'user_project_wrapper'
        project_config['golden_wrapper'] = 'user_project_wrapper_empty'
        project_config['netlist_type'] = 'verilog'
        project_config['top_netlist'] = project_path / "caravel/verilog/gl/caravel.v"
        project_config['user_netlist'] = project_path / "verilog/gl/user_project_wrapper.v"
    else:
        logging.fatal("{{IDENTIFYING PROJECT TYPE FAILED}} A valid GDS was not found.\n"
                      f"If your project is digital, a GDS file should exist under the project's 'gds' directory containing 'user_project_wrapper.(gds)'.\n"
                      f"If your project is analog, a GDS file should exist under the project's 'gds' directory containing 'user_analog_project_wrapper.(gds)'.\n")
        sys.exit(254)
    return project_config
