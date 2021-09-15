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
import subprocess
from pathlib import Path

from checks.utils import utils


def gds_xor_check(input_directory, output_directory, magicrc_file_path, gds_golden_wrapper_file_path, project_config):
    parent_directory = Path(__file__).parent
    logs_directory = output_directory / 'logs'
    outputs_directory = output_directory / 'outputs'

    gds_ut_path = input_directory / 'gds' / f"{project_config['user_module']}.gds"
    xor_log_file_path = logs_directory / 'xor_check.log'

    if not gds_ut_path.exists():
        logging.error("GDS not found")
        return False

    with open(xor_log_file_path, 'w') as xor_log:
        rb_gds_size_file_path = parent_directory / 'gds_size.rb'
        rb_gds_size_cmd = ["ruby", rb_gds_size_file_path, gds_ut_path, project_config['user_module']]
        rb_gds_size_process = subprocess.run(rb_gds_size_cmd, stderr=xor_log, stdout=xor_log)
        if rb_gds_size_process.returncode != 0:
            logging.error(f"Top cell name {project_config['user_module']} not found.")
            return False

        # TODO: Try to pass the MAGTYPE as a commandline argument
        os.environ['MAGTYPE'] = 'mag'

        # Erase box
        gds_ut_box_erased_path = outputs_directory / f"{project_config['user_module']}_erased.gds"
        tcl_erase_box_file_path = parent_directory / 'erase_box.tcl'
        magic_gds_erase_box_ut_cmd = ['magic', '-dnull', '-noconsole', '-rcfile', magicrc_file_path, tcl_erase_box_file_path,
                                      gds_ut_path, gds_ut_box_erased_path, project_config['user_module']]
        subprocess.run(magic_gds_erase_box_ut_cmd, stderr=xor_log, stdout=xor_log)
        gds_golden_wrapper_box_erased_file_path = outputs_directory / f"{project_config['golden_wrapper']}_erased.gds"
        magic_gds_erase_box_golden_wrapper_cmd = ['magic', '-dnull', '-noconsole', '-rcfile', magicrc_file_path,
                                                  tcl_erase_box_file_path, gds_golden_wrapper_file_path,
                                                  gds_golden_wrapper_box_erased_file_path, project_config['user_module']]
        subprocess.run(magic_gds_erase_box_golden_wrapper_cmd, stderr=xor_log, stdout=xor_log)

        # Check if the two resulting GDSes have any differences and write them to a file
        klayout_rb_drc_xor_file_path = parent_directory / 'xor.rb.drc'
        xor_resulting_shapes_gds_file_path = outputs_directory / f"{project_config['user_module']}.xor.gds"
        xor_total_file_path = logs_directory / 'xor_check.total'
        xor_command = ['klayout', '-b', '-r', klayout_rb_drc_xor_file_path,
                       '-rd', 'ext=gds',
                       '-rd', 'top_cell=xor_target',
                       '-rd', f'thr={os.cpu_count()}',
                       '-rd', f'a={gds_ut_box_erased_path}',
                       '-rd', f'b={gds_golden_wrapper_box_erased_file_path}',
                       '-rd', f'o={xor_resulting_shapes_gds_file_path}',
                       '-rd', f'ol={xor_resulting_shapes_gds_file_path}',
                       '-rd', f'xor_total_file_path={xor_total_file_path}']
        subprocess.run(xor_command, stderr=xor_log, stdout=xor_log)

    try:
        with open(xor_total_file_path) as xor_total:
            xor_cnt = xor_total.read()
        logging.info(f"{{XOR CHECK UPDATE}} Total XOR differences: {xor_cnt}, for more details view {xor_resulting_shapes_gds_file_path}")
        if xor_cnt == '0':
            return True
        else:
            return False
    except FileNotFoundError:
        logging.error(f"XOR CHECK FILE NOT FOUND in {xor_total_file_path}")
        return False


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format=f"%(message)s")
    parser = argparse.ArgumentParser(description='Runs a magic xor check on a given GDS.')
    parser.add_argument('--input_directory', '-i', required=True, help='Design Path')
    parser.add_argument('--output_directory', '-o', required=False, default='.', help='Output Directory')
    parser.add_argument('--magicrc_file_path', '-mrc', required=True, help='magicrc file path')
    args = parser.parse_args()

    output_directory = Path(args.output_directory)
    project_config = utils.get_project_config(Path(args.input_directory))

    empty_wrapper_url = f"{project_config['link_prefix']}/gds/{project_config['golden_wrapper']}.gds.gz"
    gds_golden_wrapper_file_path = output_directory / 'outputs' / f"{project_config['golden_wrapper']}.gds"
    utils.download_gzip_file_from_url(empty_wrapper_url, gds_golden_wrapper_file_path)
    if gds_xor_check(Path(args.input_directory), output_directory, Path(args.magicrc_file_path), gds_golden_wrapper_file_path, project_config):
        logging.info("XOR Check Clean")
    else:
        logging.info("XOR Check Dirty")
