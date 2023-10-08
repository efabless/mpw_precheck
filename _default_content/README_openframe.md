OpenFrame Project Example
=====================================

The OpenFrame Project Example is a user project designed to showcase how to use
the Caravel "OpenFrame" design, which is an alternative user project harness
chip that differs from the Caravel and Caravan designs by (1) having no integrated
SoC on chip, (2) allowing access to all GPIO controls, (3) maximizing the user
project area, and (4) minimizing the support circuitry to comprise only the
padframe, a power-on-reset circuit, and a digital ROM containing the 32-bit
project ID.  The padframe design and placement of pins matches the Caravel and
Caravan chips.  The pin types also remain the same, with power and ground pins
in the same positions, with the same power domains available.  Pins which
previously had functions connected with the CPU (flash controller interface,
SPI interface, UART) use the same GPIO pads but allocate them to
general-purpose I/O for any purpose.

One reason for choosing the Openframe harness is to implement an alternative
SoC or implement an SoC with the user project integrated into the same level
of hierarchy.  This project example demonstrates that approach, where the
VexRISC CPU from the Caravel and Caravan chips is replaced with a PicoRV32,
which is the same processor core that was used on the first Caravel design
from MPW-one.  To facilitate testing, the design maintains the same
special-purpose pins used by Caravel and Caravan, such as (critially) the
flash controller and housekeeping SPI, so that the chip after fabrication
will be fully compatible with the development board shipped by Efabless
with the chips.

The primary difference between this Openframe project example and the
original MPW-one Caravel design is that there is no user project in the
middle, since the whole thing is now the user project.  Interfaces that
existed between the SoC core and user project, such as the logic analyzer,
have no meaning in this context and are eliminated.  The Wishbone address
space to the user project is eliminated, but the design is free to add
any additional Wishbone modules at any valid memory map location.  The
GPIOs are no longer shared between the CPU and the user project.  Each
GPIO is therefore configured individually, with a separate Wishbone
interface connecting to each one for configuration and I/O.

Otherwise, this project example does not seek to provide additional
components above and beyond what was already on the Caravel harness chip,
which includes the flash controller, UART, an SPI master, two counter/timers,
housekeeping SPI, and digital locked loop (DLL).  It provides only one new
module that groups GPIO signals into a vector that can be written or read
at the same time;  that module recovers the function of simultaneous GPIO
reads and writes that was handled in Caravel and Caravan by the housekeeping
module, but was eliminated by moving GPIO configuration to individual
Wishbone interfaces.

This README file provides basic information about the project's features,
configurations, and usage.  Complete documentation can be found in the
file docs/caravel_openframe_datasheet.pdf.  The datasheet does not contain
information about architecting or hardening the design.

Table of Contents
-----------------
- Module Overview
- Designing
- Building
- Submitting
- Contributing
- License

Module Overview
---------------

The OpenFrame project example is built around the PicoRV32 CPU from YosysHQ,
specifically the version which utilizes the Wishbone interface to communicate
with various modules.  This project example includes the following IPs, listed
with their respective base addresses:

- RAM: 0x00000000
- FLASH: 0x10000000
- UART: 0x20000000
- GPIO: 0x21000000
- Counter Timer 0: 0x22000000
- Counter Timer 1: 0x23000000
- SPI Master: 0x24000000
- GPIO Vector: 0x25000000
- Flash Controller: 0x2D000000
- Debug Registers: 0x41000000

Additionally, the project includes a "housekeeping" module that is accessed
by SPI protocol for DLL configuration, chip information, and flash programming.
This IP is not accessible through the Wishbone bus in this version, but is
indirectly accessible by coupling internally to the SPI master.

Designing
---------

The main challenge of architecting an Openframe project is understanding
the GPIO pad interface, which is quite complicated.  The Caravel and
Caravan designs purposefully kept details away from the end user.  This
example presents a similar solution in which each GPIO pad is interfaced
by an independent Wishbone interface (gpio_wb.v).  Each GPIO has I/O
similar to the user project connections on Caravel and Caravan, but with
a four-signal interface that adds the input disable pin (cpu_gpio_ieb)
to the common three-pin interface with output disable (cpu_gpio_oeb),
output (cpu_gpio_out), and input (cpu_gpio_in).  The remaining configuration
options for the GPIO pad are handled through Wishbone writes.  The
Wishbone interface additionally allows the three I/O signals to be
overridden by an internal register value.

Any additions to the Wishbone bus need to be added to the Wishbone
address interpreter (intercon_wb.v).  Note that this has been done
differently for the GPIO modules so that all of the GPIO wishbone
instances (one per GPIO pin) can act as a single wishbone interface;
each instance decodes only its own address, and all GPIO instances
share the GPIO data bus and acknowledge signal.

Where on Caravel, the default configuration of each GPIO pin at power-up
is declared in a separate file, here the default configuration data is
kept as a parameter array (picosoc.v) and applied to each GPIO wishbone
instance.

