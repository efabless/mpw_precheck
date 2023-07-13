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
import json
import logging
import re
import subprocess
import sys
from pathlib import Path


def uncompress_gds(project_path, caravel_root):
    cmd = f"make -f {caravel_root}/Makefile uncompress;"
    try:
        logging.info(f"{{{{EXTRACTING FILES}}}} Extracting compressed files in: {project_path}")
        subprocess.run(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, shell=True, cwd=str(project_path))
    except subprocess.CalledProcessError as error:
        logging.info(f"{{{{EXTRACTING FILES ERROR}}}} Make 'uncompress' Error: {error}")
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

def is_valid(string):
    if string.startswith("/"):
        return False
    else:
        return True

def is_path(string):
    if "/" in string:
        return True
    else:
        return False

def substitute_env_variables(string, env):
    if "$" in string:
        words = re.findall(r'\$\w+', string)
        for w in words:
            env_var = w[1:]  # remove leading '$'
            if env_var in env:
                string = string.replace(w, env.get(env_var), 1)  # only replace first occurence. Others will be replaced later.
            else:
                logging.error(f"ERROR LVS FAILED, couldn't find environment variable {w}")
                return None
    return string

def print_lvs_config(lvs_env):
    for lvs_key in ['EXTRACT_FLATGLOB', 'EXTRACT_ABSTRACT', 'LVS_FLATTEN', 'LVS_NOFLATTEN', 'LVS_IGNORE', 'LVS_SPICE_FILES', 'LVS_VERILOG_FILES', 'LAYOUT_FILE']:
        if lvs_key in lvs_env:
            logging.info(lvs_key + " : " + lvs_env[lvs_key])
        else:
            logging.warn(f"Missing LVS configuration variable {lvs_key}")

def parse_config_file(json_file, lvs_env):
    logging.info(f"Loading LVS environment from {json_file}")
    try:
        with open(json_file, "r") as f:
            data = json.load(f)
        for key, value in data.items():
            if type(value) == list:
                exports = lvs_env[key].split() if key in lvs_env else []
                for val in value:
                    if is_valid(val):
                        val = substitute_env_variables(val, lvs_env)
                        if val is None:  # could not substitute
                            return False
                        if val not in exports:  # only add if not already in list
                            exports.append(val)
                            if key == 'INCLUDE_CONFIGS':  # load child configs
                                lvs_env['INCLUDE_CONFIGS'] += " " + val  # prevents loading same config twice
                                if not parse_config_file(val, lvs_env):
                                    return False
                    else:
                        logging.error(f"{val} is an absolute path, paths must start with $PDK_ROOT or $UPRJ_ROOT")
                        return False
                if key != 'INCLUDE_CONFIGS':
                    lvs_env[key] = ' '.join(exports)
            else:
                if is_valid(value):
                    value = substitute_env_variables(value, lvs_env)
                    if value is None:  # could not substitute
                        return False
                    lvs_env[key] = value
                else:
                    logging.error(f"{val} is an absolute path, paths must start with $PDK_ROOT or $UPRJ_ROOT")
                    return False
        return True
    except Exception as err:
        logging.error(type(err))
        logging.error(err.args)
        logging.error(f"Error with file {json_file}")
        return False
