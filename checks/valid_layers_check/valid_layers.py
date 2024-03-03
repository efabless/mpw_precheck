import argparse
import pya
import logging
from pathlib import Path

def parse_layer_map(layer_map_file_path):
    layer_map = set()
    with open(layer_map_file_path, 'r') as file:
        for line in file:
            parts = line.split()
            if len(parts) >= 4:  # Ensure line has enough parts to extract layer and datatype
                layer = parts[-2]
                datatype = parts[-1]
                layer_map.add((int(layer), int(datatype)))
    return layer_map

def get_layers_from_gds(gds_file_path):
    layout = pya.Layout()
    layout.read(gds_file_path)
    layers_in_gds = set()
    for layer in layout.layer_indices():
        layer_info = layout.get_info(layer)
        if layer_info is not None:
            layers_in_gds.add((layer_info.layer, layer_info.datatype))
    return layers_in_gds

def compare_layers(gds_file_path, layer_map_file_path):
    layers_in_gds = get_layers_from_gds(gds_file_path)
    layer_map = parse_layer_map(layer_map_file_path)
    
    # Find layers in GDS not in layer map
    missing_layers = layers_in_gds - layer_map
    
    if missing_layers:
        logging.error("The following layers/datatypes in the GDS are not in the layer map:")
        for layer, datatype in missing_layers:
            logging.error(f"Layer: {layer}, Datatype: {datatype}")
        return False
    else:
        logging.info("All layers in the GDS file are included in the layer map.")
        return True

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format=f"%(asctime)s | %(levelname)-7s | %(message)s", datefmt='%d-%b-%Y %H:%M:%S')
    parser = argparse.ArgumentParser(description='Runs LVS on a given design.')
    parser.add_argument('--gds_file', '-g', required=True, help='GDS file to check')
    parser.add_argument('--layer_map_file', '-l', required=True, help='PDK layer map file')
    args = parser.parse_args()
    gds_file = Path(args.gds_file)
    layer_map_file_path = Path(args.layer_map_file)
    result = compare_layers(gds_file, layer_map_file_path)

    if result:
        logging.info("PDN multiple check Passed!")
    else:
        logging.error("PDN multiple check Failed!")
