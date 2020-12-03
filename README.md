# open_mpw_precheck

## Prerequisites:

- Docker

## Setup:

To setup the necessary docker file, run:
```bash
    cd dependencies
    sh build-docker.sh
```

## Before Using:

- Before you run the precheck tool, make sure you go through https://opensource.google/docs/releasing/preparing/ and cover the requirements.

- Make sure you have the top level GDS-II under a directory called `gds/`; thus containing `gds/caravel.gds`, this directory should be compressed and the script will use your Makefile to uncompress it.

- Make sure you have the top level mag under a directory called `mag/`; thus containing `mag/caravel.mag`. This should be auto-generated with caravel's `make ship`.

- Please create a file `./third_party/used_external_repos.csv` and add to it all `repository name,commit hash` for any external github repository that you are using to build this project.

- Please include any useful statistics about your design, i.e. cell count, core utilization, etc. in a `.csv` file. If you're using OpenLANE then, this file should be created automatically in `<run path>/reports/final_summary_report.csv`.

## What Does the Script Do?

It runs a sequence of checks and aborts with the appropriate error message(s) if any of them fails.

The steps are as follows:

- Step #1: LICENSE checks: make sure your project is license compliant.
  - The project root has a LICENSE file (and the license is of an approved type).
  - All third_party material should be under a third_party directory and have a license identifier. https://opensource.google/docs/releasing/preparing/#third-party-components
  - All text files should have a copyright header (and appropriate SPDX identifier). https://opensource.google/docs/releasing/preparing/#license-headers
- Step #2: YAML description check.
  - YAML file should follow [this](https://github.com/efabless/caravel/blob/release/info.yaml) yaml file as list of requirements: all fields in the linked example are mandatory. It must be named `info.yaml` and must exist in the project root.
    - Make sure that you're pointing to gate level netlists or spice models with blackboxed macros when setting `top_level_netlist` and `user_level_netlist`.
- Step #3: Fuzzy Consistency checks
  - Step #3.1: The existence of documentation.
    - There is a README text file at the project root.
    - The README doesn't contain any non-inclusive language. Read [this](https://opensource.google/docs/releasing/preparing/#inclusive) for more.
  - Step #3.2: The existence of a Makefile in the project root that at least has the following targets:
    - verify: Runs simulations and testbench verifications.
    - clean: Removes all simulation and verification outputs.
    - compress: compresses the large items in the project directory and cleanup decompressed items.
    - uncompress: decompresses the large items in the project directory and cleanup compressed items.
  - Step #3.3: Consistency Checks on the netlists (spice or verilog) and the GDS. Caravel is the benchmark.
    - The top level module is `caravel` and there is a `user_project_wrapper` under it.
    - `caravel` and `user_project_wrapper` exist and are non-trivial.
    - You have not changed the pin list of the `user_project_wrapper`.
    - You are only using the allowed power connections with the pads.
    - The instance names and types match for `caravel` and the `user_project_wrapper` (a comparison between the netlist and the gds).
- Step #4: TBA -- not for this shuttle.
- Step #5: Runs DRC checks on the GDS-II by using `mag/caravel.mag` to abstract everthing but the user space.
- Step #6: TBA -- not for this shuttle.
- Step #7: TBA -- not for this shuttle.

## Current Assumptions:
- The top module name is `caravel`.
- The user module name is `user_project_wrapper`

## How To Run:
Mount the docker file:

You should export `TARGET_PATH=/path/to/target/path` and add this argument `-v $TARGET_PATH:$TARGET_PATH` to the `docker run` command, if the target project directory is outside the cloned open_mpw_precheck directory.

```
docker run -it -v $(pwd):/usr/local/bin \
    -u $(id -u $USER):$(id -g $USER) \
    open_mpw_prechecker:latest
```
Run the following command:

```
python3 open_mpw_prechecker.py [-h] --target_path TARGET_PATH
                                [--output_directory OUTPUT_DIRECTORY]
                                [--waive_fuzzy_checks] [--skip_drc]
                                [--drc_only]

Runs the precheck tool by calling the various checks in order.

optional arguments:
  --target_path TARGET_PATH, -t TARGET_PATH
                        Absolute Path to the project.
  --output_directory OUTPUT_DIRECTORY, -o OUTPUT_DIRECTORY
                        Output Directory, defaults to /target_path/checks
  --waive_fuzzy_checks, -wfc
                        Specifies whether or not to waive fuzzy consistency
                        checks.
  --skip_drc, -sd       Specifies whether or not to skip DRC checks.
  --drc_only, -do       Specifies whether or not to only run DRC checks.

```
