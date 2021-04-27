# open_mpw_precheck

## Prerequisites

- Docker

## Setup

### Docker

You can either build the docker locally or fetch it from dockerhub.
#### Build Docker Locally
To build the necessary docker locally, run:
```bash
    cd dependencies
    sh build-docker.sh
```

#### Pull Docker from Dockerhub
To pull the necessary docker from [dockerhub](https://hub.docker.com/repository/docker/efabless/open_mpw_precheck/tags?page=1&ordering=last_updated), run:
```bash
    docker pull efabless/open_mpw_precheck:latest
```

### Install the PDK
If you don't have the skywater-pdk installed, run:
```bash
    export PDK_ROOT=<absolute path to where skywater-pdk and open_pdks will reside>
    cd dependencies
    sh build-pdk.sh
```

## Before Using

- Before you run the precheck tool, make sure you go through https://opensource.google/docs/releasing/preparing/ and cover the requirements.

- Overwrite `verilog/gl/user_project_wrapper.v` with your synthesized netlist **make sure the netlist includes power information**. Otherwise, point to it properly in your `info.yaml`. You can alternatively use spice files for both `caravel` and `user_project_wrapper`. Keep on reading for this point to make more sense.

- Make sure you have the top level GDS-II under a directory called `gds/`; thus containing `gds/user_project_wrapper.gds`, this directory should be compressed and the script will use your Makefile to uncompress it.

- Please create a file `./third_party/used_external_repos.csv` and add to it all `repository name,commit hash` for any external github repository that you are using to build this project.

- Please include any useful statistics about your design, i.e. cell count, core utilization, etc. in a `.csv` file under `./signoff/<macro-name>/final_summary_report.csv`. If you're using OpenLANE then, this file should be created automatically in `<run path>/reports/final_summary_report.csv`.

## What Does the Script Do?

It runs a sequence of checks and aborts with the appropriate error message(s) if any of them fails.

The steps are as follows:

- Step #1: LICENSE checks: make sure your project is license compliant.
  - The project root has a LICENSE file (and the license is of an approved type).
  - All third_party material should be under a third_party directory and have a license identifier. https://opensource.google/docs/releasing/preparing/#third-party-components
  - All text files should have a copyright header (and appropriate SPDX identifier). https://opensource.google/docs/releasing/preparing/#license-headers
- Step #2: YAML description check.
  - YAML file should follow [this](https://github.com/efabless/caravel/blob/master/info.yaml) yaml file as list of requirements: all fields in the linked example are mandatory. It must be named `info.yaml` and must exist in the project root.
    - Make sure that you're pointing to gate level netlists or spice models with blackboxed macros when setting `top_level_netlist` and `user_level_netlist`.
- Step #3: Complaince checks
  - Step #3.1: Manifest Checks. Verify that the user is using the current caravel master.
  - Step #3.2: The existence of documentation.
    - There is a README text file at the project root.
    - The README doesn't contain any non-inclusive language. Read [this](https://opensource.google/docs/releasing/preparing/#inclusive) for more.
  - Step #3.3: The existence of a Makefile in the project root that at least has the following targets:
    - verify: Runs simulations and testbench verifications.
    - clean: Removes all simulation and verification outputs.
    - compress: compresses the large items in the project directory and cleanup decompressed items.
    - uncompress: decompresses the large items in the project directory and cleanup compressed items.
- Step #4: Optional. Check [this section](#extra-optional-checks).
- Step #5: XORs the border of your user_project_wrapper with the golden empty user_project_wrapper to make sure that when your project is integrated into caravel, the integration will go smoothly and without causing LVS/DRC issues.
- Step #6: Runs Magic DRC checks on the GDS-II by using `gds/user_project_wrapper.gds`.

## Extra Optional Checks

If you have already integrated your design into caravel, then you can enable the fuzzy consistency checks to make sure that the integration went well. Check the [How To Run](#how-to-run) section below for more details.

- Step #4: Consistency Checks on the netlists (spice or verilog) and the GDS. Caravel is the benchmark.
    - The top level module is `caravel` and there is a `user_project_wrapper` under it.
    - `caravel` and `user_project_wrapper` exist and are non-trivial.
    - You have not changed the pin list of the `user_project_wrapper`.
    - The instance names and types match for `caravel` and the `user_project_wrapper` (a comparison between the netlist and the gds).
    - You have internal power connections in the `user_project_wrapper` netlist.
    - You are only using the allowed power connections with the pads. Since the power info is not connected in caravel toplevel yet, this sub-check is expected to fail. So, don't worry about that.

- Step #7: Runs Klayout DRC checks on the GDS-II by using `gds/user_project_wrapper.gds`.

## Current Assumptions

- The user module name is `user_project_wrapper`
- Caravel is submoduled inside the user project or installed at a different path specified by CARAVEL_ROOT.

## How To Run

Mount the docker file:

```bash
export PDK_ROOT=<Absolute path to parent of sky130A. Installed PDK root.>
export TARGET_PATH=<Absolute path to the target caravel path>
sh docker-mount.sh
```

Run the following command:

```
python3 open_mpw_prechecker.py [-h] --target_path TARGET_PATH
                              --caravel_root CARAVEL_ROOT
                              [--output_directory OUTPUT_DIRECTORY] --pdk_root
                              PDK_ROOT [--manifest_source MANIFEST_SOURCE]
                              [--run_fuzzy_checks] [--skip_drc] [--drc_only]
                              [--dont_compress] [--run_klayout_drc]

Runs the precheck tool by calling the various checks in order.

optional arguments:
  -h, --help            show this help message and exit
  --target_path TARGET_PATH, -t TARGET_PATH
                        Absolute Path to the user project.
   --caravel_root CARAVEL_ROOT, -c CARAVEL_ROOT
                        Absolute Path to caravel. 
  --output_directory OUTPUT_DIRECTORY, -o OUTPUT_DIRECTORY
                        Output Directory, defaults to /target_path/checks
  --pdk_root PDK_ROOT, -p PDK_ROOT
                        PDK_ROOT, points to pdk installation path
  --manifest_source MANIFEST_SOURCE, -ms MANIFEST_SOURCE
                        The manifest files source branch: master or develop. Defaults to master
  --run_fuzzy_checks, -rfc
                        Specifies whether or not to run fuzzy consistency
                        checks. Default: False
  --skip_drc, -sd       Specifies whether or not to skip DRC checks. Default: False
  --drc_only, -do       Specifies whether or not to only run DRC checks. Default: False
  --dont_compress, -dc  If enabled, compression won't happen at the end of the
                        run. Default: False
  --run_klayout_drc, -rkd
                        Specifies whether or not to run Klayout DRC checks. Default: False
```
