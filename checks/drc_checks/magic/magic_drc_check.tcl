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


set GDS_UT_PATH [lindex $argv end-8]
set DESIGN_NAME [lindex $argv end-7]
set PDK_PATH [lindex $argv end-6]
set DRC_REPORT [lindex $argv end-5]
set DRC_MAG [lindex $argv end-4]
set SRAM_MODULES [lindex $argv end-3]
set ESD_FET [lindex $argv end-2]
set HAS_SRAM [lindex $argv end-1]
set HAS_ESD_FET [lindex $argv end]

if { $HAS_ESD_FET } {
    gds noduplicates yes
    puts "Detected an ESD FET module"
    puts "Pre-loading a maglef of: $ESD_FET"
    load $PDK_PATH/libs.ref/sky130_fd_io/maglef/$ESD_FET.mag
}

if { $HAS_SRAM } {
    gds noduplicates yes
    puts "Detected an SRAM module"
    foreach x [split $SRAM_MODULES " "] {
        puts "Pre-loading a maglef of the SRAM block: ${x}"
        load $PDK_PATH/libs.ref/sky130_sram_macros/maglef/${x}.mag
    }
}
load (UNNAMED)
gds read $GDS_UT_PATH

set fout [open $DRC_REPORT w]
set oscale [cif scale out]
set cell_name $DESIGN_NAME
magic::suspendall
puts stdout "\[INFO\]: Loading $cell_name\n"
flush stdout
load $cell_name
select top cell
expand
drc euclidean on
drc style drc(full)
drc check
set drc_result [drc listall why]


set count 0
puts $fout "$cell_name"
puts $fout "----------------------------------------"
foreach {errtype coordlist} $drc_result {
	puts $fout $errtype
	puts $fout "----------------------------------------"
	foreach coord $coordlist {
	    set bllx [expr {$oscale * [lindex $coord 0]}]
	    set blly [expr {$oscale * [lindex $coord 1]}]
	    set burx [expr {$oscale * [lindex $coord 2]}]
	    set bury [expr {$oscale * [lindex $coord 3]}]
	    set coords [format " %.3f %.3f %.3f %.3f" $bllx $blly $burx $bury]
	    puts $fout "$coords"
	    set count [expr {$count + 1} ]
	}
	puts $fout "----------------------------------------"
}

puts $fout "\[INFO\]: COUNT: $count"
puts $fout "\[INFO\]: Should be divided by 3 or 4"

puts $fout ""
close $fout

puts stdout "\[INFO\]: COUNT: $count"
puts stdout "\[INFO\]: Should be divided by 3 or 4"
puts stdout "\[INFO\]: DRC Checking DONE ($DRC_REPORT)"
flush stdout

puts stdout "\[INFO\]: Saving mag view with DRC errors($DRC_MAG)"
# WARNING: changes the name of the cell; keep as last step
save $DRC_MAG
puts stdout "\[INFO\]: Saved"

exit $count
