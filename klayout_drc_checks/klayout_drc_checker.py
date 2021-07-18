import os
import sys
import argparse
import subprocess
import re
from pathlib import Path
from utils.utils import *
from time import sleep

def violations_num(xml_file_path):
    # Some XML files are huge, for limited memory, read the file
    # on multiple chunks
    xml = ""
    BSIZE = 1048576 # 1 MB
    with open(xml_file_path, 'r') as marker_database_file:
        while True:
            chunk = marker_database_file.read(BSIZE)
            if chunk == '':
                break
            xml += chunk
    return xml.count('<item>')

def write_violations_num(n_violations, violations_num_file_path):
    with open(violations_num_file_path, 'w') as violations_num_file:
        violations_num_file.write("%s"%n_violations)

def run_klayout_drc_script(gds_input_file_path, report_file_path, script_file, log_file):
    klayout_cmd = ["klayout", "-b", "-r", script_file,
                                    "-rd","input=%s"%gds_input_file_path, "-rd", "report=%s"%report_file_path]
    with open(log_file, 'w') as log:
        klayout_subprocess = subprocess.Popen(klayout_cmd, stderr=log, stdout=log).wait()

def drc_checker(test_name, gds_input_file_path, report_file_path, output_directory, drc_script_path, total_file_path, log_file_path):
    failed = False
    errors = []
    warnings = []
    paths_to_check = [gds_input_file_path, output_directory, drc_script_path]
    paths_check_failed, paths_check_errors, paths_check_warnings = paths_checker(paths_to_check)
    # TODO(ahmednofal): Move to a separate dependency check for this check
    # Usage of extend is inconsistent here because of that
    errors.extend(paths_check_errors)
    warnings.extend(paths_check_warnings)
    if paths_check_failed:
        failed = True
        return failed, errors, warnings
    run_klayout_drc_script(gds_input_file_path, report_file_path, drc_script_path, log_file_path)
    paths_check_failed, paths_check_errors, paths_check_warnings = paths_checker([report_file_path])
    if paths_check_failed:
        failed = True
        errors.append("Klayout Failed to produce a marker XML database file")
        return failed, errors, warnings
    n_violations = violations_num(report_file_path)
    write_violations_num(n_violations, total_file_path)
    if n_violations != 0:
        errors.append("There are # %s %s DRC violations"%(n_violations, test_name))
        failed = True
    return failed, errors, warnings

def drc_log_total_files_paths(test_name, output_directory):
    drc_script_path = Path(__file__).absolute().parent / ('%s.lydrc'%test_name)
    log_file_path = Path(output_directory) / ('%s_check.log'%test_name)
    total_file_path = Path(output_directory) / ('%s_total.txt'%test_name)
    return drc_script_path, total_file_path, log_file_path

def offgrid_checker(gds_input_file_path, report_file_path, output_directory):
    drc_script_path, total_file_path, log_file_path = drc_log_total_files_paths('offgrid', output_directory)
    return drc_checker('offgrid', gds_input_file_path, report_file_path, output_directory, drc_script_path, total_file_path, log_file_path)

def met_min_ca_density_checker(gds_input_file_path, report_file_path, output_directory):
    drc_script_path, total_file_path, log_file_path = drc_log_total_files_paths('met_min_ca_density', output_directory)
    return drc_checker('metal minimum clear area density', gds_input_file_path, report_file_path, output_directory, drc_script_path, total_file_path, log_file_path)

def fom_density_checker(gds_input_file_path, report_file_path, output_directory):
    drc_script_path, total_file_path, log_file_path = drc_log_total_files_paths('fom_density', output_directory)
    return drc_checker('FOM density', gds_input_file_path, report_file_path, output_directory, drc_script_path, total_file_path, log_file_path)
