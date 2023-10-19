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
box 0 0 3166.63um -2um
flatten -nolabels -dobox xor_target
box 3166.63um 0 3168.63um 4766.63um
flatten -nolabels -dobox xor_target
box 3166.63um 4766.63um 0 4768.63um
flatten -nolabels -dobox xor_target
box 0 4766.63um -2um 0
flatten -nolabels -dobox xor_target
#
# load new cell and erase power straps from user_project_area
load xor_target
select top cell
erase metal5
erase metal4
erase metal5
erase metal4
#
# write gds
#
gds write $out_file
quit -noprompt
