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

import logging
import os
import sys
from collections import OrderedDict
from pathlib import Path

from checks import defaults_check
from checks import documentation_check
from checks import makefile_check
from checks import manifest_check
from checks.consistency_check import consistency_check
from checks.drc_checks.klayout import klayout_gds_drc_check
from checks.drc_checks.magic import magic_gds_drc_check
from checks.license_check import license_check
from checks.utils import utils
from checks.xor_check import xor_check


class CheckManagerNotFound(Exception):
    pass


class CheckManager:
    def __init__(self, precheck_config, project_config):
        self.precheck_config = precheck_config
        self.project_config = project_config
        self.result = True

    def run(self):
        """
        Define the check running steps. This version does nothing and is intended to be implemented by subclasses.
        """


class Consistency(CheckManager):
    __ref__ = 'consistency'
    __surname__ = 'Consistency'

    def __init__(self, precheck_config, project_config):
        super().__init__(precheck_config, project_config)
        self.output_directory = self.precheck_config['output_directory']
        self.input_directory = self.precheck_config['input_directory']

    def run(self):
        empty_wrapper_url = f"{self.project_config['link_prefix']}/verilog/rtl/__{self.project_config['user_module']}.v"
        golden_wrapper_file_path = self.output_directory / 'outputs' / f"__{self.project_config['user_module']}.v"
        utils.download_gzip_file_from_url(empty_wrapper_url, golden_wrapper_file_path)
        defines_url = f"{self.project_config['link_prefix']}/verilog/rtl/defines.v"
        defines_file_path = self.output_directory / 'outputs/defines.v'
        utils.download_gzip_file_from_url(defines_url, defines_file_path)
        self.result = consistency_check.main(input_directory=self.input_directory,
                                             output_directory=self.output_directory,
                                             project_config=self.project_config,
                                             golden_wrapper_netlist=golden_wrapper_file_path,
                                             defines_file_path=defines_file_path)
        if self.result:
            logging.info("{{CONSISTENCY CHECK PASSED}} The user netlist and the top netlist are valid.")
        else:
            logging.warning("{{CONSISTENCY CHECK FAILED}} The user netlist and the top netlist are not valid.")
        return self.result


class Defaults(CheckManager):
    __ref__ = 'default'
    __surname__ = 'Default'

    def __init__(self, precheck_config, project_config):
        super().__init__(precheck_config, project_config)

    def run(self):
        default_readme_result = defaults_check.has_default_readme(self.precheck_config['input_directory'], self.precheck_config['default_content'])
        if default_readme_result:
            logging.info("{{README DEFAULT CHECK PASSED}} Project 'README.md' was modified and is not identical to the default 'README.md'")
        else:
            self.result = False
            logging.warning("{{README DEFAULT CHECK FAILED}} Project 'README.md' was not modified and is identical to the default 'README.md'")

        default_content_result = defaults_check.has_default_content(self.precheck_config['input_directory'], self.precheck_config['default_content'])
        if default_content_result:
            logging.info("{{CONTENT DEFAULT CHECK PASSED}} Project 'gds' was modified and is not identical to the default 'gds'")
        else:
            self.result = False
            logging.warning("{{CONTENT DEFAULT CHECK FAILED}} Project 'gds' was not modified and is identical to the default 'gds'")

        return self.result


class Documentation(CheckManager):
    __ref__ = 'documentation'
    __surname__ = 'Documentation'

    def __init__(self, precheck_config, project_config):
        super().__init__(precheck_config, project_config)

    def run(self):
        self.result = documentation_check.main(input_directory=self.precheck_config['input_directory'])
        if self.result:
            logging.info("{{DOCUMENTATION CHECK PASSED}} Project documentation is appropriate.")
        else:
            logging.warning("{{DOCUMENTATION CHECK FAILED}} Project documentation is not appropriate.")
        return self.result


