import argparse
import pya
import logging
from pathlib import Path

def run_metal_check(gds_file_path):
    layout = pya.Layout()
    layout.read(gds_file_path)
    for layer in layout.layer_indices():
        layer_info = layout.get_info(layer)
        if layer_info is not None:
            if f"{layer_info.layer}/{layer_info.datatype}" in "71/44" or f"{layer_info.layer}/{layer_info.datatype}" in "72/20":
                return False
            
    return True

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format=f"%(asctime)s | %(levelname)-7s | %(message)s", datefmt='%d-%b-%Y %H:%M:%S')
    parser = argparse.ArgumentParser(description='check if metal5 in design.')
    parser.add_argument('--gds_file', '-g', required=True, help='GDS file to check')
    args = parser.parse_args()
    gds_file = Path(args.gds_file)
    result = run_metal_check(gds_file)

    if result:
        logging.info("metal layers check Passed!")
    else:
        logging.error("metal layers check Failed!")