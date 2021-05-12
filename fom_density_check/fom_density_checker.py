import os
import sys
import argparse
import subprocess
from pathlib import Path
from utils.utils import *
from xml.etree import ElementTree

def fom_density_checker(gds_input, density_check_drc, report_file):
    print("Reading from %s" % gds_input)
    print("Writing report to %s" % report_file)
    parent_path = os.path.dirname(os.path.realpath(__file__))
    sh_process = subprocess.Popen(["sh", "%s/fom_density_checker.sh" % parent_path,
                                    gds_input, report_file],
                                    stderr=subprocess.PIPE,
                                    stdout=subprocess.PIPE)
    # os.system('sh %s/fom_density_checker.sh %s %s ' % (parent_path, gds_input, report_file))
    malformed_xml = open(report_file, 'r')
    xml_lines = malformed_xml.readlines()
    xml_lines.insert(1, "<root>")
    xml_lines.append("</root>")
    with open(report_file, 'w') as fixed_xml_report:
        fixed_xml_report.write(''.join(xml_lines))

    dom = ElementTree.parse(report_file)
    errors = dom.findall('report-database/categories/category/description')
    reason = ""
    for error in errors:
        reason += error.text + "\n"
    return ( not errors ), reason
