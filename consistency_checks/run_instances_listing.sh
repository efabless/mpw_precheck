#!/bin/bash
# Copyright 2020 Efabless Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# To call: ./run_instance_listing.sh <target_path> <design_name> <sub_design_name> <output_path>

export TARGET_DIR=$1
export DESIGN_NAME=$2
export SUB_DESIGN_NAME=$3
export OUT_DIR=$4
export SCRIPTS_ROOT=${5:-$(pwd)}

if ! [[ -d "$OUT_DIR" ]]
then
    mkdir $OUT_DIR
fi
echo "Running Magic..."
export PDKPATH=/EF/SW
export MAGIC_MAGICRC=$PDKPATH/sky130A.magicrc

docker run -it -v $MAGIC_ROOT:/magic_root -v $SCRIPTS_ROOT:$SCRIPTS_ROOT \
    -v $SCRIPTS_ROOT/../tech-files:/EF/SW -v $TARGET_DIR:$TARGET_DIR \
    -e PDKPATH=$PDKPATH -e SCRIPTS_ROOT=$SCRIPTS_ROOT \
    -e DESIGN_NAME=$DESIGN_NAME -e SUB_DESIGN_NAME=$SUB_DESIGN_NAME\
    -e TARGET_DIR=$TARGET_DIR -e OUT_DIR=$OUT_DIR \
    -u $(id -u $USER):$(id -g $USER) \
    magic:latest sh -c "magic \
        -noconsole \
        -dnull \
        -rcfile $MAGIC_MAGICRC \
        $SCRIPTS_ROOT/magic_list_instances.tcl \
        </dev/null \
        |& tee $OUT_DIR/magic_extract.log"

exit 0
