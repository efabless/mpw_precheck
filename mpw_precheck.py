# SPDX-FileCopyrightText: 2020-2022 Efabless Corporation
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
import datetime
import json
import logging
import os
import subprocess
import sys
from pathlib import Path

import precheck_logger
from check_manager import get_check_manager, open_source_checks, private_checks
from checks.utils.utils import file_hash, get_project_config, uncompress_gds


def log_info(precheck_config, project_config):
    gds_info_path = precheck_config['log_path'].parent / 'gds.info'
    pdks_info_path = precheck_config['log_path'].parent / 'pdks.info'
    tools_info_path = precheck_config['log_path'].parent / 'tools.info'

    logging.info(f"{{{{Project Type Info}}}} {project_config['type']}")

    with open(gds_info_path, 'w') as gds_info:
        user_module_hash = file_hash(f"{precheck_config['input_directory']}/gds/{project_config['user_module']}.gds")
        gds_info.write(f"{project_config['user_module']}.gds: {user_module_hash}")
        logging.info(f"{{{{Project GDS Info}}}} {project_config['user_module']}: {user_module_hash}")
    with open(tools_info_path, 'w') as tools_info:
        klayout_version = subprocess.check_output(['klayout', '-v'], encoding='utf-8').replace('KLayout', '').lstrip().rstrip()
        magic_version = subprocess.check_output(['magic', '--version'], encoding='utf-8').rstrip()
        tools_info.write(f"KLayout: {klayout_version}\n")
        tools_info.write(f"Magic: {magic_version}")
        logging.info(f"{{{{Tools Info}}}} KLayout: v{klayout_version} | Magic: v{magic_version}")
    with open(pdks_info_path, 'w') as pdks_info:
        try:
            with open(precheck_config['pdk_path'] / '.config/nodeinfo.json') as f:
                pdk_nodeinfo = json.load(f)
                open_pdks_commit = pdk_nodeinfo['commit']['open_pdks']
                pdk_commit = pdk_nodeinfo['reference'].get('skywater_pdk', pdk_nodeinfo['reference'].get('gf180mcu_pdk'))
            pdks_info.write(f"Open PDKs {open_pdks_commit}\n")
            pdks_info.write(f"{precheck_config['pdk_path'].name.upper()} PDK {pdk_commit}")
            logging.info(f"{{{{PDKs Info}}}} {precheck_config['pdk_path'].name.upper()}: {pdk_commit} | Open PDKs: {open_pdks_commit}")
        except Exception as e:
            logging.error(f"MPW Precheck failed to retreive {precheck_config['pdk_path'].name.upper()} PDK & Open PDKs commits: {e}")


def check_log_for_magic_drc(path):
    try:
        with open(path, 'r') as log_file:
            for line in log_file:
                if "{{MAGIC DRC CHECK FAILED}}" in line:
                    return True
    except FileNotFoundError:
        logging.error(f"Error: The file at '{path}' does not exist.")
    except Exception as e:
        logging.error(f"An error occurred: {e}")
    return False


def run_precheck_sequence(precheck_config, project_config):
    results = {}
    logging.info(f"{{{{START}}}} Precheck Started, the full log '{precheck_config['log_path'].name}' will be located in '{precheck_config['log_path'].parent}'")
    logging.info(f"{{{{PRECHECK SEQUENCE}}}} Precheck will run the following checks: [{', '.join([get_check_manager(x, precheck_config, project_config).__surname__ for x in precheck_config['sequence']])}]")
    for check_count, entry in enumerate(precheck_config['sequence'], start=1):
        check = get_check_manager(entry, precheck_config, project_config)
        if check:
            logging.info(f"{{{{STEP UPDATE}}}} Executing Check {check_count} of {len(precheck_config['sequence'])}: {check.__surname__}")
            results[check.__surname__] = check.run()

    logging.info(f"{{{{FINISH}}}} Executing Finished, the full log '{precheck_config['log_path'].name}' can be found in '{precheck_config['log_path'].parent}'")
    if check_log_for_magic_drc(precheck_config['log_path']):
        logging.warn("{{WARNING}} Magic DRC failed !")
    if False not in list(results.values()):
        logging.info("{{SUCCESS}} All Checks Passed !!!")
    else:
        failed_checks = [x for x in results.keys() if results[x] is False]
        logging.fatal(f"{{{{FAILURE}}}} {len(failed_checks)} Check(s) Failed: {failed_checks} !!!")
        sys.exit(2)


