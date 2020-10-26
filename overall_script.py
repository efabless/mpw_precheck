import argparse
import base_checks.check_license as check_license
import base_checks.check_yaml as check_yaml
import consistency_checks.consistency_checker as consistency_checker
import drc_checks.gds_drc_checker as gds_drc_checker


parser = argparse.ArgumentParser(
    description='Runs the precheck tool by calling the various checks in order.')

parser.add_argument('--target_path', '-t', required=True,
                    help='Design Path')

parser.add_argument('--spice_netlist', '-s', nargs='+', default=[],
                    help='Spice Netlists: toplvl.spice user_module.spice')

parser.add_argument('--verilog_netlist', '-v', nargs='+', default=[],
                    help='Verilog Netlist: toplvl.v user_module.v')

parser.add_argument('--output_directory', '-o', required=False,
                    help='Output Directory')

args = parser.parse_args()
target_path = args.target_path
verilog_netlist = args.verilog_netlist
spice_netlist = args.spice_netlist
if args.output_directory is None:
    output_directory = str(target_path)+ '/checks'
else:
    output_directory = args.output_directory



# Step 1: Check LICENSE.
if check_license.check_main_license(target_path):
    print("APACHE-2.0 LICENSE exists in target path")
else:
    print("APACHE-2.0 LICENSE is Not Found in target path")
    exit(255)

third_party_licenses=  check_license.check_lib_license(str(target_path)+'/third-party/')

if len(third_party_licenses):
    for key in third_party_licenses:
        if third_party_licenses[key] == False:
            print("Third Party", str(key),"License Not Found")
            exit(255)
    print("Third Party Licenses Found")
else:
    print("No third party libraries found.")

# Step 2: Check YAML description.
if check_yaml.check_yaml(target_path):
    print("YAML file valid!")
else:
    print("YAML file not valid in target path")
    exit(255)

# Step 3: Check Fuzzy Consistency.
check, reason = consistency_checker.fuzzyCheck(target_path,spice_netlist,verilog_netlist,output_directory)
if check:
    print("Fuzzy Consistency Checks Passed!")
else:
    print("Fuzzy Consistency Checks Failed, Reason: ", reason)

# Step 4: Not Yet Implemented.

# Step 5: Perform DRC checks on the GDS.
# assumption that we'll always be using a caravel top module based on what's on step 3
check, reason = gds_drc_checker.gds_drc_check(target_path, 'caravel', output_directory)

if check:
    print("DRC Checks on GDS-II Passed!")
else:
    print("DRC Checks on GDS-II Failed, Reason: ", reason)

# Step 6: Not Yet Implemented.
# Step 7: Not Yet Implemented.
