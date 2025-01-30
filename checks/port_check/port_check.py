# SPDX-FileCopyrightText: 2025 Efabless Corporation
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
import re
import subprocess
from pathlib import Path
import pprint
import xml.etree.ElementTree as ET

from checks.utils import utils

"""
Checks that the user_project cell has the same ports on the same layer at the same pin location as the golden cell.
"""

# Indicies for port_data key tuple
LEFT_INDEX = 0
BOTTOM_INDEX = 1
RIGHT_INDEX = 2
TOP_INDEX = 3
PORT_LAYER_INDEX = 4

# Indicies for text_data key tuple
X_INDEX = 0
Y_INDEX = 1
TEXT_LAYER_INDEX = 2


class PortCheckError(Exception):
    """ Generic exception class for all known port check errors.
    Error messages are handled with the logging system, so none are expected.
    """
    pass


def get_port_layers(pdk_path, log_file):
    """Return a dict of layer_number/datatype: layer_name for pin and label datatypes."""

    layer_file_path = pdk_path / f"libs.tech/klayout/tech/{pdk_path.name}.lyp"
    print(f"\nUsing the following pin and label layers from {layer_file_path}", file=log_file)

    if not layer_file_path.exists():
        logging.error(f"Layer file {layer_file_path} not found")
        raise PortCheckError

    layer_map = {}
    tree = ET.parse(layer_file_path)
    layer_properties = tree.getroot()

    for layer_property in layer_properties.findall("properties"):
        name_element = layer_property.find('name')  # Get the 'name' element
        # <name>prBoundary.boundary - 235/4</name>
        layer_name, datatype, layer_purpose  = re.split(r"[ .-]+", name_element.text)  # split on space or period or dash
        if datatype in ['pin', 'label']:  # only map pin and label purpose layers
            layer_map[layer_purpose] = layer_name

    if not layer_map:
        logging.error(f"No port layers found in {layer_file_path}")
        raise PortCheckError

    pprint.pprint(layer_map, stream=log_file)
    return layer_map


def map_text_to_port(pin_data, layer_map, log_file):
    """Assigns names to pins based on the layer map.
    Returns the port data with mapped text and the dbu units.
    """
    error_count = 0
    # Intialize port_data to the coordinates and layer of box shapes
    port_data = {}  # {(left, bottom, right, top, layer): text, ...}
    # Text data is the coordinate and layer of the text
    text_data = {}  # {(x, y, layer): text, ...}
    for line_it in pin_data.splitlines():
        if line_it.startswith("box:"):  # format: box: left,bottom right,top layer/type
            _, left, bottom, right, top, layer_type = re.split(r"[ ,]+", line_it)  # split on space and comma
            # key = (left, bottom, right, top, layer_name): value = port_name (initially empty string)
            key = (int(left), int(bottom), int(right), int(top), layer_map[layer_type])
            port_data[key] = ""  # Duplicates are ignored.

        elif line_it.startswith("text:"):  # format text: x,y layer_type text
            _, x, y, layer_type, text = re.split(r"[ ,]+", line_it)  # split on space and comma
            # key = (x, y, layer_name): value = text
            key = (int(x), int(y), layer_map[layer_type])
            if key not in text_data:
                text_data[key] = text
            elif text_data[key] != text:  # duplicate keys only allowed with matching text
                error_message = (f"Multiple text on layer {key[TEXT_LAYER_INDEX]} "
                                 f"@({int(x)*float(dbu):.3f},{int(y)*float(dbu):.3f}). {text_data[key]} != {text}")
                logging.error(error_message)
                print(error_message, file=log_file)
                error_count += 1

        elif line_it.startswith("dbu:"):  # format dbu: user_units_per_dbu
            _, dbu = re.split(" ", line_it)

    port_keys = sorted(port_data.keys())
    compare_ports = []
    for text_it in sorted(text_data.keys()):  # To avoid O(n^2), sort keys on x coordinate
        while port_keys and port_keys[0][LEFT_INDEX] <= text_it[X_INDEX]:  # for ports with left coordinate to the left of current text
            port_it = port_keys.pop(0)  # remove from port potential compare list
            if port_it[RIGHT_INDEX] >= text_it[X_INDEX]:
                # add ports with right coordinate to the right of current text to compare candidates
                compare_ports.append(port_it)

        for compare_it in compare_ports[:]:  # iterate over a copy of the list because invalid ports will be removed
            if compare_it[RIGHT_INDEX] < text_it[X_INDEX]:
                # if the right side of the port is to the left of text, the port is no longer a candidate for comparison
                compare_ports.remove(compare_it)
            elif ( compare_it[BOTTOM_INDEX] <= text_it[Y_INDEX]
                   and compare_it[TOP_INDEX] >= text_it[Y_INDEX]
                   and compare_it[PORT_LAYER_INDEX] == text_it[TEXT_LAYER_INDEX] ):
                # if the text y-coordinate is between the bottom and top of the port and the layer matches, assign the text to the port
                if port_data[compare_it] == "":
                    port_data[compare_it] = text_data[text_it]
                elif text_data[text_it] != port_data[compare_it]:  # throw an error if multiple texts don't match
                    error_message = (f"Multiple text for {text_it[TEXT_LAYER_INDEX]} pin "
                                     f"@(left={compare_it[LEFT_INDEX]*float(dbu):.3f},"
                                     f"bottom={compare_it[BOTTOM_INDEX]*float(dbu):.3f}). "
                                     f"{text_data[text_it]} != {port_data[compare_it]}")
                    logging.error(error_message)
                    print(error_message, file=log_file)
                    error_count += 1

    if error_count > 0:
        print(f"\nError extracting pin data. The previous errors came from the following klayout log.", file=log_file)
        print(pin_data, file=log_file)
        raise PortCheckError

    return port_data, dbu


