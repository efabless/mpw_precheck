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
echo $MAGTYPE
tech unlock *
gds read $1
box $2um $3um $4um $5um
erase
select area
delete
#### REVISE THIS:
select top cell
erase labels
####
gds write $6
EOF
ls $6