def main(*args, **kwargs):
    check_managers = private_checks if kwargs['private'] else open_source_checks
    precheck_config = dict(input_directory=Path(kwargs['input_directory']),
                           output_directory=Path(kwargs['output_directory']),
                           caravel_root=Path(kwargs['caravel_root']),
                           pdk_path=Path(kwargs['pdk_path']),
                           private=kwargs['private'],
                           sequence=kwargs['sequence'],
                           log_path=Path(kwargs['log_path']),
                           default_content=Path(kwargs['default_content']),
                           check_managers=check_managers)

    uncompress_gds(precheck_config['input_directory'], precheck_config['caravel_root'])
    project_config = get_project_config(precheck_config['input_directory'], precheck_config['caravel_root'])
    gds_file_path = precheck_config['input_directory'] / f"gds/{project_config['user_module']}.gds"
    compressed_gds_file_path = precheck_config['input_directory'] / f"gds/{project_config['user_module']}.gds.gz"
    if gds_file_path.exists() and compressed_gds_file_path.exists():
        logging.fatal("{{GDS VIOLATION}} Both a compressed and an uncompressed version of the gds exist, ensure only one design file exists.")
        sys.exit(255)

    log_info(precheck_config, project_config)
    # note: update to filter sequence based on supported pdks
    precheck_config['sequence'] = [check for check in precheck_config['sequence'] if precheck_config['pdk_path'].stem in get_check_manager(check, precheck_config, project_config).__supported_pdks__ and project_config['type'] in get_check_manager(check, precheck_config, project_config).__supported_type__]
    run_precheck_sequence(precheck_config=precheck_config, project_config=project_config)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Runs the mpw precheck tool.", allow_abbrev=False)
    parser.add_argument('-i', '--input_directory', required=True, help="INPUT_DIRECTORY Absolute Path to the project.")
    parser.add_argument('-p', '--pdk_path', required=True, help="PDK_PATH, points to the installation path of the pdk (variant specific)")
    parser.add_argument('-o', '--output_directory', required=False, help="OUTPUT_DIRECTORY, default=<input_directory>/precheck_results/DD_MMM_YYYY___HH_MM_SS.")
    parser.add_argument('--private', action='store_true', help=f"If provided, precheck skips {open_source_checks.keys() - private_checks.keys()}  checks that qualify the project to be Open Source")
    parser.add_argument('checks', metavar='check', type=str, nargs='*', choices=list(open_source_checks.keys()).append([]), help=f"Checks to be run by the precheck: {' '.join(open_source_checks.keys())}")
    parser.add_argument('--skip_checks', metavar='check', type=str, nargs='*', choices=list(open_source_checks.keys()).append([]), help=f"Checks not to be run by the precheck: {' '.join(open_source_checks.keys())}")
    args = parser.parse_args()

    # NOTE Separated to allow the option later on for a run tag
    tag = f"{datetime.datetime.utcnow():%d_%b_%Y___%H_%M_%S}".upper()
    output_directory = args.output_directory if args.output_directory else f"{args.input_directory}/precheck_results/{tag}"
    Path(f"{output_directory}/logs").mkdir(parents=True, exist_ok=True)
    Path(f"{output_directory}/outputs").mkdir(parents=True, exist_ok=True)
    Path(f"{output_directory}/outputs/reports").mkdir(parents=True, exist_ok=True)
    log_path = Path(output_directory) / 'logs/precheck.log'
    precheck_logger.initialize_root_logger(log_path)

    if not Path('/.dockerenv').exists():
        logging.warning("MPW Precheck is being executed outside Docker, this mode is no longer supported. Efabless bears no responsibility for the generated results !!!")
        question = lambda q: input(q).lower().strip() == "continue" or question(q)
        question("If you want to proceed please type 'continue' and press 'Enter'.\n")

    if 'GOLDEN_CARAVEL' not in os.environ:
        logging.critical("`GOLDEN_CARAVEL` environment variable is not set. Please set it to point to absolute path to the golden caravel")
        sys.exit(1)

    all_checks = [check.lower() for check in (private_checks.keys() if args.private else open_source_checks.keys())]
    input_checks = [check.lower() for check in args.checks] if args.checks else all_checks
    skip_checks = [check.lower() for check in args.skip_checks] if args.skip_checks else []
    input_checks = [check for check in input_checks if check in all_checks]
    skip_checks = [check for check in skip_checks if check in all_checks]
    sequence = [check for check in input_checks if check not in skip_checks]

    main(input_directory=args.input_directory,
         output_directory=output_directory,
         caravel_root=os.environ['GOLDEN_CARAVEL'],
         pdk_path=args.pdk_path,
         private=args.private,
         sequence=sequence,
         log_path=log_path,
         default_content='_default_content')
