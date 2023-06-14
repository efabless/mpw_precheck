import argparse
import logging
import subprocess
import os
from pathlib import Path
from datetime import datetime
import json
import re
import shutil

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

def print_lvs_config(lvs_env):
    for lvs_key in ['EXTRACT_FLATGLOB', 'EXTRACT_ABSTRACT', 'LVS_FLATTEN', 'LVS_NOFLATTEN', 'LVS_IGNORE', 'LVS_SPICE_FILES', 'LVS_VERILOG_FILES', 'LAYOUT_FILE']:
        if lvs_key in lvs_env:
            logging.info(lvs_key + " : " + lvs_env[lvs_key])
        else:
            logging.warn(f"Missing LVS configuration variable {lvs_key}")

def run_lvs(design_directory, output_directory, design_name, config_file, pdk_root, pdk):
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
        logging.error(f"ERROR LVS FAILED, Could not find LVS configuration file {config_file}")
        return False
    lvs_env['INCLUDE_CONFIGS'] = f"{config_file}"
    if not parse_config_file(config_file, lvs_env):
        return False
    lvs_cmd = ['bash', f'{os.getcwd()}/checks/lvs_check/run_be_checks', f'{config_file}', f'{design_name}']
    print_lvs_config(lvs_env)
    lvs_env.update(os.environ)
    with open(log_file_path, 'w') as lvs_log:
        logging.info("run: run_be_checks")
        logging.info(f"LVS output directory: {output_directory}")
        p = subprocess.run(lvs_cmd, stderr=lvs_log, stdout=lvs_log, env=lvs_env)
        # Check exit-status of all subprocesses
        stat = p.returncode
        if stat != 0:
            logging.error(f"ERROR LVS FAILED, stat={stat}, see {log_file_path}")
            return False
        else:
            if os.path.isdir(f"{tmp_dir}"):
                shutil.rmtree(tmp_dir)
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

    tag = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    lvs_output = f"{output_directory}/{design_name}/lvs_results/{tag}"
    if not os.path.isdir(f"{output_directory}/{design_name}/lvs_results"):
        os.mkdir(f"{output_directory}/{design_name}/lvs_results")
    if not os.path.isdir(lvs_output):
        os.mkdir(lvs_output)

    if not run_lvs(design_directory, lvs_output, design_name, config_file, pdk_root, pdk):
        logging.error("LVS Failed.")
    else:
        if os.path.isdir(f"{lvs_output}/tmp"):
            shutil.rmtree(f"{lvs_output}/tmp")
        logging.info("LVS Passed!")
