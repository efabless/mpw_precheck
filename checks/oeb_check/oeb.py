

import argparse
from datetime import datetime
import logging
import os
from pathlib import Path
import shutil
import subprocess
from checks.utils import utils


def run_oeb(design_directory, output_directory, design_name, config_file, pdk_root, pdk):
    log_path = f"{output_directory}/logs"
    report_path = f"{output_directory}/outputs/reports"
    log_file_path = f"{log_path}/be_check.log"
    tmp_dir = f"{output_directory}/tmp"
    if not os.path.isdir(log_path):
        os.mkdir(log_path)
    if not os.path.isdir(tmp_dir):
        os.mkdir(f"{tmp_dir}")
    if not os.path.isdir(f"{output_directory}/outputs"):
        os.mkdir(f"{output_directory}/outputs")
    if not os.path.isdir(report_path):
        os.mkdir(f"{report_path}")

    lvs_env = dict()
    lvs_env['UPRJ_ROOT'] = f"{design_directory}"
    lvs_env['LVS_ROOT'] = f'{os.getcwd()}/checks/lvs_check/'
    lvs_env['WORK_ROOT'] = f"{tmp_dir}"
    lvs_env['LOG_ROOT'] = f"{log_path}"
    lvs_env['SIGNOFF_ROOT'] = f"{report_path}"
    lvs_env['PDK'] = f'{pdk}'
    lvs_env['PDK_ROOT'] = f'{pdk_root}'
    if not os.path.exists(f"{config_file}"):
        logging.error(f"ERROR OEB CHECK FAILED, Could not find LVS configuration file {config_file}")
        return False
    lvs_env['INCLUDE_CONFIGS'] = f"{config_file}"
    if not utils.parse_config_file(config_file, lvs_env):
        return False
    lvs_cmd = ['bash', f'{os.getcwd()}/checks/oeb_check/run_oeb_check', f'{config_file}', f'{design_name}']
    utils.print_lvs_config(lvs_env)
    lvs_env.update(os.environ)
    with open(log_file_path, 'w') as lvs_log:
        logging.info("run: run_oeb_checks")
        logging.info(f"oeb output directory: {output_directory}")
        p = subprocess.run(lvs_cmd, stderr=lvs_log, stdout=lvs_log, env=lvs_env)
        # Check exit-status of all subprocesses
        stat = p.returncode
        if stat != 0:
            logging.error(f"ERROR OEB FAILED, stat={stat}, see {log_file_path}")
            return False
        else:
            if os.path.isdir(f"{tmp_dir}"):
                shutil.rmtree(tmp_dir)
            return True


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format="%(asctime)s | %(levelname)-7s | %(message)s", datefmt='%d-%b-%Y %H:%M:%S')
    parser = argparse.ArgumentParser(description='Runs LVS on a given design.')
    parser.add_argument('--design_directory', '-g', required=True, help='Design Directory')
    parser.add_argument('--output_directory', '-o', required=True, help='Output Directory')
    parser.add_argument('--design_name', '-d', required=True, help='Design Name')
    parser.add_argument('--config_file', '-c', required=True, help='LVS config file')
    parser.add_argument('--pdk_path', '-p', required=True, help='pdk path')
    args = parser.parse_args()
    output_directory = Path(args.output_directory)
    design_directory = Path(args.design_directory)
    config_file = Path(args.config_file)
    design_name = args.design_name
    pdk_path = Path(args.pdk_path)
    pdk = pdk_path.name
    pdk_root = pdk_path.parent

    tag = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    lvs_output = f"{output_directory}/{design_name}/oeb_results/{tag}"
    if not os.path.isdir(f"{output_directory}/{design_name}/oeb_results"):
        os.mkdir(f"{output_directory}/{design_name}/oeb_results")
    if not os.path.isdir(lvs_output):
        os.mkdir(lvs_output)

    if not run_oeb(design_directory, lvs_output, design_name, config_file, pdk_root, pdk):
        logging.error("OEB check Failed.")
    else:
        if os.path.isdir(f"{lvs_output}/tmp"):
            shutil.rmtree(f"{lvs_output}/tmp")
        logging.info("OEB check Passed!")
