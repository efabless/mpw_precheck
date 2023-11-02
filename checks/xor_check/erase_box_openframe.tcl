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
box 0 0 3166.63um -210.685um
flatten -nolabels -dobox xor_target
box 3166.63um 0 3377.315um 4766.63um
flatten -nolabels -dobox xor_target
box 3166.63um 4766.63um 0 4977.315um
flatten -nolabels -dobox xor_target
box 0 4766.63um -210.685um 0
flatten -nolabels -dobox xor_target

#
# write gds
#
load xor_target
gds write $out_file
quit -noprompt