def port_center(port_key, dbu):
    """ Returns the x and y coordinates of the port center in microns."""

    x = (port_key[LEFT_INDEX] + port_key[RIGHT_INDEX]) * float(dbu)
    y = (port_key[BOTTOM_INDEX] + port_key[TOP_INDEX]) * float(dbu)
    return x, y


def get_layout_ports(top_cell, layout_file_path, layer_map, log_file):
    """ Returns a dict of pin: label for the top_cell in the layout_file_path.
    Only shapes on layers in the layer_map are processed.
    Layer names are mapped from layer numbers according to the layer_map.
    """
    print(f"\nExtracting port data from {top_cell} of {layout_file_path}", file=log_file)
    parent_directory = Path(__file__).parent
    rb_layout_port_file_path = parent_directory / 'layout_ports.rb'
    rb_layout_port_cmd = ['ruby', rb_layout_port_file_path, layout_file_path, top_cell, ' '.join(layer_map.keys())]
    rb_layout_port_process = subprocess.run(rb_layout_port_cmd, capture_output=True, text=True)
    if rb_layout_port_process.returncode != 0:
        print(rb_layout_port_process.stdout, file=log_file)
        logging.error(f"Could not extract ports from {top_cell} of {layout_file_path}.")
        raise PortCheckError

    # returns port_data, dbu
    port_data, dbu = map_text_to_port(rb_layout_port_process.stdout, layer_map, log_file)

    if not port_data:
        logging.error(f"Could not extract ports from {top_cell} of {layout_file_path}.")
        raise PortCheckError

    return port_data, dbu


def report_port_mismatch(golden_port_key, expected_text, actual_text, top_cell, layout_file, dbu, log_file):
    """ Logs the port mismatch data."""

    x, y = port_center(golden_port_key, dbu)
    layer = golden_port_key[PORT_LAYER_INDEX]
    if actual_text == "missing":
        message_header = f"missing port {expected_text}"
    elif actual_text == "unlabeled":
        message_header = f"unlabeled port (expected {expected_text})"
    else:
        message_header = f"incorrect port {actual_text} (expected {expected_text})"

    logging.error(f"{message_header} on {layer} pin centered @({x:.3f},{y:.3f}) in {top_cell} of {layout_file}.")
    print(f"{x:9.3f} {y:9.3f} {layer:>9s} {expected_text:>15s} {actual_text:>15s}", file=log_file)


