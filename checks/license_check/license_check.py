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
from pathlib import Path

from strsimpy.sorensen_dice import SorensenDice

# Default values for base license files
APPROVED_LICENSES_PATH = Path(__file__).parent / "_licenses/_approved_licenses"
PROHIBITED_LICENSES_PATH = Path(__file__).parent / "_licenses/_prohibited_licenses"

# Directories, files and file_extensions ignored for license check
IGNORED_DIRS = [".git", ".github", "caravel", "gl", "third_party", "precheck_results", "venv", "dependencies", "runs", "signoff"]
IGNORED_EXTS = [".cfg", ".csv", ".def", ".drc", ".gds", ".gz", ".hex", ".jpg", ".lef", ".log", ".mag", ".md", ".out", ".pdf", ".png", ".pyc", ".rdb", ".spice", ".svg", ".txt", ".vcd", ".xml", ".sdf", ".cells", ".lib", ".sdc", ".spef", ".json"]
IGNORED_FILES = [".git", ".gitignore", ".gitmodules", "info.yaml", "LICENSE", "manifest", "OPENLANE_VERSION", "PDK_SOURCES"]

# Default values for base license files
LICENSE_FILENAME = "LICENSE"
SPDX_COPYRIGHT_HEADER = "SPDX-FileCopyrightText"
SPDX_LICENSE_HEADER = "SPDX-License-Identifier"


def check_license(target_license_path, licenses_path):
    confidence_map = []
    try:
        target_license_file_content = target_license_path.open(encoding="utf-8").read()
    except FileNotFoundError:
        logging.error(f"LICENSE FILE NOT FOUND in {target_license_path.parent}")
        return None

    for license_file in licenses_path.iterdir():
        license_file_content = license_file.open(encoding="utf-8").read()
        confidence = 1 - SorensenDice().distance(license_file_content.strip(), target_license_file_content.strip())
        confidence_map.append({"license_key": license_file.stem, "confidence": confidence * 100})
    license_check_result = max(confidence_map, key=lambda x: x["confidence"])
    return license_check_result["license_key"] if license_check_result["confidence"] > 95 else None


def verify_license_compliance(path):
    path = path / LICENSE_FILENAME
    try:
        prohibited_license = check_license(path, PROHIBITED_LICENSES_PATH)
        if prohibited_license:
            logging.warning(f"A prohibited LICENSE ({prohibited_license}) was found in {path.parent}.")
            return False
        else:
            approved_license = check_license(path, APPROVED_LICENSES_PATH)
            if approved_license:
                logging.info(f"An approved LICENSE ({approved_license}) was found in {path.parent}.")
                return approved_license
            else:
                logging.warning(f"An identifiable LICENSE file was not found in {path.parent}.")
                return False
    except Exception as e:
        logging.fatal(f"VERIFY LICENSE EXCEPTION in ({path}): {e}")
        raise


def check_submodules_licenses(path):
    submodules = []
    for root, dirs, files in os.walk(path):  # note: root = submodule
        if ".git" not in dirs or root == path:
            continue
        submodules.append(verify_license_compliance(path))
    return False if False in submodules else True


def check_third_party_libs_licenses(path):
    libs = []
    for lib_path in next(os.walk(path))[1]:
        lib_path = Path(path) / lib_path
        libs.append(verify_license_compliance(lib_path))
    return False if False in libs else True


def check_dir_spdx_compliance(non_compliant_list, path, license_key=None):
    for root, dirs, files in os.walk(path):
        for file in files:
            file_under_test = Path(root) / file
            if not any(ignored_dir in Path(file_under_test.parent).parts for ignored_dir in IGNORED_DIRS):
                result = check_file_spdx_compliance(file_under_test, license_key)
                if result:
                    non_compliant_list.append(result)
    return non_compliant_list


def check_file_spdx_compliance(file_path, license_key):
    spdx_license_header = SPDX_LICENSE_HEADER if not license_key else f"{'SPDX-License-Identifier'}: {license_key}"
    spdx_compliant = spdx_cp_compliant = spdx_ls_compliant = False

    file_base = file_path.name
    if file_base in IGNORED_FILES:
        return None
    file_ext = file_path.suffix
    if file_ext in IGNORED_EXTS:
        return None

    try:
        with open(file_path, "tr", encoding="utf-8") as f:
            lines = [x.rstrip() for x in f.readlines()]
        if lines and list(filter(None, lines)):
            for line in lines:
                if line:
                    if SPDX_COPYRIGHT_HEADER in line:
                        spdx_cp_compliant = True
                    if spdx_license_header in line:
                        spdx_ls_compliant = True

                if spdx_cp_compliant and spdx_ls_compliant:
                    spdx_compliant = True
                    break
            return file_path if not spdx_compliant else None
    except UnicodeDecodeError as unicode_error:
        logging.error(f"SPDX COMPLIANCE FILE UNICODE DECODE EXCEPTION in ({file_path}): {unicode_error}")
    except FileNotFoundError as file_not_found_error:
        if not Path(file_not_found_error.filename).is_symlink():
            logging.error(f"SPDX COMPLIANCE FILE NOT FOUND in {file_path}")
        else:
            logging.error(f"SPDX COMPLIANCE SYMLINK FILE NOT FOUND in {file_path}")
    return None


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format=f"%(asctime)s | %(levelname)-7s | %(message)s", datefmt='%d-%b-%Y %H:%M:%S')
    default_input_directory = Path(__file__).parents[2] / "_default_content"
    parser = argparse.ArgumentParser(description='Runs a set of license checks on a given directory.')
    parser.add_argument('--input_directory', '-i', required=False, default=default_input_directory, help='Yaml Path')
    args = parser.parse_args()

    if verify_license_compliance(Path(args.input_directory)):
        logging.info("License Clean")
    else:
        logging.warning("License Dirty")

    if check_third_party_libs_licenses(Path(args.input_directory)):
        logging.info("Third Party Libraries Clean")
    else:
        logging.warning("Third Party Libraries Dirty")

    if check_submodules_licenses(Path(args.input_directory)):
        logging.info("Submodules Clean")
    else:
        logging.warning("Submodules Dirty")

    spdx_non_compliant_list = [str(x) for x in check_dir_spdx_compliance([], Path(args.input_directory))]
    if not spdx_non_compliant_list:
        logging.info("Project is compliant with the SPDX Standard")
    else:
        logging.warning(f"Project is not compliant with the SPDX Standard."
                        f" {spdx_non_compliant_list.__len__()} non-compliant files found: {spdx_non_compliant_list}")
