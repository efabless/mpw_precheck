import os
import sys
import argparse
import subprocess
import re
from pathlib import Path
from utils.utils import *
from xml.etree import ElementTree

def li1_density_checker(gds_input, report_file):
    parent_path = os.path.dirname(os.path.realpath(__file__))
    print("Reading from %s" % gds_input)
    print("Reporting to %s" % report_file)
    print("Running li1 density check .....")
    sh_process = subprocess.Popen(["sh", "%s/li1_density_checker.sh" % parent_path,
                                    gds_input, report_file],
                                    stderr=subprocess.PIPE,
                                    stdout=subprocess.PIPE)

    while True:
        line = sh_process.stdout.readline()
        match = re.search(r"(\d+)\/(\d+)", line.decode("utf-8"))
        # print(match)
        if match:
            count = int(match.groups()[0])
            total = int(match.groups()[1])
            print("\tProgress: %d %% ( %d / %d) "%((count/total) * 100, count, total), end='\r')
        if not line:
            break
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
