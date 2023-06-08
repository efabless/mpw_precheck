import argparse
import logging
import subprocess
import os
from pathlib import Path
from datetime import datetime

def run_lvs(design_directory, output_directory, design_name, config_file, pdk_root, pdk):
    tag = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    if not os.path.isdir(f"{design_directory}/lvs/{design_name}/lvs_results"):
        os.mkdir(f"{design_directory}/lvs/{design_name}/lvs_results")
    if not os.path.isdir(f"{design_directory}/lvs/{design_name}/lvs_results/{tag}"):
        os.mkdir(f"{design_directory}/lvs/{design_name}/lvs_results/{tag}")
    logs_directory = output_directory / 'logs'
    log_file_path = logs_directory / 'be_check.log'
    if not os.path.isdir(logs_directory):
        os.mkdir(logs_directory)
    os.environ['UPRJ_ROOT'] = f"{design_directory}"
    os.environ['LVS_ROOT'] = f'{os.getcwd()}/checks/lvs_check/'
    os.environ['WORK_ROOT'] = f"{design_directory}/lvs/{design_name}/lvs_results/{tag}"
    os.environ['LOG_ROOT'] = f"{design_directory}/lvs/{design_name}/lvs_results/{tag}/logs"
    os.environ['SIGNOFF_ROOT'] = f"{design_directory}/lvs/{design_name}/lvs_results/{tag}/output"
    os.environ['PDK'] = f'{pdk}'
    os.environ['PDK_ROOT'] = f'{pdk_root}'
    lvs_cmd = ['bash', f'{os.getcwd()}/checks/lvs_check/run_be_checks', f'{config_file}', f'{design_name}']

    with open(log_file_path, 'w') as lvs_log:
        logging.info("run: run_be_checks")  # helpful reference, print long-cmd once & messages below remain concise
        p = subprocess.run(lvs_cmd, stderr=lvs_log, stdout=lvs_log)
        # Check exit-status of all subprocesses
        stat = p.returncode
        if stat != 0:
            logging.error(f"ERROR LVS FAILED, stat={stat}, see {log_file_path}")
            return False
        else:
            return True


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format=f"%(asctime)s | %(levelname)-7s | %(message)s", datefmt='%d-%b-%Y %H:%M:%S')
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

    run_lvs(design_directory, output_directory, design_name, config_file, pdk_root, pdk)
