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

TARGET_PATH=$1
FILE_NAME=$2
GIT_URL=$3
OUT_FILE=$4
echo "Going into $TARGET_PATH"
cd $TARGET_PATH
echo "Removing $FILE_NAME"
rm -rf $FILE_NAME
echo "Fetching $FILE_NAME"
wget $GIT_URL
echo "Running sha1sum checks"
sha1sum -c $FILE_NAME > $OUT_FILE