def compare_ports(top_cell, layout_path, golden_ports, user_ports, dbu, log_file):
    """ Returns the number of golden_ports with no match in user_ports."""

    print(f"\n=== Port mismatches ===", file=log_file)
    print(f"    X         Y       Layer       Expected         Found", file=log_file)
    print(f"--------- --------- --------- --------------- ---------------", file=log_file)
    golden_port_keys = sorted(golden_ports)
    user_port_keys = iter(sorted(user_ports))
    user_port_it = next(user_port_keys)
    port_error_count = 0
    for golden_port_it in golden_port_keys:
        try:
            while user_port_it < golden_port_it:  # extra user ports ignored
                user_port_it = next(user_port_keys)
        except StopIteration:
            user_port_it = None

        if user_port_it != golden_port_it:  # missing port in user data
            report_port_mismatch(golden_port_it, golden_ports[golden_port_it], "missing",
                                 top_cell, layout_path, dbu, log_file)
            port_error_count += 1
        elif not user_ports[user_port_it]:  # user port with no text
            report_port_mismatch(golden_port_it, golden_ports[golden_port_it], "unlabeled",
                                 top_cell, layout_path, dbu, log_file)
            port_error_count += 1
        elif user_ports[user_port_it] != golden_ports[golden_port_it]:  # port name mismatch
            report_port_mismatch(golden_port_it, golden_ports[golden_port_it], user_ports[user_port_it],
                                 top_cell, layout_path, dbu, log_file)
            port_error_count += 1

    return port_error_count


def layout_port_check(input_directory, output_directory, gds_golden_wrapper_file_path, project_config, pdk_path):
    """ Check that the user_module has the same ports at the same location on the same layer as the golden wrapper.
    Ports are defined as pins (box shapes) with an associated label.
    The pin layer and label layer may have different datatypes but the layer name must match.
    Extra user module ports are allowed and silently ignored.
    Concurrent data is silently ignored.
    Duplicate labels on the same pin are a fatal error.
    """
    logs_directory = output_directory / 'logs'

    top_cell = project_config['user_module']
    gds_ut_path = input_directory / 'gds' / f"{top_cell}.gds"
    port_log_file_path = logs_directory / 'port_check.log'

    if not gds_ut_path.exists():
        logging.error("Layout {gds_ut_path} not found")
        return False

    with open(port_log_file_path, 'w') as port_log:
        try:
            print(f"Comparing {top_cell} ports of {gds_ut_path} to {gds_golden_wrapper_file_path}", file=port_log)
            # Get port layers from klayout layer file
            port_layers = get_port_layers(pdk_path, port_log)

            golden_ports, golden_dbu = get_layout_ports(top_cell, gds_golden_wrapper_file_path, port_layers, port_log)

            user_ports, user_dbu = get_layout_ports(top_cell, gds_ut_path, port_layers, port_log)

            if golden_dbu != user_dbu:  # dbu must match
                logging.error(f"Golden dbu {golden_dbu} of {gds_golden_wrapper_file_path} "
                              f"does not match user dbu {user_dbu} from {gds_ut_path}.")
                return False

            print(f"\nGolden ports for {top_cell} of {gds_golden_wrapper_file_path}", file=port_log)
            pprint.pprint(golden_ports, stream=port_log)

            print(f"\nUser ports for {top_cell} of {gds_ut_path}", file=port_log)
            pprint.pprint(user_ports, stream=port_log)

            port_error_count = compare_ports(top_cell, gds_ut_path, golden_ports, user_ports, golden_dbu, port_log)
            print(f"\nPort check completed normally with {port_error_count} errors.", file=port_log)

        except PortCheckError:
            logging.info(f"{{{{PORT CHECK UPDATE}}}} failed to complete. For details, see {port_log_file_path}")
            return False

    logging.info(f"{{{{PORT CHECK UPDATE}}}} Total port differences: {port_error_count}. For details, see {port_log_file_path}")
    if port_error_count == 0:
        return True
    else:
        return False


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format=f"%(asctime)s | %(levelname)-7s | %(message)s", datefmt='%d-%b-%Y %H:%M:%S')
    parser = argparse.ArgumentParser(description='Runs a port check on a given layout.')
    parser.add_argument('--input_directory', '-i', required=True, help='Design Path')
    parser.add_argument('--caravel_root', '-cr', required=True, help="CARAVEL_ROOT Absolute Path to caravel.")
    parser.add_argument('--pdk_path', '-p', required=True, help="pdk path")
    parser.add_argument('--output_directory', '-o', required=False, default='.', help='Output Directory')
    args = parser.parse_args()

    output_directory = Path(args.output_directory)
    project_config = utils.get_project_config(Path(args.input_directory), Path(args.caravel_root))
    gds_golden_wrapper_file_path = f"{args.caravel_root}/gds/{project_config['golden_wrapper']}.gds"
    pdk_path = Path(args.pdk_path)

    if layout_port_check(Path(args.input_directory), output_directory, gds_golden_wrapper_file_path, project_config, pdk_path):
        logging.info("Port Check Clean")
    else:
        logging.info("Port Check Dirty")
