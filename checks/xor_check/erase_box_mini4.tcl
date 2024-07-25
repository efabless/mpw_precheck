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
box -50um -50um 0 1650um
flatten -nolabels -dobox xor_target
box 1300um -50um 1350um 1650um
flatten -nolabels -dobox xor_target
box -50um -50um 1350um 0
flatten -nolabels -dobox xor_target
box -50um 1600um 1350um 1650um
flatten -nolabels -dobox xor_target
box 0um 0um 1300um 1600um
flatten -nolabels -dobox -dotoplabels -nosubcircuits xor_target
#
# load new cell and erase power straps from user_project_area
load xor_target
#
# Remove all layers except for metal4 inside the PR boundary
#
#box 0 0 1300um 1600um
#erase metal4
#
# write gds
#
gds write $out_file
quit -noprompt
