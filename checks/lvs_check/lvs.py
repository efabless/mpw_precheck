import argparse
from datetime import datetime
import logging
import os
from pathlib import Path
import shutil
from checks.utils import utils

def run_lvs(design_directory, output_directory, design_name, config_file, pdk_root, pdk):
    return utils.run_be_check(design_directory, output_directory, design_name, config_file, pdk_root, pdk, "LVS")


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
