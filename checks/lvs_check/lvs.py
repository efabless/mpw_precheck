import argparse
import logging
import subprocess
import os
from pathlib import Path
from datetime import datetime
import json
import re

def is_path(string):
    string = string.strip()
    if string[0] in ["/", "\\"]:
        return True
    return False


def parse_config_file(json_file, lvs_env):
    with open(json_file, "r") as f:
        data = json.load(f)
    for key, value in data.items():
        if type(value) == list:
            exports = []
            for val in value:
                if "$" in val:
                    words = re.findall(r'\$\w+', val)
                    for w in words:
                        env_var = w.split("$")[1]
                        if env_var in lvs_env:
                            if not is_path(val):
                                val = val.replace(w, lvs_env.get(env_var))
                            else:
                                val = os.path.join(os.path.dirname(val), os.path.splitext(val)[0].replace(w, lvs_env.get(env_var)) + os.path.splitext(val)[1])
                        else:
                            logging.error(f"ERROR LVS FAILED, couldn't find environment variable {w}")
                            return False
                exports.append(val)
            lvs_env[key] = ' '.join(exports)
        else:
            if "$" in value:
                words = re.findall(r'\$\w+', value)
                for w in words:
                    env_var = w.split("$")[1]
                    if env_var in lvs_env:
                        if not is_path(value):
                            value = value.replace(w, lvs_env.get(env_var))
                        else:
                            value = os.path.join(os.path.dirname(value), os.path.splitext(value)[0].replace(w, lvs_env.get(env_var)) + os.path.splitext(value)[1])
                    else:
                        logging.error(f"ERROR LVS FAILED, couldn't find environment variable {w}")
                        return False
            lvs_env[key] = value
    return True


def run_lvs(design_directory, output_directory, design_name, config_file, pdk_root, pdk):
    tag = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    if not os.path.isdir(f"{design_directory}/lvs/{design_name}/lvs_results"):
        os.mkdir(f"{design_directory}/lvs/{design_name}/lvs_results")
    output_directory = f"{design_directory}/lvs/{design_name}/lvs_results/{tag}"
    if not os.path.isdir(f"{output_directory}"):
        os.mkdir(f"{output_directory}")
    log_file_path = f"{output_directory}/be_check.log"
    if not os.path.isdir(f"{output_directory}/log"):
        os.mkdir(f"{output_directory}/log")
    lvs_env = os.environ.copy()
    lvs_env['UPRJ_ROOT'] = f"{design_directory}"
    lvs_env['LVS_ROOT'] = f'{os.getcwd()}/checks/lvs_check/'
    lvs_env['WORK_ROOT'] = f"{output_directory}"
    lvs_env['LOG_ROOT'] = f"{output_directory}/log"
    lvs_env['SIGNOFF_ROOT'] = f"{output_directory}/output"
    lvs_env['PDK'] = f'{pdk}'
    lvs_env['PDK_ROOT'] = f'{pdk_root}'
    if not os.path.exists(f"{config_file}"):
        logging.error(f"ERROR LVS FAILED, Could not find LVS configuration file {config_file}")
        return False
    if not parse_config_file(config_file, lvs_env):
        return False
    lvs_cmd = ['bash', f'{os.getcwd()}/checks/lvs_check/run_be_checks', f'{config_file}', f'{design_name}']

    with open(log_file_path, 'w') as lvs_log:
        logging.info("run: run_be_checks")  # helpful reference, print long-cmd once & messages below remain concise
        p = subprocess.run(lvs_cmd, stderr=lvs_log, stdout=lvs_log, env=lvs_env)
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
