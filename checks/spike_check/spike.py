import argparse
import logging
import subprocess
from pathlib import Path

def run_spike_check(gds_input_file_path, output_directory, script_path):
    report_file_path = output_directory / 'outputs/reports' / f'spike_check.xml'
    logs_directory = output_directory / 'logs'
    run_spike_cmd = ['bash', script_path, '-V','-m', report_file_path, gds_input_file_path]
    log_file_path = logs_directory / f'spike_check.log'
    cmd = ' '.join(str(x) for x in run_spike_cmd) + ' >& ' + str(log_file_path)
    with open(log_file_path, 'w') as spike_log:
        logging.info(f"run: {cmd}") # helpful reference, print long-cmd once & messages below remain concise
        p = subprocess.run(run_spike_cmd, stderr=spike_log, stdout=spike_log)
        # Check exit-status of all subprocesses
        stat = p.returncode
        if stat != 0:
            logging.error(f"ERROR Spike check FAILED, stat={stat}, see {log_file_path}")
            return False
        else:
            logging.info("No Spikes found")
            return True

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format=f"%(asctime)s | %(levelname)-7s | %(message)s", datefmt='%d-%b-%Y %H:%M:%S')
    parser = argparse.ArgumentParser(description='Runs Spike Check.')
    parser.add_argument('--gds_input_file_path', '-g', required=True, help='GDS File to apply spike check on')
    parser.add_argument('--output_directory', '-o', required=True, help='Output Directory')
    parser.add_argument('--script_path', '-s', required=True, help='path to gdsArea0 script')
    args = parser.parse_args()

    gds_input_file_path = Path(args.gds_input_file_path)
    output_directory = Path(args.output_directory)
    script_path = Path(args.script_path)


    if gds_input_file_path.exists() and gds_input_file_path.suffix == ".gds":
        if output_directory.exists() and output_directory.is_dir():
            if run_spike_check(gds_input_file_path, output_directory, script_path):
                logging.info("Spike check passed")
            else:
                logging.error("Spike check failed")
        else:
            logging.error(f"{output_directory} is not valid")
    else:
        logging.error(f"{gds_input_file_path} is not valid")