#!/bin/bash
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

# exit when any command fails
export RUN_ROOT=$(pwd)
export IMAGE_NAME=efabless/open_mpw_precheck:latest
echo $PDK_ROOT
echo $RUN_ROOT
make skywater-pdk

# Section Begin
cnt=0
until make skywater-library; do
cnt=$((cnt+1))
if [ $cnt -eq 5 ]; then
	exit 2
fi
rm -rf $PDK_ROOT/skywater-pdk
make skywater-pdk
done
# Section End

make open_pdks
docker run -it -v $(pwd)/..:/usr/local/bin -v $PDK_ROOT:$PDK_ROOT -e PDK_ROOT=$PDK_ROOT -u $(id -u $USER):$(id -g $USER) $IMAGE_NAME bash -c "cd /usr/local/bin/dependencies; make build-pdk"