class KlayoutDRC(CheckManager):
    __ref__ = None
    __surname__ = None

    def __init__(self, precheck_config, project_config):
        super().__init__(precheck_config, project_config)
        self.gds_input_file_path = self.precheck_config['input_directory'] / f"gds/{project_config['user_module']}.gds"
        self.drc_script_path = ""
        self.klayout_cmd_extra_args = []

    def run(self):
        if not self.gds_input_file_path.exists():
            self.result = False
            logging.warning(f"{{{{{self.__surname__} CHECK FAILED}}}} {self.gds_input_file_path.name}, GDS file was not found.")
            return self.result

        self.result = klayout_gds_drc_check.klayout_gds_drc_check(self.__ref__,
                                                                  self.drc_script_path,
                                                                  self.gds_input_file_path,
                                                                  self.precheck_config['output_directory'],
                                                                  self.klayout_cmd_extra_args)
        if self.result:
            logging.info(f"{{{{{self.__surname__} CHECK PASSED}}}} The GDS file, {self.gds_input_file_path.name}, has no DRC violations.")
        else:
            logging.warning(f"{{{{{self.__surname__} CHECK FAILED}}}} The GDS file, {self.gds_input_file_path.name}, has DRC violations.")
        return self.result


class KlayoutBEOL(KlayoutDRC):
    __ref__ = 'klayout_beol'
    __surname__ = 'Klayout BEOL'

    def __init__(self, precheck_config, project_config):
        super().__init__(precheck_config, project_config)
        self.drc_script_path = Path(__file__).parent.parent / "checks/tech-files/sky130A_mr.drc"
        self.klayout_cmd_extra_args = ['-rd', 'beol=true']


class KlayoutFEOL(KlayoutDRC):
    __ref__ = 'klayout_feol'
    __surname__ = 'Klayout FEOL'

    def __init__(self, precheck_config, project_config):
        super().__init__(precheck_config, project_config)
        self.drc_script_path = Path(__file__).parent.parent / "checks/tech-files/sky130A_mr.drc"
        self.klayout_cmd_extra_args = ['-rd', 'feol=true']


# TODO: discuss migration to tapeout and removal from precheck
class KlayoutFOMDensity(KlayoutDRC):
    __ref__ = 'klayout_fom_density'
    __surname__ = 'Klayout Field Oxide Mask Density'

    def __init__(self, precheck_config, project_config):
        super().__init__(precheck_config, project_config)
        self.drc_script_path = Path(__file__).parent.parent / "checks/drc_checks/klayout/fom_density.lydrc"


class KlayoutMetalMinimumClearAreaDensity(KlayoutDRC):
    __ref__ = 'klayout_met_min_ca_density'
    __surname__ = 'Klayout Metal Minimum Clear Area Density'

    def __init__(self, precheck_config, project_config):
        super().__init__(precheck_config, project_config)
        self.drc_script_path = Path(__file__).parent.parent / "checks/drc_checks/klayout/met_min_ca_density.lydrc"


class KlayoutOffgrid(KlayoutDRC):
    __ref__ = 'klayout_offgrid'
    __surname__ = 'Klayout Offgrid'

    def __init__(self, precheck_config, project_config):
        super().__init__(precheck_config, project_config)
        self.drc_script_path = Path(__file__).parent.parent / "checks/drc_checks/klayout/offgrid.lydrc"


class KlayoutPinLabelPurposesOverlappingDrawing(KlayoutDRC):
    __ref__ = 'klayout_pin_label_purposes_overlapping_drawing'
    __surname__ = 'Klayout Pin Label Purposes Overlapping Drawing'

    def __init__(self, precheck_config, project_config):
        super().__init__(precheck_config, project_config)
        self.drc_script_path = Path(__file__).parent.parent / "checks/drc_checks/klayout/pin_label_purposes_overlapping_drawing.rb.drc"
        self.klayout_cmd_extra_args = ['-rd', f'top_cell_name={self.project_config["user_module"]}']


class KlayoutZeroArea(KlayoutDRC):
    __ref__ = 'klayout_zeroarea'
    __surname__ = 'Klayout ZeroArea'

    def __init__(self, precheck_config, project_config):
        super().__init__(precheck_config, project_config)
        self.drc_script_path = Path(__file__).parent.parent / "checks/drc_checks/klayout/zeroarea.rb.drc"
        self.klayout_cmd_extra_args = ["-rd", f"""cleaned_output={self.precheck_config['output_directory'] / 'outputs' / f"{self.gds_input_file_path.stem}_no_zero_areas.gds"}"""]


