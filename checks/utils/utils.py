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
import os
import shutil
import subprocess
from pathlib import Path

import requests
import yaml


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
        raise SystemExit(252)


def uncompress_gds(gds_path):
    cmd = f"cd {gds_path}; make uncompress;"
    try:
        logging.info(f"{{{{EXTRACTING GDS}}}} Extracting GDS files in: {gds_path}")
        subprocess.run(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
    except subprocess.CalledProcessError as error:
        logging.info(f"{{{{EXTRACTING GDS ERROR}}}} Make 'uncompress' Error: {error}")
        raise SystemExit(252)


def is_binary_file(filename):
    file_extensions = Path(filename).suffix
    return 'gds' in file_extensions or 'gz' in file_extensions


def is_not_binary_file(filename):
    return not is_binary_file(filename)


def file_hash(filename):
    def is_compressed(filename):
        with open(filename, 'rb') as f:
            return f.read(2) == b'\x1f\x8b'

    sha1 = hashlib.sha1()
    BSIZE = 65536

    if is_compressed(filename):
        f = gzip.open(filename, 'rb')
    else:
        f = open(filename, 'rb')
    while True:
        data = f.read(BSIZE)
        if not data:
            break
        sha1.update(data)
    f.close()
    return sha1.hexdigest()


def get_project_config(project_path, private):
    project_config = {}
    try:
        yaml_path = project_path / 'info.yaml'
        project = yaml.load(open(yaml_path, encoding='utf-8'), Loader=yaml.FullLoader).get('project')
    except FileNotFoundError:
        logging.error(f"{{{{YAML NOT FOUND ERROR}}}} Required YAML file 'info.yaml' was not found in path: {project_path}")
        raise SystemExit(254)

    if project:
        if not project.get('top_level_netlist'):
            logging.fatal("{{TOP LEVEL NETLIST NOT FOUND}} 'top_level_netlist' wast not found in project 'info.yaml'")
        if not project.get('user_level_netlist'):
            logging.fatal("{{USER LEVEL NETLIST NOT FOUND}} 'user_level_netlist' wast not found in project 'info.yaml'")
    else:
        logging.fatal("{{PROJECT YAML MALFORMED}} Project 'info.yaml' is structured incorrectly")

    if not project or not project.get('top_level_netlist') or not project.get('user_level_netlist'):
        raise SystemExit(254)

    # enforce spice netlist for public analog projects
    if private: 
        analog_netlist_extension = ["v", "spice"] 
    else: 
        analog_netlist_extension = ["spice"] 

    # note: get netlists
    project_config['top_netlist'] = project_path / project['top_level_netlist']
    project_config['user_netlist'] = project_path / project['user_level_netlist']

    # note: parse netlists
    top_level_netlist_extension = os.path.splitext(project_config['top_netlist'])[1]
    user_level_netlist_extension = os.path.splitext(project_config['user_netlist'])[1]

    if top_level_netlist_extension == '.v' and user_level_netlist_extension == '.v':
        project_config['netlist_type'] = 'verilog'
    elif top_level_netlist_extension == '.spice' and user_level_netlist_extension == '.spice':
        project_config['netlist_type'] = 'spice'
    else:
        logging.fatal("{{PARSING NETLISTS FAILED}} The provided top and user level netlists are neither '.spice' or '.v' files. Please adhere to the required input types.")
        raise SystemExit(254)

    # note: get project type and set remaining config
    project_config['link_prefix'] = "https://raw.githubusercontent.com/efabless/caravel/master"
    is_caravan = any(netlist in str(project_config['top_netlist']) for netlist in [f'caravan.{ext}' for ext in analog_netlist_extension])
    is_caravel = any(netlist in str(project_config['top_netlist']) for netlist in [f'caravel.{ext}' for ext in ['v', 'spice']])
    is_analog_wrapper = any(netlist in str(project_config['user_netlist']) for netlist in [f'user_analog_project_wrapper.{ext}' for ext in analog_netlist_extension])
    is_digital_wrapper = any(netlist in str(project_config['user_netlist']) for netlist in [f'user_project_wrapper.{ext}' for ext in ['v', 'spice']])
    
    if is_caravan and is_analog_wrapper:
        project_config['type'] = 'analog'
        project_config['top_module'] = 'caravan'
        project_config['user_module'] = 'user_analog_project_wrapper'
        project_config['golden_wrapper'] = 'user_analog_project_wrapper_empty'
    elif is_caravel and is_digital_wrapper:
        project_config['type'] = 'digital'
        project_config['top_module'] = 'caravel'
        project_config['user_module'] = 'user_project_wrapper'
        project_config['golden_wrapper'] = 'user_project_wrapper_empty'
    else:
        logging.fatal("{{IDENTIFYING PROJECT TYPE FAILED}} The provided top level and user level netlists are not correct.\n"
                      f"The top level netlist should point to 'caravel.(v/spice)' if your project is digital or 'caravan.({'/'.join(analog_netlist_extension)})' if your project is analog.\n"
                      f"The user level netlist should point to 'user_project_wrapper.(v/spice)' if your project is digital or 'user_analog_project_wrapper.({'/'.join(analog_netlist_extension)})' if your project is analog.")
        raise SystemExit(254)
    return project_config
