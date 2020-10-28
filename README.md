# google_mpw_precheck

# Prerequisites:

- python
- yaml python package

# Setup:

To setup the necessary docker file, run:
```bash
    cd dependencies
    sh build-docker.sh
```

# What Does the Script Do?

It runs a sequence of checks and aborts with the appropriate error message(s) if any of them fails.

The steps are as follows:

- LICENSE checks.
- YAML description check.
- The existence of documentation.
- The existence of a Makefile in the project root that at least has the following targets:
    - verify: Runs simulations and testbench verifications.
    - clean: Removes all simulation and verification outputs.
    - compress: compresses the project directory.
    - uncompress: decompresses the project directory.
- Fuzzy Consistency checks on the netlists (spice or verilog) and the GDS. Caravel is the benchmark.
- TBA
- Runs DRC checks on the GDS-II.
- TBA
- TBA

# Current Assumptions:
- The project is compressed, and so before running anything we should run make uncompress and then copy all .gds files to the top level (target path) to process them.
- The top module name is `caravel`.
- The user module name is `user_project_wrapper`

# How To Run:
Run the following command:

```
python3 google_mpw_prechecker.py --target_path TARGET_PATH
                         [--spice_netlist SPICE_NETLIST [SPICE_NETLIST ...]]
                         [--verilog_netlist VERILOG_NETLIST [VERILOG_NETLIST ...]]
                         [--output_directory OUTPUT_DIRECTORY]
                         [--waive_fuzzy_checks] [--skip_drc]

Runs the precheck tool by calling the various checks in order.

optional arguments:
  -h, --help            show this help message and exit
  --target_path TARGET_PATH, -t TARGET_PATH
                        Absolute Path to the Project
  --spice_netlist SPICE_NETLIST [SPICE_NETLIST ...], -s SPICE_NETLIST [SPICE_NETLIST ...]
                        Spice Netlists: toplvl.spice user_module.spice, both
                        should be in /target_path
  --verilog_netlist VERILOG_NETLIST [VERILOG_NETLIST ...], -v VERILOG_NETLIST [VERILOG_NETLIST ...]
                        Verilog Netlist: toplvl.v user_module.v , both should
                        be in /target_path
  --output_directory OUTPUT_DIRECTORY, -o OUTPUT_DIRECTORY
                        Output Directory, defaults to /target_path/checks
  --waive_fuzzy_checks, -wfs
                        Specifies whether or not to waive fuzzy consistency checks.
  --skip_drc, -sd       Specifies whether or not to skip DRC checks.
```

# To-Dos:
- Add the proper user_project_wrapper pin list once it's finalized in the caravel project.
- Add checks #4, #6, and #7.
- Test on a real/dummy caravel project output.
