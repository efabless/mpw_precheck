# MPW Precheck

| :exclamation: :exclamation: :exclamation:  Important Note  :exclamation: :exclamation: :exclamation: |
| -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Although still possible, running the mpw-precheck from outside Docker is no longer supported by efabless. If you choose to run directly through python, you bare full responsibility for the generated results |

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

If you don't have the pdk installed, please refer to the [caravel](https://github.com/efabless/caravel.git) Makefile.

## Before Using

- Before you run the precheck tool, make sure you go through https://opensource.google/docs/releasing/preparing/ and cover the requirements.

- Overwrite `verilog/gl/user_project_wrapper.v` with your synthesized netlist **make sure the netlist includes power information**. Keep on reading for this point to make more sense.

- Make sure you have the top level GDS-II under a directory called `gds/`; thus containing `gds/user_project_wrapper.gds`, this directory should be compressed and the script will use your Makefile to uncompress it.

- Please create a file `./third_party/used_external_repos.csv` and add to it all `repository name,commit hash` for any external github repository that you are using to build this project.

- Please include any useful statistics about your design, i.e. cell count, core utilization, etc. in a `.csv` file under `./signoff/<macro-name>/final_summary_report.csv`. If you're using OpenLANE then, this file should be created
  automatically in `<run path>/reports/final_summary_report.csv`.

## What Does the Script Do?

It runs a sequence of checks and aborts with the appropriate error message(s) if any of them fails.

The steps are as follows:

- **License**:
  - The root directory of the project, submodules and third party libraries contain at least one approved license and does not contain any prohibitted license
  - All source files contain an approved SPDX License and Copyright Headers
- **Makefile**:
  - Makefile targets contain at least compression and uncompression for the user_project_wrapper.gds file
- **Defaults**:
  - Contents of the project are different from the default content in [caravel_user_project](https://github.com/efabless/caravel_user_project.git) for digital projects
    and [caravel_user_project_analog](https://github.com/efabless/caravel_user_project_analog.git)
  - The user_project_wrapper.gds must be different from the default one found in [caravel_user_project](https://github.com/efabless/caravel_user_project.git) for digital projects
    and [caravel_user_project_analog](https://github.com/efabless/caravel_user_project_analog.git) for analog projects
- **Documentation**:
  - Documentation file README.md exists and does not use any non-inclusive language
- **Consistency**:
  - Runs a series of checks on the user netlist (user_project_wrapper/user_analog_project_wrapper), and the top netlist (caravel/caravan) to make sure that both conform to the constraints put by the golden wrapper.
    - Both Netlists share the following checks:
      - Modeling check: check netlist is structural and doesn't contain behavioral constructs
      - Complexity check: check netlist isn't empty and contains at least eight instances
    - Remaining Top Netlist checks:
      - Sub-module hooks: check the user wrapper submodule port connections match the golden wrapper ports
      - Power check: check all submodules in the netlist are connected to power
    - Remaining User Netlist checks:
      - Ports check: check netlist port names match the golden wrapper ports
      - Layout check: check netlist matches the provided user wrapper layout in terms of the number of instances, and the instance names
- **GPIO Defines**:
  - A verilog directives check that validates the project's 'verilog/rtl/user_defines.v' netlist.
- **XOR**:
  - No modification in the user_project_wrapper(versus default user_project_wrapper.gds in [caravel_user_project](https://github.com/efabless/caravel_user_project.git) for digital projects
    and [caravel_user_project_analog](https://github.com/efabless/caravel_user_project_analog.git) for analog projects) outside the user defined area lower left corner (0,0) and upper right corner (2920, 3520)
- **MagicDRC**:
  - The user_project_wrapper.gds does not have any DRC violations(using magic vlsi tool)
- **KlayoutBEOLDRC**:
  - The user_project_wrapper.gds does not have any DRC violations(using klayout) in the [\_Back End Of Line* layers](https://skywater-pdk.readthedocs.io/en/main/rules/summary.html)
- **KlayoutFEOLDRC**:
  - The user_project_wrapper.gds does not have any DRC violations(using klayout) in the [\_Front End Of Line* layers](https://skywater-pdk.readthedocs.io/en/main/rules/summary.html)
- **KlayoutOffgrid**:
  - The user_project_wrapper.gds does not contain any shapes that have offgrid violations(rules [x.1b, x.3a, x.2, x.2c](https://skywater-pdk.readthedocs.io/en/main/rules/periphery.html))
- **KlayoutMetalMinimumClearAreaDensity**:
  - The user_project_wrapper.gds has metal density (for each of the 5 metal layers) that is the lower than the maximum metal density specified by
    the [li1.pd.ld, m1.pd.ld, m2.pd.ld, m3.pd.ld, m4.pd.ld, m5.pd.ld rules](https://skywater-pdk.readthedocs.io/en/main/rules/periphery.html)
- **LVS**:
  **LVS is disabled on the platform by default, it is only enabled when running locally**
  - Runs hierarchy check, soft check, lvs check, ERC check on the user project. For more information (click here)[./checks/be_checks/README.md]
- **OEB**:
  - Runs oeb check, to make sure that user connected all needed oeb signals. For more information (click here)[./checks/be_checks/README.md]

## Current Assumptions

- The user module name is `user_project_wrapper` (or `user_analog_project_wrapper' for caravel_user_project_analog)
- The mpw precheck is executed from inside it's docker container where a golden copy of caravel exists and is specified by an environment variable called `GOLDEN_CARAVEL`.

## LVS Configuration

- In order for LVS and OEB checks to run successfully, the user must provide an lvs configuration file, that describes the hierarchy of the design, and give necessary information for running the checks. For extra information on how to write the configuration file (click here)[./checks/be_checks/README.md]

**NOTE : If running precheck from user project Makefile, LVS can be disabled by using `DISABLE_LVS` environment variable**

## How To Run

Mount the docker file:

```bash
export PDK_PATH=<Absolute path to the desired PDK 'variant specific'.>
export INPUT_DIRECTORY=<Absolute path to the user project path>
sh docker-mount.sh
```

Run the following command:

```
usage: mpw_precheck.py [-h] --input_directory $INPUT_DIRECTORY --pdk_path $PDK_PATH [--output_directory OUTPUT_DIRECTORY] [--private] [check [check ...]]

Runs the precheck tool by calling the various checks in order.

positional arguments:

  check                 Checks to be ran by the precheck (default: None)

optional arguments:

  -h, --help               show this help message and exit

  -i, --input_directory    $INPUT_DIRECTORY
                           INPUT_DIRECTORY, absolute Path to the project. (default: None)

  -p, --pdk_path           $PDK_PATH
                           PDK_PATH, points to the installation path of the pdk 'variant specific' (default: None)

  -o, --output_directory   OUTPUT_DIRECTORY
                           OUTPUT_DIRECTORY, default=<input_directory>/precheck_results. (default:None)

  --private                If provided, precheck skips [License, Defaults, Documentation]
                           checks used to qualify the project to as an Open Source Project (default: False)
```

## How to Troubleshoot Issues with Precheck

See the following [document](./debug_precheck.md) for guidance on troubleshooting issues with precheck.
