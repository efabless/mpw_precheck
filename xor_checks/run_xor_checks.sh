# SPDX-FileCopyrightText: 2020 Efabless Corporation
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
# SPDX-License-Identifier: Apache-2.0

TARGET_PATH=$1
USER_GDS=$2
GOLDEN_GDS=$3
FILE_URL=$4/$GOLDEN_GDS.gz
DESIGN_NAME=$5
OUT_DIR=$6
export PDK_ROOT=$7
export SCRIPTS_ROOT=${8:-$(pwd)}

set -e

if ! [[ -d "$OUT_DIR" ]]
then
    mkdir -p "$OUT_DIR"
fi

{ if ! ${SCRIPTS_ROOT}/gdsSize.rb ${TARGET_PATH}/${USER_GDS} ${DESIGN_NAME} &> /dev/null ; then
  echo "{{ ERROR }} top cell name ${DESIGN_NAME} not found."
  exit 99
fi } &> $OUT_DIR/xor.log

wget --header='Accept-Encoding: gzip' $FILE_URL
mv $GOLDEN_GDS.gz $OUT_DIR/$GOLDEN_GDS.gz
rm -rf $OUT_DIR/$GOLDEN_GDS
gzip -d $OUT_DIR/$GOLDEN_GDS.gz
# first erase the user's user_project_wrapper.gds 
sh $SCRIPTS_ROOT/erase_box.sh $TARGET_PATH/$USER_GDS 0 0 2920 3520 $OUT_DIR/${USER_GDS%.*}_erased.gds $5 > $OUT_DIR/erase_box_$USER_GDS.log
# do the same for the empty wrapper
sh $SCRIPTS_ROOT/erase_box.sh $OUT_DIR/$GOLDEN_GDS 0 0 2920 3520 $OUT_DIR/${GOLDEN_GDS%.*}_erased.gds $5 > $OUT_DIR/erase_box_$GOLDEN_GDS.log
# XOR the two resulting layouts
sh $SCRIPTS_ROOT/xor.sh \
    $OUT_DIR/${GOLDEN_GDS%.*}_erased.gds $OUT_DIR/${USER_GDS%.*}_erased.gds \
    xor_target $OUT_DIR/$DESIGN_NAME.xor.xml
sh $SCRIPTS_ROOT/xor.sh \
    $OUT_DIR/${GOLDEN_GDS%.*}_erased.gds $OUT_DIR/${USER_GDS%.*}_erased.gds \
    xor_target $OUT_DIR/$DESIGN_NAME.xor.gds > $OUT_DIR/xor.log

python $SCRIPTS_ROOT/parse_klayout_xor_log.py \
    -l "$OUT_DIR/xor.log" \
    -o "$OUT_DIR/xor_total.txt"

# screenshot the result for convenience
sh $SCRIPTS_ROOT/scrotLayout.sh \
    $PDK_ROOT/sky130A/libs.tech/klayout/sky130A.lyt \
    $OUT_DIR/$DESIGN_NAME.xor.gds

cat $OUT_DIR/xor_total.txt
