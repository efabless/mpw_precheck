/^port/ {
	sub(/_uq[0-9]*/, "");
	ports[$2] = "";
}
/^merge/ {
	gsub(/_uq[0-9]*/, "");
	if ( NF > 3 ) {
		if ( shorts ~ / .* / ) {
			if ( CELL != "" ) {
				print CELL;
				CELL = "";
			}
			print shorts;
		}
		shorts = "";
		last_port = "";
		if ( $2 in ports ) {
			shorts = " " $2;
			last_port = $2;
		}
	} 
	if ( last_port != $3 && $3 in ports ) {
		shorts = shorts " " $3;
		last_port = $3;
	}
}
END {
	if ( shorts ~ / .* / ) {
		print shorts;
	}
}
