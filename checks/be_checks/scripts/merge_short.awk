/^port/ {
	sub(/_uq[0-9]*/, "");
	ports[$2] = "";
}
/^merge/ {
	gsub(/_uq[0-9]*/, "");
        if ( last == "" ) {
		if ( $2 in ports ) {
			shorts = " " $2;
			last_port = $2;
		}
	}
	if ( last == $2 ) {
		if ( last_port != $3 && $3 in ports ) {
			shorts = shorts " " $3;
			last_port = $3;
		}
	} else {
		if ( last != "" && shorts ~ / .* / ) {
			if ( CELL != "" ) {print CELL}
			print shorts;
			CELL = "";
		}
		if ( $3 in ports ) {
			shorts = " " $3;
			last_port = $3;
		} else {
			shorts = "";
		}
	}
	last = $3;
}
END {
	if ( last != "" && shorts ~ / .* / ) {
		print shorts;
	}
}
