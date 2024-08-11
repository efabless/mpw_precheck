import argparse
import pya
import logging
from pathlib import Path

def run_illegal_cellname_check(gds_input_file_path):
    # Load the OASIS file
    layout = pya.Layout()
    #layout.read("caravel_24063bad.oas")
    layout.read(gds_input_file_path)
    # Specify the character to search for
    search_chars = ["#", "/"] # Replace with your desired character
    # Function to recursively search subcells
    def search_subcells(cell, search_char, depth=0):
        match_found = False
        for instance in cell.each_inst():
            subcell = instance.cell
            for search_char in search_chars:
                if search_char in subcell.name:
                    logging.error(f"{' ' * depth}Found '{search_char}' in subcell: {subcell.name}")
                    match_found = True
            # Recursively search in the subcells
            if not search_subcells(subcell, search_char, depth + 1):
                match_found = True
        
        return not match_found


    # Start the search from the top cell
    top_cell = layout.top_cell()
    return search_subcells(top_cell, search_chars)

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format=f"%(asctime)s | %(levelname)-7s | %(message)s", datefmt='%d-%b-%Y %H:%M:%S')
    parser = argparse.ArgumentParser(description='Runs Illegal cellname check.')
    parser.add_argument('--gds_input_file_path', '-g', required=True, help='GDS File to apply illegal cellname check on')
    args = parser.parse_args()

    gds_input_file_path = Path(args.gds_input_file_path)


    if gds_input_file_path.exists() and gds_input_file_path.suffix == ".gds":
        if run_illegal_cellname_check(gds_input_file_path):
            logging.info("Illegal cellname check passed")
        else:
            logging.error("Illegal cellname check failed")
    else:
        logging.error(f"{gds_input_file_path} is not valid")