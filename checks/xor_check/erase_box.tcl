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
box -42.88um 0 0 3520um
flatten -nolabels -dobox xor_target
box 2920um 0 2962.5um 3520um
flatten -nolabels -dobox xor_target
box -42.88um -37.53um 2962.5um 0
flatten -nolabels -dobox xor_target
box -42.88um 3520um 2962.5um 3557.21um
flatten -nolabels -dobox xor_target
#
# load new cell and erase power straps from user_project_area
load xor_target
box values -42.88um 0 0 3520um
erase metal5
box values 0 3520um 2920um 3557.21um
erase metal4
box values 2920um 0 2962.5um 3520um
erase metal5
box values 0 -37.53um 2920um 0
erase metal4
#
# write gds
#
gds write $out_file
quit -noprompt
