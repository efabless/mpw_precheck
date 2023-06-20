drc off
set gds_input [lindex $argv 6]
set out_file [lindex $argv 7]
set cell_name [lindex $argv 8]
undo disable
tech unlock *
cif istyle sky130(vendor)
gds read $gds_input
load $cell_name
select top cell
#
# flatten perimeter outside of PR boundary including power rings
#
box -9.58um 0 0 2980.20um
flatten -nolabels -dobox xor_target
box 2980.20um 0 2989.90um 2980.20um
flatten -nolabels -dobox xor_target
box -9.58um -8.22um 2989.90um 0
flatten -nolabels -dobox xor_target
box -9.58um 2980.20um 2989.90um 2991.34um
flatten -nolabels -dobox xor_target
#
# load new cell and erase power straps from user_project_area
load xor_target
box values -9.58um 0 0 2980.20um
erase metal5
box values 0 2980.20um 2980.20um 2991.34um
erase metal4
box values 2980.20um 0 2989.90um 2980.20um
erase metal5
box values 0 -8.22um 2980.20um 0
erase metal4
#
# write gds
#
gds write $out_file
quit -noprompt
