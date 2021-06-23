#!/bin/bash

: ${1?"Usage: $0 file.gds out_file.gds cellname"}
: ${2?"Usage: $0 file.gds out_file.gds cellname"}
: ${3?"Usage: $0 file.gds out_file.gds cellname"}
: ${PDK_ROOT?"You need to export PDK_ROOT"}

echo "$1 $2 $3"

export PDK=sky130A

export MAGIC_MAGICRC

MAGTYPE=mag magic -rcfile $MAGIC_MAGICRC -dnull -noconsole  <<EOF
drc off
undo disable
tech unlock *
cif istyle sky130(vendor)
gds read $1
load $3
select top cell
box 0 0 20um 3520um
flatten -nolabels -dobox $3
box 2900um 0 2920um 3520um
flatten -nolabels -dobox $3
box 20 0 2900um 20um
flatten -nolabels -dobox $3
box 20 3500um 2900um 3520um
flatten -nolabels -dobox $3
load $3
gds write $2
quit -noprompt
EOF
ls $2
