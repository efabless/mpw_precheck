import argparse
import os
import logging
import json
from pathlib import Path


def run_pdn(config_file):
    if not os.path.exists(config_file):
        logging.error(f"OpenLane configuration file {config_file} doesn't exist")
        return False

    with open(config_file, "r") as f:
        data = json.load(f)

    if "FP_PDN_HPITCH" not in data or "FP_PDN_HPITCH_MULT" not in data:
        logging.error("FP_PDN_HPITCH or FP_PDN_HPITCH_MULT not defined in OpenLane configuration file")
        return False

    if type(data["FP_PDN_HPITCH_MULT"]) is str:
        logging.error("FP_PDN_HPITCH_MULT can't be a string")
        return False

    if data["FP_PDN_HPITCH"] != "expr::60 + $FP_PDN_HPITCH_MULT * 30":
        logging.error(f"FP_PDN_HPITCH in OpenLane configuration file has incorrect values, it should be expr::60 + $FP_PDN_HPITCH_MULT * 30")
        return False

    if data["FP_PDN_HPITCH_MULT"] < 0:
        logging.error(f"FP_PDN_HPITCH_MULT in OpenLane configuration file can't be a negative number")
        return False

    if not isinstance(data["FP_PDN_HPITCH_MULT"], int):
        logging.error(f"FP_PDN_HPITCH_MULT in OpenLane configuration file can't be a floating number")
        return False

    return True

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format=f"%(asctime)s | %(levelname)-7s | %(message)s", datefmt='%d-%b-%Y %H:%M:%S')
    parser = argparse.ArgumentParser(description='Runs LVS on a given design.')
    parser.add_argument('--config_file', '-c', required=True, help='OpenLane configuration file path')
    args = parser.parse_args()
    config_file = Path(args.config_file)
    result = run_pdn(config_file)

    if result:
        logging.info("PDN multiple check Passed!")
    else:
        logging.error("PDN multiple check Failed!")
