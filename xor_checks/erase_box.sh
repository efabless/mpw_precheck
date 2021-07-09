#!/bin/bash

: ${1?"Usage: $0 file.gds out_file.gds cellname"}
: ${2?"Usage: $0 file.gds out_file.gds cellname"}
: ${3?"Usage: $0 file.gds out_file.gds cellname"}
: ${PDK_ROOT?"You need to export PDK_ROOT"}

echo "$1 $2 $3"

export PDK=sky130A

export MAGIC_MAGICRC=$PDK_ROOT/$PDK/libs.tech/magic/$PDK.magicrc

MAGTYPE=mag magic -dnull -noconsole -rcfile $MAGIC_MAGICRC <<EOF
drc off
undo disable
tech unlock *
cif istyle sky130(vendor)
gds read $1
load $3
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
*
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
gds write $2
quit -noprompt
EOF
ls $2
