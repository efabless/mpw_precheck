#!/bin/bash

# force [un]compress in caravel/Makefile's gzip ...
export GZIP="-f"

python3 open_mpw_prechecker.py -dc --pdk_root $PDK_ROOT --target_path $TARGET_PATH -c $CARAVEL_ROOT "$@"
