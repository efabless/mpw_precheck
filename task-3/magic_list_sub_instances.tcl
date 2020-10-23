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

gds read $::env(TARGET_DIR)/$::env(DESIGN_NAME).gds

set oscale [cif scale out]
set cell_name $::env(DESIGN_NAME)
magic::suspendall
puts stdout "\[INFO\]: Loading $cell_name\n"
flush stdout
load $cell_name
select top cell
select cell $::env(SUB_DESIGN_NAME)
drc off

set fout [open $::env(OUT_DIR)/$::env(SUB_DESIGN_NAME).magic.celllist w]

set outlist [cellname list children]

puts $fout $outlist
close $fout
puts stdout "\[INFO\]: Saved"


exit 0
