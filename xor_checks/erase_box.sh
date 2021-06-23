#!/bin/bash

: ${1?"Usage: $0 file.gds llx lly urx ury out_file.gds cellname"}
: ${2?"Usage: $0 file.gds llx lly urx ury out_file.gds cellname"}
: ${3?"Usage: $0 file.gds llx lly urx ury out_file.gds cellname"}
: ${4?"Usage: $0 file.gds llx lly urx ury out_file.gds cellname"}
: ${5?"Usage: $0 file.gds llx lly urx ury out_file.gds cellname"}
: ${6?"Usage: $0 file.gds llx lly urx ury out_file.gds cellname"}
: ${7?"Usage: $0 file.gds llx lly urx ury out_file.gds cellname"}
: ${PDK_ROOT?"You need to export PDK_ROOT"}

echo "$1 $2 $3 $4 $5 $6 $7"

export PDK=sky130A

export MAGIC_MAGICRC

MAGTYPE=mag magic -rcfile $MAGIC_MAGICRC -dnull -noconsole  <<EOF
drc off
undo disable
tech unlock *
cif istyle sky130(vendor)
gds read $1
load $7
select top cell
box 0 0 20um 3520um
flatten -nolabels -dobox $7
box 2900um 0 2920um 3520um
flatten -nolabels -dobox $7
box 20 0 2900um 20um
flatten -nolabels -dobox $7
box 20 3500um 2900um 3520um
flatten -nolabels -dobox $7
load $7
gds write $6
quit -noprompt
EOF
ls $6