class License(CheckManager):
    __ref__ = 'license'
    __surname__ = 'License'

    def __init__(self, precheck_config, project_config):
        super().__init__(precheck_config, project_config)

    def run(self):
        license_check_result = license_check.verify_license_compliance(self.precheck_config['input_directory'])
        if license_check_result:
            logging.info("{{MAIN LICENSE CHECK PASSED}} An approved LICENSE was found in project root.")
        else:
            self.result = False
            logging.warning("{{MAIN LICENSE CHECK FAILED}} A prohibited LICENSE was found in project root.")

        submodules_license_check_result = license_check.check_submodules_licenses(self.precheck_config['input_directory'])
        if submodules_license_check_result:
            logging.info("{{SUBMODULES LICENSE CHECK PASSED}} No prohibited LICENSE file(s) was found in project submodules")
        else:
            self.result = False
            logging.warning("{{SUBMODULES LICENSE CHECK FAILED}} A prohibited LICENSE file(s) was found in project submodules")

        third_party_libraries_path = self.precheck_config['input_directory'] / 'third_party'
        if third_party_libraries_path.exists():
            third_party_libs_license_check_result = license_check.check_third_party_libs_licenses(third_party_libraries_path)
            if third_party_libs_license_check_result:
                logging.info("{{THIRD PARTY LIBRARIES LICENSE CHECK PASSED}} No prohibited LICENSE file(s) was found in project 'third_party' directory")
            else:
                self.result = False
                logging.warning("{{THIRD PARTY LIBRARIES LICENSE CHECK FAILED}} A prohibited LICENSE file(s) was found in project 'third_party' directory")

        spdx_non_compliant_list = license_check.check_dir_spdx_compliance([], self.precheck_config['input_directory'], license_check_result)
        if not spdx_non_compliant_list:
            logging.info("{{SPDX COMPLIANCE CHECK PASSED}} Project is compliant with the SPDX Standard")
        else:
            paths = [str(x) for x in spdx_non_compliant_list[:15]] if spdx_non_compliant_list.__len__() >= 15 else [str(x) for x in spdx_non_compliant_list]
            logging.warning(f"{{{{SPDX COMPLIANCE CHECK FAILED}}}} Found {spdx_non_compliant_list.__len__()} non-compliant file(s) with the SPDX Standard.")
            logging.info(f"SPDX COMPLIANCE: NON-COMPLIANT FILE(S) PREVIEW: {paths}")
            try:
                if not self.precheck_config['output_directory'].exists():  # note: needed if check is used independently to create output dirs
                    os.makedirs(self.precheck_config['output_directory'])
                spdx_compliance_report_path = self.precheck_config['output_directory'] / "logs/spdx_compliance_report.log"
                with open(spdx_compliance_report_path, mode='w+') as f:
                    logging.info(f"For the full SPDX compliance report check: {spdx_compliance_report_path}")
                    [f.write(f"{str(x)}\n") for x in spdx_non_compliant_list]
            except OSError as os_error:
                logging.fatal(f"{{{{SPDX COMPLIANCE EXCEPTION}}}} Failed to create SPDX compliance report: {os_error}")
                sys.exit(253)
        return self.result


class MagicDRC(CheckManager):
    __ref__ = 'magic_drc'
    __surname__ = 'Magic DRC'

    def __init__(self, precheck_config, project_config):
        super().__init__(precheck_config, project_config)
        self.gds_input_file_path = self.precheck_config['input_directory'] / f"gds/{self.project_config['user_module']}.gds"

    def run(self):
        if not self.gds_input_file_path.exists():
            self.result = False
            logging.warning(f"{{{{MAGIC DRC CHECK FAILED}}}} The GDS file, {self.gds_input_file_path.name}, was not found.")
            return self.result

        self.result = magic_gds_drc_check.magic_gds_drc_check(self.gds_input_file_path,
                                                              self.project_config['user_module'],
                                                              self.precheck_config['pdk_root'],
                                                              self.precheck_config['output_directory'])
        if self.result:
            logging.info(f"{{{{MAGIC DRC CHECK PASSED}}}} The GDS file, {self.gds_input_file_path.name}, has no DRC violations.")
        else:
            logging.warning(f"{{{{MAGIC DRC CHECK FAILED}}}} The GDS file, {self.gds_input_file_path.name}, has DRC violations.")
        return self.result


class Makefile(CheckManager):
    __ref__ = 'makefile'
    __surname__ = 'Makefile'

    def __init__(self, precheck_config, project_config):
        super().__init__(precheck_config, project_config)

    def run(self):
        self.result = makefile_check.main(input_directory=self.precheck_config['input_directory'])
        if self.result:
            logging.info("{{MAKEFILE CHECK PASSED}} Makefile valid.")
        else:
            logging.warning("{{MAKEFILE CHECK FAILED}} Makefile file is not valid.")
        return self.result


