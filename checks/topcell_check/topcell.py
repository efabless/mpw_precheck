import argparse
import pya
import logging
from pathlib import Path

def check_top_cells(gds_file):
    # Load the GDS file
    layout = pya.Layout()
    layout.read(gds_file)

    # Get the top cells
    top_cells = [cell for cell in layout.top_cells()]

    # Check the number of top cells
    if len(top_cells) == 0:
        print("Error: No top cell found in the GDS layout.")
        return False
    elif len(top_cells) > 1:
        print(f"Error: Multiple top cells found in the GDS layout: {[cell.name for cell in top_cells]}")
        return False
    else:
        print(f"Success: Single top cell '{top_cells[0].name}' found in the GDS layout.")
        return True

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format=f"%(asctime)s | %(levelname)-7s | %(message)s", datefmt='%d-%b-%Y %H:%M:%S')
    parser = argparse.ArgumentParser(description='Runs Illegal cellname check.')
    parser.add_argument('--gds_input_file_path', '-g', required=True, help='GDS File to apply DRC checks on')
    args = parser.parse_args()

    gds_input_file_path = Path(args.gds_input_file_path)


    if gds_input_file_path.exists() and gds_input_file_path.suffix == ".gds":
        if check_top_cells(gds_input_file_path):
            logging.info("Illegal cellname check passed")
        else:
            logging.error("Illegal cellname check failed")
    else:
        logging.error(f"{gds_input_file_path} is not valid")
