#!/bin/bash
python3 mpw_precheck.py --input_directory $INPUT_DIRECTORY --pdk_root $PDK_ROOT $@
if [str(x.name) for x in gds_path.glob('user_analog_project_wrapper*')]: