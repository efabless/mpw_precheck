import os
import sys
import argparse
import subprocess
import re
from pathlib import Path
from utils.utils import *


class KlayoutDRCCheck:
    def __init__(self, gds_input_file_path, output_directory):
        self.gds_input_file_path = Path(gds_input_file_path)
        self.output_directory = Path(output_directory)
        self.report_file_path = Path(self.output_directory) / ('%s_check.xml'%self.__ref__)
        self.total_file_path = Path(self.output_directory) / ('%s_check.txt'%self.__ref__)
        self.log_file_path = Path(self.output_directory) / ('%s_total.log'%self.__ref__)
        self.n_violations = 0
        self.failed = False

    @classmethod
    def violations_num(cls, xml_file_path):
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

    @classmethod
    def write_violations_num_to_file(cls, n_violations, violations_num_file_path):
        with open(violations_num_file_path, 'w') as violations_num_file:
            violations_num_file.write("%s"%n_violations)

    def run(self):
        failed = False
        errors = []
        warnings = []
        paths_to_check = [self.gds_input_file_path, self.output_directory, self.drc_script_path]
        paths_check_failed, paths_check_errors, paths_check_warnings = paths_checker(paths_to_check)
        # TODO(ahmednofal): Move to a separate dependency check for this check
        # Usage of extend is inconsistent here because of that
        errors.extend(paths_check_errors)
        warnings.extend(paths_check_warnings)
        if paths_check_failed:
            failed = True
            return failed, errors, warnings
        klayout_cmd = ["klayout", "-b", "-r", self.drc_script_path,
                        "-rd","input=%s"%self.gds_input_file_path,
                        "-rd", "report=%s"%self.report_file_path]
        with open(self.log_file_path, 'w') as log:
            klayout_subprocess = subprocess.Popen(klayout_cmd, stderr=log, stdout=log).wait()
        paths_check_failed, paths_check_errors, paths_check_warnings = paths_checker([self.report_file_path])
        if paths_check_failed:
            failed = True
            errors.append("Klayout Failed to produce a marker XML database file")
            return failed, errors, warnings
        n_violations = self.violations_num(self.report_file_path)
        if n_violations != 0:
            errors.append(f"There are # {n_violations} {self.__surname__} DRC violations")
            failed = True
        self.write_violations_num_to_file(n_violations, self.total_file_path)
        return failed, errors, warnings


class OffgridCheck(KlayoutDRCCheck):
    def __init__(self, gds_input_path, output_directory):
        self.__ref__ = "offgrid"
        self.__surname__ = "Offgrid"
        self.drc_script_path = Path(__file__).resolve().parent / 'offgrid.lydrc'
        super().__init__(gds_input_path, output_directory)


class MetalMinimumClearAreaDensityCheck(KlayoutDRCCheck):
    def __init__(self, gds_input_path, output_directory):
        self.__ref__ = "met_min_ca_density"
        self.__surname__ = "Metal Minimum Clear Area Density"
        self.drc_script_path = Path(__file__).resolve().parent / 'met_min_ca_density.lydrc'
        super().__init__(gds_input_path, output_directory)


class FOMDensityCheck(KlayoutDRCCheck):
    def __init__(self, gds_input_path, output_directory):
        self.__ref__ = "fom_density"
        self.__surname__ = "Field Oxide Mask Density"
        self.drc_script_path = Path(__file__).resolve().parent / 'fom_density.lydrc'
        super().__init__(gds_input_path, output_directory)
