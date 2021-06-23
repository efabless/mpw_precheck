#!/bin/bash

: ${1?"Usage: $0 file.gds out_file.gds cellname"}
: ${2?"Usage: $0 file.gds out_file.gds cellname"}
: ${3?"Usage: $0 file.gds out_file.gds cellname"}
: ${PDK_ROOT?"You need to export PDK_ROOT"}

echo "$1 $2 $3"

export PDK=sky130A

export MAGIC_MAGICRC

MAGTYPE=mag magic -dnull -noconsole -rcfile $MAGIC_MAGICRC <<EOF
drc off
undo disable
tech unlock *
cif istyle sky130(vendor)
gds read $1
load $3
select top cell
box -20um 0 0 3520um
flatten -nolabels -dobox xor_target
box 2920um 0 2940um 3520um
flatten -nolabels -dobox xor_target
box -20um -20um 2940um 0
flatten -nolabels -dobox xor_target
box -20um 3520um 2940um 3540um
flatten -nolabels -dobox xor_target
load xor_target
gds write $2
quit -noprompt
EOF
ls $2
