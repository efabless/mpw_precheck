import os
import sys
import argparse
import subprocess
import re
from pathlib import Path
from utils.utils import *
from time import sleep

def violations_num(xml_file_path):
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

def run_klayout_drc_script(gds_input, report_file, script_file):
    parent_path = os.path.dirname(os.path.realpath(__file__))
    klayout_cmd = ["klayout", "-b", "-r", "%s/%s" % (parent_path, script_file),
                                    "-rd","input=%s"%gds_input, "-rd", "report=%s"%report_file]
    subprocess.Popen(klayout_cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE).wait()

def drc_checker(test_name, gds_input, report_file, output_directory, drc_script_name, total_file_name):
    failed = False
    errors = []
    warnings = []
    run_klayout_drc_script(gds_input, report_file, drc_script_name)
    n_violations = violations_num(report_file)
    write_violations_num(n_violations, Path(output_directory)/total_file_name)
    if n_violations != 0:
        errors.append("There are # %s %s DRC violations"%(n_violations, test_name))
        failed = True
    return failed, errors, warnings

def offgrid_checker(gds_input, report_file, output_directory):
    return drc_checker('offgrid', gds_input, report_file, output_directory, 'offgrid.lydrc', 'offgrid_total.txt')

def met_min_ca_density_checker(gds_input, report_file, output_directory):
    return drc_checker('metal minimum clear area density', gds_input, report_file, output_directory, 'met_min_ca_density.lydrc', 'met_min_ca_density_total.txt')

def fom_density_checker(gds_input, report_file, output_directory):
    return drc_checker('FOM density', gds_input, report_file, output_directory, 'fom_density.lydrc', 'fom_density_total.txt')
