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
box 0 9.52um 7.89um 2989.28um
flatten -nolabels -dobox xor_target
box 2992.08um 9.52um 3000um 2989.28um
flatten -nolabels -dobox xor_target
box 0 0 3000um 9.52um
flatten -nolabels -dobox xor_target
box 0um 2989.28um 3000um 3000um
flatten -nolabels -dobox xor_target
#
# load new cell and erase power straps from user_project_area
load xor_target
box values 0 9.52um 7.89um 2989.28um
erase metal5
box values 7.89um 2989.28um 2992.08um 3000um
erase metal4
box values 2992.08um 9.52um 3000um 2989.28um
erase metal5
box values 7.89um 0 2992.08um 9.52um
erase metal4
#
# write gds
#
gds write $out_file
quit -noprompt
