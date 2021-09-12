# MPW Precheck

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

To pull the necessary docker from [dockerhub](https://hub.docker.com/repository/docker/efabless/mpw_precheck/tags?page=1&ordering=last_updated), run:

```bash
    docker pull efabless/mpw_precheck:latest
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

- Overwrite `verilog/gl/user_project_wrapper.v` with your synthesized netlist **make sure the netlist includes power information**. Otherwise, point to it properly in your `info.yaml`. You can alternatively use spice files for
  both `caravel` and `user_project_wrapper`. Keep on reading for this point to make more sense.

- Make sure you have the top level GDS-II under a directory called `gds/`; thus containing `gds/user_project_wrapper.gds`, this directory should be compressed and the script will use your Makefile to uncompress it.

- Please create a file `./third_party/used_external_repos.csv` and add to it all `repository name,commit hash` for any external github repository that you are using to build this project.

- Please include any useful statistics about your design, i.e. cell count, core utilization, etc. in a `.csv` file under `./signoff/<macro-name>/final_summary_report.csv`. If you're using OpenLANE then, this file should be created
  automatically in `<run path>/reports/final_summary_report.csv`.

## What Does the Script Do?

It runs a sequence of checks and aborts with the appropriate error message(s) if any of them fails.

The steps are as follows:

- **License**:
    - The root directory of the project contains at least one of the approved licenses and does not contain any of the prohibitted licenses
    - All source files contain an approved SPDX header
- **Yaml**:
    - info.yaml file contain the pre-defined fields in [caravel_user_project](https://github.com/efabless/caravel_user_project.git) for digital projects
      and [caravel_user_project_analog](https://github.com/efabless/caravel_user_project_analog.git)
- **Manifest**:
    - Caravel version used in development is the latest
- **Makefile**:
    - Makefile targets contain at least compression and uncompression for the user_project_wrapper.gds file
- **Defaults**:
    - Contents of the project are different from the default content in [caravel_user_project](https://github.com/efabless/caravel_user_project.git) for digital projects
      and [caravel_user_project_analog](https://github.com/efabless/caravel_user_project_analog.git)
    - The info.yaml must contain fields that different from the default fields
    - The user_project_wrapper.gds must be different from the default one found in [caravel_user_project](https://github.com/efabless/caravel_user_project.git) for digital projects
      and [caravel_user_project_analog](https://github.com/efabless/caravel_user_project_analog.git) for analog projects
- **Documentation**:
    - Documentation file README.md exists and does not use any non-inclusive language
- **Consistency**:
    - Port names match that of the golden wrapper in user_project_wrapper_empty.gds or user_project_wrapper_analog_empty.gds
- **XOR**:
    - No modification in the user_project_wrapper(versus default user_project_wrapper.gds in [caravel_user_project](https://github.com/efabless/caravel_user_project.git) for digital projects
      and [caravel_user_project_analog](https://github.com/efabless/caravel_user_project_analog.git) for analog projects) outside the user defined area lower left corner (0,0) and upper right corner (2920, 3520)
- **MagicDRC**:
    - The user_project_wrapper.gds does not have any DRC violations(using magic vlsi tool)
- **KlayoutFEOLDRC**:
    - The user_project_wrapper.gds does not have any DRC violations(using klayout) in the [_Front End Of Line_ layers](https://skywater-pdk.readthedocs.io/en/latest/rules/summary.html#id3)
- **KlayoutOffgrid**:
    - The user_project_wrapper.gds does not contain any shapes that have offgrid violations(rules [x.1b, x.3a, x.2, x.2c](https://skywater-pdk.readthedocs.io/en/latest/rules/periphery.html))
- **KlayoutFOMDensity**:
    - The user_project_wrapper.gds has Field Oxide Mask density between 33 and 54 percent according to the [cfom.pd.1e, cfom.pd.1d rules](https://skywater-pdk.readthedocs.io/en/latest/rules/periphery.html)
- **KlayoutMetalMinimumClearAreaDensity**:
    - The user_project_wrapper.gds has metal density (for each of the 5 metal layers) that is the lower than the maximum metal density specified by
      the [li1.pd.ld, m1.pd.ld, m2.pd.ld, m3.pd.ld, m4.pd.ld, m5.pd.ld rules](https://skywater-pdk.readthedocs.io/en/latest/rules/periphery.html)

## Current Assumptions

- The user module name is `user_project_wrapper` (or `user_analog_project_wrapper' for caravel_user_project_analog)
- Caravel is submoduled inside the user project or installed at a different path specified by CARAVEL_ROOT.

## How To Run

Mount the docker file:

```bash
export PDK_ROOT=<Absolute path to parent of sky130A. Installed PDK root.>
export INPUT_DIRECTORY=<Absolute path to the user project path>
# if caravel is submoduled under the user project, run "export CARAVEL_ROOT=$INPUT_DIRECTORY/caravel"
export CARAVEL_ROOT=<Absolute path to caravel>
sh docker-mount.sh
```

Run the following command:

```
usage: mpw_precheck.py [-h] --input_directory INPUT_DIRECTORY --caravel_root
                       CARAVEL_ROOT --pdk_root PDK_ROOT
                       [--output_directory OUTPUT_DIRECTORY] [--private]
                       [check [check ...]]

Runs the precheck tool by calling the various checks in order.

positional arguments:
  check                 Checks to be ran by the precheck (default: None)

optional arguments:
  -h, --help            show this help message and exit
  --input_directory INPUT_DIRECTORY, -i INPUT_DIRECTORY
                        INPUT_DIRECTORY Absolute Path to the project.
                        (default: None)
  --caravel_root CARAVEL_ROOT, -cr CARAVEL_ROOT
                        CARAVEL_ROOT Absolute Path to caravel. (default: None)
  --pdk_root PDK_ROOT, -p PDK_ROOT
                        PDK_ROOT, points to pdk installation path (default:
                        None)
  --output_directory OUTPUT_DIRECTORY, -o OUTPUT_DIRECTORY
                        Output Directory,
                        default=<input_directory>/precheck_results. (default:
                        None)
  --private             If provided, precheck skips [License, Defaults,
                        Documentation] checks that qualify the project to be
                        Open Source (default: False)
```

## How to Troubleshoot Issues with Precheck

See the following [document](./debug_precheck.md) for guidance on troubleshooting issues with precheck.