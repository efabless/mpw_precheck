#!/bin/bash

: ${1?"Usage: $0 file.gds llx lly urx ury out_file.gds"}
: ${2?"Usage: $0 file.gds llx lly urx ury out_file.gds"}
: ${3?"Usage: $0 file.gds llx lly urx ury out_file.gds"}
: ${4?"Usage: $0 file.gds llx lly urx ury out_file.gds"}
: ${5?"Usage: $0 file.gds llx lly urx ury out_file.gds"}
: ${6?"Usage: $0 file.gds llx lly urx ury out_file.gds"}
: ${PDK_ROOT?"You need to export PDK_ROOT"}

echo "$1 $2 $3 $4 $5 $6"

export PDK=sky130A

export MAGIC_MAGICRC=$PDK_ROOT/$PDK/libs.tech/magic/$PDK.magicrc

MAGTYPE=mag magic -rcfile $MAGIC_MAGICRC -dnull -noconsole  <<EOF
drc off
tech unlock *
cif istyle sky130(vendor)
gds read $1
load $7
select top cell
flatten -nolabels xor_target
load xor_target
box $2um $3um $4um $5um
erase
gds write $6
quit -noprompt
EOF
ls $6
