
# Function:

This script runs a magic drc check on a given GDSII.

# Prerequisites:

- python

# Setup:

To setup the necessary docker file, run:
```bash
    sh build-docker.sh
```
# How to use:

The following explains how to run the script:

```
usage: gds_drc_checker.py [-h] --target_path TARGET_PATH --design_name
                          DESIGN_NAME [--output_directory OUTPUT_DIRECTORY]

  --target_path TARGET_PATH, -t TARGET_PATH
                        Design Path
  --design_name DESIGN_NAME, -d DESIGN_NAME
                        Design Name
  --output_directory OUTPUT_DIRECTORY, -o OUTPUT_DIRECTORY
                        Output Directory
```