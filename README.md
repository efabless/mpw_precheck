# google_mpw_precheck

# Prerequisites:

- Docker

# Setup:

To setup the necessary docker file, run:
```bash
    cd dependencies
    sh build-docker.sh
```

# What Does the Script Do?

It runs a sequence of checks and aborts with the appropriate error message(s) if any of them fails.

The steps are as follows:

- Step #1: LICENSE checks.
- Step #2: YAML description check.
- Step #3: Fuzzy Consistency checks
  - Step #3.1: The existence of documentation.
  - Step #3.2: The existence of a Makefile in the project root that at least has the following targets:
    - verify: Runs simulations and testbench verifications.
    - clean: Removes all simulation and verification outputs.
    - compress: compresses the project directory.
    - uncompress: decompresses the project directory.
  - Step #3.3: Fuzzy Consistency checks on the netlists (spice or verilog) and the GDS. Caravel is the benchmark.
- Step #4: TBA
- Step #5: Runs DRC checks on the GDS-II.
- Step #6: TBA
- Step #7: TBA

# Current Assumptions:
- The project is compressed, and so before running anything we should run make uncompress and then copy all .gds files to the top level (target path) to process them.
- The top module name is `caravel`.
- The user module name is `user_project_wrapper`

# How To Run:
Mount the docker file:

You should export `TARGET_PATH=/path/to/target/path` and add this argument `-v $TARGET_PATH:$TARGET_PATH` to the `docker run` command, if the directory is outside the cloned google_mpw_precheck directory.

```
docker run -it -v $(pwd):/prechecker_root \
    -v $(pwd)/tech-files:/EF/SW \
    -u $(id -u $USER):$(id -g $USER) \
    google_mpw_prechecker:latest
```
Run the following command:

```
python3 google_mpw_prechecker.py [-h] --target_path TARGET_PATH
                                --top_level_netlist TOP_LEVEL_NETLIST
                                --user_level_netlist USER_LEVEL_NETLIST
                                [--output_directory OUTPUT_DIRECTORY]
                                [--waive_fuzzy_checks] [--skip_drc]

Runs the precheck tool by calling the various checks in order.

optional arguments:
  --target_path TARGET_PATH, -t TARGET_PATH
                        Absolute Path to the project.
  --top_level_netlist TOP_LEVEL_NETLIST, -tn TOP_LEVEL_NETLIST
                        Netlist: toplvl.spice or toplvl.v should be in
                        /target_path and could be spice or verilog (.spice or
                        .v) as long as it's of the same type as
                        user_level_netlist.
  --user_level_netlist USER_LEVEL_NETLIST, -un USER_LEVEL_NETLIST
                        Netlist: user_level_netlist.spice or
                        user_level_netlist.v should be in /target_path and
                        could be spice or verilog (.spice or .v) as long as
                        it's of the same type as top_level_netlist.
  --output_directory OUTPUT_DIRECTORY, -o OUTPUT_DIRECTORY
                        Output Directory, defaults to /target_path/checks
  --waive_fuzzy_checks, -wfc
                        Specifies whether or not to waive fuzzy consistency
                        checks.
  --skip_drc, -sd       Specifies whether or not to skip DRC checks.

```

# To-Dos:
- Add checks #4, #6, and #7.
- Test on a real/dummy caravel project output.
