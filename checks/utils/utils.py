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
import sys
from pathlib import Path


def uncompress_gds(project_path):
    for compressed_file in [x for x in Path(project_path).glob('**/*.gz')]:
        logging.info(f"{{{{EXTRACTING FILES}}}} Extracting file {compressed_file} into: {compressed_file.parent}")
        uncompressed_file = compressed_file.parent / compressed_file.stem
        with gzip.open(compressed_file, 'rb') as cf, open(uncompressed_file, 'wb') as ucf:
            shutil.copyfileobj(cf, ucf)
            compressed_file.unlink()


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


def get_project_config(project_path, caravel_root):
    project_config = {}
    analog_gds_path = project_path / 'gds/user_analog_project_wrapper.gds'
    digital_gds_path = project_path / 'gds/user_project_wrapper.gds'
    if analog_gds_path.exists() and not digital_gds_path.exists():
        project_config['type'] = 'analog'
        project_config['netlist_type'] = 'spice'
        project_config['top_module'] = 'caravan'
        project_config['user_module'] = 'user_analog_project_wrapper'
        project_config['golden_wrapper'] = 'user_analog_project_wrapper_empty'
        project_config['top_netlist'] = caravel_root / "spi/lvs/caravan.spice"
        project_config['user_netlist'] = project_path / "netgen/user_analog_project_wrapper.spice"
    elif digital_gds_path.exists() and not analog_gds_path.exists():
        project_config['type'] = 'digital'
        project_config['netlist_type'] = 'verilog'
        project_config['top_module'] = 'caravel'
        project_config['user_module'] = 'user_project_wrapper'
        project_config['golden_wrapper'] = 'user_project_wrapper_empty'
        project_config['top_netlist'] = caravel_root / "verilog/gl/caravel.v"
        project_config['user_netlist'] = project_path / "verilog/gl/user_project_wrapper.v"
    else:
        logging.fatal("{{IDENTIFYING PROJECT TYPE FAILED}} A single valid GDS was not found. "
                      "If your project is digital, a GDS file should exist under the project's 'gds' directory named 'user_project_wrapper(.gds/.gds.gz)'. "
                      "If your project is analog, a GDS file should exist under the project's 'gds' directory named 'user_analog_project_wrapper(.gds/.gds.gz)'.")
        sys.exit(254)
    return project_config