class Manifest(CheckManager):
    __ref__ = 'manifest'
    __surname__ = 'Manifest'

    def __init__(self, precheck_config, project_config):
        super().__init__(precheck_config, project_config)

    def run(self):
        caravel_root = self.precheck_config['caravel_root']
        self.result = manifest_check.main(input_directory=caravel_root, output_directory=self.precheck_config['output_directory'], manifest_source='master')
        if self.result:
            logging.info("{{MANIFEST CHECKS PASSED}} Manifest Checks Passed. Caravel version matches.")
        else:
            logging.warning("{{MANIFEST CHECKS FAILED}} Manifest checks failed. Caravel version does not match. Please rebase your Repository to the latest Caravel master.")
        return self.result


class XOR(CheckManager):
    __ref__ = 'xor'
    __surname__ = 'XOR'

    def __init__(self, precheck_config, project_config):
        super().__init__(precheck_config, project_config)

    def run(self):
        # TODO(nofal): This should be a single file across the entire precheck
        # We should have a good reason to have it in the XORCheck, it should be
        # part of a constant variables file that defines project-wide variables
        magicrc_file_path = self.precheck_config['pdk_root'] / 'sky130A' / 'libs.tech' / 'magic' / 'sky130A.magicrc'
        empty_wrapper_url = f"{self.project_config['link_prefix']}/gds/{self.project_config['golden_wrapper']}.gds.gz"
        gds_golden_wrapper_file_path = self.precheck_config['output_directory'] / 'outputs' / f"{self.project_config['golden_wrapper']}.gds"

        utils.download_gzip_file_from_url(empty_wrapper_url, gds_golden_wrapper_file_path)
        self.result = xor_check.gds_xor_check(self.precheck_config['input_directory'], self.precheck_config['output_directory'],
                                              magicrc_file_path, gds_golden_wrapper_file_path, self.project_config)
        if self.result:
            logging.info("{{XOR CHECK PASSED}} The GDS file has no XOR violations.")
        else:
            logging.warning("{{XOR CHECK FAILED}} The GDS file has non-conforming geometries.")
        return self.result


# Note: list of checks for an public (open source) project
open_source_checks = OrderedDict([
    (License.__ref__, License),
    (Manifest.__ref__, Manifest),
    (Makefile.__ref__, Makefile),
    (Defaults.__ref__, Defaults),
    (Documentation.__ref__, Documentation),
    (Consistency.__ref__, Consistency),
    (XOR.__ref__, XOR),
    (MagicDRC.__ref__, MagicDRC),
    (KlayoutFEOL.__ref__, KlayoutFEOL),
    (KlayoutBEOL.__ref__, KlayoutBEOL),
    (KlayoutOffgrid.__ref__, KlayoutOffgrid),
    (KlayoutMetalMinimumClearAreaDensity.__ref__, KlayoutMetalMinimumClearAreaDensity),
    (KlayoutPinLabelPurposesOverlappingDrawing.__ref__, KlayoutPinLabelPurposesOverlappingDrawing),
    (KlayoutZeroArea.__ref__, KlayoutZeroArea)
])

# Note: list of checks for a private project
private_checks = OrderedDict([
    (Manifest.__ref__, Manifest),
    (Makefile.__ref__, Makefile),
    (Consistency.__ref__, Consistency),
    (XOR.__ref__, XOR),
    (MagicDRC.__ref__, MagicDRC),
    (KlayoutFEOL.__ref__, KlayoutFEOL),
    (KlayoutBEOL.__ref__, KlayoutBEOL),
    (KlayoutOffgrid.__ref__, KlayoutOffgrid),
    (KlayoutMetalMinimumClearAreaDensity.__ref__, KlayoutMetalMinimumClearAreaDensity),
    (KlayoutPinLabelPurposesOverlappingDrawing.__ref__, KlayoutPinLabelPurposesOverlappingDrawing),
    (KlayoutZeroArea.__ref__, KlayoutZeroArea)
])


def get_check_manager(name, *args, **kwargs):
    check_managers = args[0]['check_managers']
    if name.lower() in check_managers.keys():
        return check_managers[name.lower()](*args, **kwargs)
    else:
        raise CheckManagerNotFound(f"The check '{name.lower()}' does not exist")
