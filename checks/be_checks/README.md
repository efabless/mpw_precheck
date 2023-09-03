# Backend Checks

In your `caravel_user_project` or `caravel_user_project_analog` directory,
create an LVS configuration file based on [digital user project wrapper lvs configuration](https://github.com/efabless/caravel_user_project/blob/main/lvs/user_project_wrapper/lvs_config.json) or [analog user project configuration](https://github.com/efabless/caravel_user_project_analog/blob/main/lvs/user_analog_project_wrapper/lvs_config.json).
`mpw_precheck` expects this file to be in `lvs/<cellname>/lvs_config.json`.

LVS check will run these checks by default:
```
run_hier_check: Checks layout hierarchy against verilog hierarchy
run_scheck: Soft connection check
run_full_lvs: Device level LVS
run_cvc: ERC checks
```
OEB check will run these checks:
```
run_oeb_check: Check oeb connections
```

## Configuration File

The `lvs_config.json` files are a possibly hierarchical set of files to set parameters for device level LVS

Required variables:
`TOP_SOURCE` : Top source cell name.

`TOP_LAYOUT` : Top layout cell name.

`LAYOUT_FILE` : Layout gds data file. 

`LVS_SPICE_FILES` : A list of spice files.

`LVS_VERILOG_FILES` : A list of verilog files. **Note: files with child modules should be listed before parent modules.**

Optional variable lists: `*` may be used as a wild card character.

### Extraction Options

`EXTRACT_FLATGLOB` : List of cell names to flatten before extraction. 
        Cells without text tend to work better if flattened.
        Note: it is necessary to flatten all sub cells of any cells listed.

`EXTRACT_ABSTRACT` : List of cells to extract as abstract devices.
        Normally, cells that do not contain any devices will be flattened during netlisting. 
        Using this variable can prevent unwanted flattening of empty cells.
        This has no effect of cells that are flattened because of a small number of layers.
        Internal connectivity is maintained (at least at the top level).

### LVS Options
`LVS_FLATTEN` : List of cells to flatten before comparing,
        Sometimes matching topologies with mismatched pins cause errors at a higher level.
        Flattening these cells can yield a match.

`LVS_NOFLATTEN` : List of cells not to be flattened in case of a mismatch.
        Lower level errors can propagate to the top of the chip resulting in long run times.
        Specify cells here to prevent flattening. May still cause higher level problems if there are pin mismatches.

`LVS_IGNORE` : List of cells to ignore during LVS.
        Cells ignored result in LVS ending with a warning.
        Generally, should only be used when debugging and not on the final netlist.

## Checks Description

1. Check design hierarchies. A fast check for digital designs to ensure that design hierarchies match.

   Output:
   - `precheck_results/<tag>/tmp/verilog.hier`: The netlist hierarchy.
   - `precheck_results/<tag>/tmp/layout.txt.gz`: If input is gds/oas, the layout hierarchy converted to text.
   - `precheck_results/<tag>/tmp/layout.hier`: The layout hierarchy.
   - `precheck_results/<tag>/outputs/reports/hier.csv`: Comparison results.

   Algorithm:
   - Convert gds/oasis to gds text file.
   - Extract netlist hierarchy.
   - Extract layout hierarchy.
   - Compare.

2. Soft connection check: find high resistance connections (i.e. soft connections) through n/pwell.

   Output:
   - `precheck_results/<tag>/tmp/ext/*`: Extraction results with well connectivity.
   - `precheck_results/<tag>/logs/ext.log`: Well connectivity extraction log.
   - `precheck_results/<tag>/tmp/nowell.ext/*`: Extraction results without well connectivity.
   - `precheck_results/<tag>/logs/nowell.ext.log`: No well connectivity extraction log.
   - `precheck_results/<tag>/logs/soft.log`: Soft connection check LVS log.
   - `precheck_results/<tag>/outputs/reports/soft.report`: Comparison results.

   Algorithm:
   - Create 2 versions of the extracted netlist.
   - Version 1 extracts well connectivity.
     - Remove well connections and disconnected signals.
   - Version 2 does not extract well connectivity.
     - Remove disconnected signals.
   - Compare with LVS.

   Analysis:
   - Any discrepancies should be the result of well/substrate taps not connected to the correct power net.
   - Use the `precheck_results/<tag>/outputs/reports/soft.report` file to find problem nets.
   - Use the problem nets to find a connected device in the `precheck_results/<tag>/tmp/nowell.ext/<top_layout>.gds.nowell.spice` file.
   - Use the corresponding `precheck_results/<tag>/tmp/nowell.ext/*.ext` file to find the coordinates of error devices. (divide by 200 to get coordinates in um).

3. Full device level LVS

   Output:
   - `precheck_results/<tag>/tmp/ext/*`: Extraction results with well connectivity.
   - `precheck_results/<tag>/logs/ext.log`: Well connectivity extraction log.
   - `precheck_results/<tag>/logs/lvs.log`: LVS comparison log.
   - `precheck_results/<tag>/outputs/reports/lvs.report`: Comparison results.

   Hints:
   - Rerunning with --noextract is faster because previous extraction result will be used.
   - Add cells to the `EXTRACT_FLATGLOB` to flatten before extraction.
   - Cells in `EXTRACT_ABSTRACT` will be extracted (top level?), but netlisted as black-boxes.
   - `LVS_FLATTEN` is a list of cell names to be flattened during LVS.
     Flattening cells with unmatched ports may resolve proxy port errors.
   - netgen normally flattens unmatched cells which can lead to confusing results at higher levels.
     To avoid this, add cells to `LVS_NOFLATTEN`.
   - Add cells to `LVS_IGNORE` to skip LVS checks.

4. CVC-RV. Circuit Validity Check - Reliability Verification - voltage aware ERC.
   Voltage aware ERC tool to detect current leaks and electrical overstress errors.

   Output:
   - `precheck_results/<tag>/tmp/ext/<top_layout>.cdl.gz`: CDL file converted from extracted spice file.
   - `precheck_results/<tag>/tmp/cvc.error.gz`: Detailed errors results.
   - `precheck_results/<tag>/logs/cvc.log`: Log file with error summary.

   Analysis;
   - Works well with digital designs. Analog results can be obscure.
   - If the log file shows errors, look for details in the error file.
   - Error device locations can be found in the respective `precheck_results/<tag>/tmp/ext/*.ext` files. (coordinates should be divided by 200).

5. OEB check. Check for user oeb signal output to gpio cells.
   The following conditions are errors.
   - gpio with both digital (io_in/io_out) and analog (analog_io/gpio_analog) connections
   - gpio with analog (analog_io/gpio_analog) and oeb not high
   - gpio with only input (io_in) but oeb not high
   - gpio with output (io_out) but oeb never low
   The following condition is a warning.
   - gpio with both input (io_in) and output (io_out) and oeb always low

   Output:
   - `precheck_results/<tag>/tmp/ext/<top_layout>.cdl.gz`: CDL file converted from extracted spice file.
   - `precheck_results/<tag>/tmp/cvc.oeb.error.gz`: Detailed errors results.
   - `precheck_results/<tag>/logs/cvc.oeb.log`: Log file with error summary.
   - `precheck_results/<tag>/outputs/reports/cvc.oeb.report`: List of each gpio, connection counts, and errors
