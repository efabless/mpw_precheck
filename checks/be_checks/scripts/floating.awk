/^!/ {
	block = "unknown";
	if ( /Checking mos floating input/ ) {
		block = "floating";
	}
}
NF == 0 {
	if ( block == "floating" && device != "" && type != "secondary" ) {
		print type, gate, device;
	}
	device = "";
	type = "";
}
/^\// {
	full_device_path = $1;
	model = $3;
	sub(/\)\/M.*/, "", $1);
	device = $1;
	next;
}
/^*/ {
	if ( /Tri-state input/ ) {
		type = "tristate";
	} else if ( /Secondary/ ) {
		type = "secondary";
	} else if ( /leak/ ) {
		type = "no-leak";
	} else {
		type = "unknown";
	}
}
/^[GSDB]:/ {
	terminal = $1;
	switch (terminal) {
		case "G:": gate = $2;
		case "S:": source = $2;
		case "D:": drain = $2;
		case "B:": bulk = $2;
	}
	getline;
	min = $2;
	getline;
	sim = $2;
	getline;
	max = $2;
	if ( terminal == "G:" && gate == min && gate == sim && gate == max && type == "" ) {
		type = "open";
	}
	next;
}
