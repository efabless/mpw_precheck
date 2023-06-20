### Always check the $INPUT_DIRECTORY/precheck_results folder for relevant log files

# What to do if:

#### License check failed

Include a LICENSE file in

- The root directory in your project
- each directory under `third_party`
- each git submodule (Any directory that contains a .git folder)

Make sure it is one of the [approved licenses](base_checks/_licenses/_approved_licenses)

#### SPDX Compliance failed

check the `$INPUT_DIRECTORY/checks/spdx_compliance_report.log` for the non-compliant files. Then add SPDX header in the beginning of all of those files.

#### Compliance Check failed

- Remove all non-inclusive keywords in all of your files those are

  - blacklist
  - whitelist
  - slave

- Include `verify` and `clean` targets in your makefile

#### Fuzzy consistency check failed

This indicates a serious issue with the design please check [information about fuzzy checks in README.md](README.md#fuzzy-consistency-checks)

#### XOR check failed

- Load `$INPUT_DIRECTORY/checks/<design_name>.xor.gds` into [klayout](#how-to-view-a-gds) and then you can see where exactly your design violates the boundary set for the user project

- Read xor.log and check the specific coordiantes of your violations

- Read xor_total.txt to find out how many shapes are not respecting the user space boundary

#### DRC Check failed

###### Magic DRC check

To debug drc errors you can open up the `$INPUT_DIRECTORY/checks/magic_drc.log` folder and you can view them via the .magic.drc.mag file which is loadable in magic

Also there is a listing of all the failed parts of the design in $INPUT_DIRECTORY/checks/<design_name>.magic.drc

If you are having a huge number of DRC violations there is a good chance you are using an SRAM block that is not the latest version in efabless/sram_sky130_macros . Just pull the master branch and include one of those updated macros instead

###### Klayout DRC check (DISABLED BY DEFAULT)

Load marker databases provided by the drc check into klayout (Or whichever layout editor/viewer you wish to use) along with the gds file (user_project_wrapper.gds)
and you can view the violations on top of your design layout
[using klayout](#how-to-load-marker-database-files)

Investigate the specific coordinates of the failures in the design gds. Use `$INPUT_DIRECTORY/checks/<design_name>_klayout.lydrc` file as a marker database file loadable in [klayout](#how-to-load-marker-database-files)

#### Default content check failed

Submit content other than the default content

- gds
- lef
- def
- mag
- maglef
- verilog/rtl
- verilog/gl
- spi/lvs

### Errors specific to running precheck on efabless platform:

#### exception code 254

There is a problem cloning your git repo using the provided git repo url

Common mistakes

- Using ssh as a git url
- Including private submodules that require credentials to get cloned

#### exception code 1

there is a problem with your project's name, the project's name is supposed to not have a space in it. You should create another project with a name that does not contain spaces and point your mpw-two request to the new one instead.

## Using klayout:

### How to view a gds

    klayout <gds_file>

### How to load marker database files

    klayout <gds_file> -m <marker_database_file>
