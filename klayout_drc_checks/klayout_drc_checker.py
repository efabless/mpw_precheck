import os
import sys
import argparse
import subprocess
import re
from pathlib import Path
from utils.utils import *
from xml.etree import ElementTree
from time import sleep

def legalize_xml(report_file):
    malformed_xml = open(report_file, 'r')
    xml_lines = malformed_xml.readlines()
    xml_lines.insert(1, "<root>")
    xml_lines.append("</root>")
    malformed_xml.close()
    with open(report_file, 'w') as fixed_xml_report:
        fixed_xml_report.write(''.join(xml_lines))

def drc_violations_from_legal_xml(xml_file_path):
    dom = ElementTree.parse(xml_file_path)
    violations = dom.findall('report-database/categories/category/description')
    return violations

# klayout writes an illegal marker database xml file
# It can not read legal xml files
# need to remove <root> </root>
def rewrite_illegal_xml(report_file, illegal_xml_report_lines):
    with open(report_file, 'w') as legal_xml_marker_db:
        legal_xml_marker_db.write(''.join(illegal_xml_report_lines))

def off_grid_checker(gds_input, report_file):
    failed = False
    errors = []
    warnings = []
    parent_path = os.path.dirname(os.path.realpath(__file__))
    sh_process = subprocess.Popen(["sh", "%s/off_grid_checker.sh" % parent_path,
                                    gds_input, report_file],
                                    stderr=subprocess.PIPE,
                                    stdout=subprocess.PIPE).wait()
    # This function call has sideeffects

    with open(report_file, 'r') as malformed_xml_marker_db:
        malformed_xml = malformed_xml_marker_db.readlines()
    legalize_xml(report_file)
    violations = drc_violations_from_legal_xml(report_file)
    rewrite_illegal_xml(report_file, malformed_xml)
    for violation in violations:
        errors.append(violation.text)
    if errors:
        failed = True
    return failed, errors, warnings