The "cpu_gpio_*" pins on the GPIO wishbone interface (see above) define
a "standard function" for each GPIO pin (such as SPI master pins, UART
transmit/receive, etc.).  Since many of these GPIO do not change
configuration (are always either input or output), the input and output
disables, and sometimes the output value, are fixed constant high or
low.  For this purpose, each pad provides an individual pair of pins
"gpio_loopback_zero" and "gpio_loopback_one" that are placed next to
the pad and should be used for applying constant values to pad-related
signals.

The loopback constants can also be used to blanket disable specific
unneeded functions of the GPIO pins.  In openframe_project_wrapper.v,
they have been used to disable the obscure inputs "gpio_analog_*"
(an interface to a switched-capacitor analog bus pair) and
"gpio_holdover" (related to a sleep state that possibly cannot be
achieved given the wiring inside the padframe).

The hierarchy of the Openframe project is:

Top level:  openframe_project_wrapper.v.  This must always be the name
of the top level cell, as it is what gets integrated into the Openframe
design to create the completed chip.  The openframe_project_wrapper
module instantiates the SoC and ties off (or leaves unconnected) pins
unused by the SoC.

Second level:  picosoc.v.  This is the SoC definition.  It instantiates
all of the blocks of the SoC as Wishbone components:  The CPU
(picorv32_wb), the SPI flash controller (spimemio_wb), the UART
(simpleuart_wb), SRAM (mem_wb), and others.  It defines all of the
wiring to the I/Os.  It also defines a few modules that have not (by
design choice) been implemented as Wishbone components:  The
housekeeping module (housekeeping), the DLL (digital_locked_loop), and
the clock and reset routing and synchronization (clock_routing).

Third level:  All SoC modules.

Power domain considerations:

This design example connects the entire user project design to the
vccd1/vssd1 domain using power connection cells (with verilog,
layout, abstract, etc. views) that are treated as macros and placed
at the appropriate position in the layout to connect between the
padframe power pads and the power ring surrounding the synthesized
digital core.  In general, however, it is preferable to connect
together as many domains as possible to maximize the amount of
current delivered to the project and minimize the amount of I-R
drop from the pads to any point in the core.  The 3.3-5.0V domains
(vdda/vssa, vdda1/vssa1, vdda2/vssa2, vddio/vssio) should be kept
separate from the 1.8V domains (vccd/vssd, vccd1/vssd1, vccd2/vssd2),
but otherwise the user is encouraged to short together all the 1.8V
domains and optionally (if used) the 3.3V domains with the exception
of vddio/vssio, which is the ESD supply for the padframe and should
remain isolated.

Analog and mixed-signal designs:

Analog designs may make use of Openframe, but since there is no
Caravan-equivalent of Openframe with bare analog pads, any analog
signals in the Openframe design must connect to the GPIO pads, which
limits them to the voltage range of (vddio, vssio), and limits the
frequency to approximately 60MHz.  All GPIOs connected to analog
signals must have the input and output buffers disabled.

The two choices of connections for analog signals to a GPIO pad are
(1) the analog_io[] pins, which connect to the pad through a resistor
and are the preferred connection, having some ESD protection; and
(2) the analog_noesd_io[] pins, which connect directly to the pad and
are very ESD sensitive.  They should not be used unless the signal
in question cannot tolerate the voltage drop across the ESD protection
resistor on the analog_io[] pin.

Analog circuits that need 3.3V-5.0V compatible digital controls can
make use of the gpio_in_h digital inputs from the GPIO pins, which
are in the high voltage domain.  However, there is no equivalent
GPIO high voltage output, so any outputs in a high voltage domain
must be level-shifted to 1.8V before connecting to a gpio_out[] pin.

Caravel board compatibility:

To keep compatibility with the caravel circuit board, projects should
note which pins connect on the board to other (potentially) driving 
circuitry:  Pins gpio[1] through gpio[4] connect to the FTDI chip (used
by the housekeeping SPI on Caravel, and which can theoretically be
placed into a high-impedence state through software).  Pin gpio[38]
connects to the CMOS clock (which can be disabled to a high impedence
state with a jumper); pins gpio[39] to gpio[42] connect directly to
the SPI flash chip and can only be disconnected by desoldering the
SPI flash chip; and pin gpio[43] is connected to an LED.  Pins gpio[5]
and gpio[6] connect to switches which allow them to be connected to
the FTDI (UART function) but will normally be in a high-impedence
state.  All other GPIO pins connect only to header pins on the
development board.

Building
--------

For instructions on building (hardening) the OpenFrame Example project,
please refer to the [README](./README) containing the build notes.

This project example was built using locally installed tools and not
with docker.  Instructions are specific to my local build environment
but hopefully with enough commentary to be more generally useful.  It
should also be possible to build the project in the Efabless-recommended
docker environment.

Submitting
----------

(To be completed)

Contributing
------------

Bug fixes are always welcome.  Enhancements will be considered if they
demonstrate some useful technique that can only be achieved with the
Openframe version.  Otherwise, this project example is meant to be just
that---an example to learn from and build on for your own Openframe
project.  The best way to contribute is to create your own open source
Openframe project for a ChipIgnite shuttle run.

License
-------

The Caravel Openframe harness chip design on which this example depends
is distributed under the Apache-2.0 license.  This project example is
also distributed under the Apache-2.0 license (see the LICENSE file).
