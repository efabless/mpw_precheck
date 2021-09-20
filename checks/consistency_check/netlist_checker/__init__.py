import enum
import logging

import numpy as np


class NetlistChecks(enum.Enum):
    ports = 'Ports'.upper()
    power = 'Power'.upper()
    layout = 'Layout'.upper()
    hierarchy = 'Hierarchy'.upper()
    modeling = 'Modeling'.upper()
    complexity = 'Complexity'.upper()
    port_types = 'Port Types'.upper()
    submodule_hooks = 'Submodule Hooks'.upper()
    layout_subcell = 'Layout Subcell'.upper()


class NetlistChecker:
    def __init__(self, netlist_parser, layout_parser=None, golden_wrapper_parser=None):
        self.netlist_parser = netlist_parser
        self.layout_parser = layout_parser
        self.golden_wrapper_parser = golden_wrapper_parser

    def check(self, checks, min_instances=0, power_nets=[], ignored_instances=[], submodule=None, submodule_banned_power=[], submodule_power=[]):
        check_operations = {
            NetlistChecks.ports: (self.check_ports, None),
            NetlistChecks.power: (self.check_power_hooks, [power_nets, ignored_instances]),
            NetlistChecks.layout: (self.check_layout, [self.layout_parser, ignored_instances]),
            NetlistChecks.hierarchy: (self.check_hierarchy, [submodule]),
            NetlistChecks.modeling: (self.check_modeling, None),
            NetlistChecks.complexity: (self.check_instances_num, [min_instances]),
            NetlistChecks.port_types: (self.check_port_types, None),
            NetlistChecks.submodule_hooks: (self.check_submodule_hooks, [submodule, submodule_power, submodule_banned_power]),
            NetlistChecks.layout_subcell: (self.check_layout_subcell, [submodule, self.layout_parser])
        }

        results = []
        failed_netlist_checks = []
        for check in checks:
            fn = check_operations[check][0]  # assign actual check function
            args = check_operations[check][1]  # get arguments to be passed to check function
            result = fn() if args is None else fn(*args)
            if not result:
                failed_netlist_checks.append(check.value)
            results.append(result)

        passed = all(results)
        if passed:
            logging.info(f"{{{{NETLIST CONSISTENCY CHECK PASSED}}}} {self.netlist_parser.top_module} netlist passed "
                         f"all consistency checks.")
        else:
            logging.warning(f"{{{{NETLIST CONSISTENCY CHECK FAILED}}}} {self.netlist_parser.top_module} netlist failed "
                            f"{len(failed_netlist_checks)} consistency check(s): {failed_netlist_checks}.")
        return passed

    def check_hierarchy(self, submodule):
        found = self.netlist_parser.find_instance(module_name=submodule)
        if found:
            logging.info(f"{NetlistChecks.hierarchy.value} CHECK PASSED: Module {submodule} is instantiated in {self.netlist_parser.top_module}. ")
        else:
            logging.warning(f"{NetlistChecks.hierarchy.value} CHECK FAILED: Module {submodule} isn't instantiated in {self.netlist_parser.top_module}.")
        return found

    def check_instances_num(self, min_number):
        num_instances = self.netlist_parser.get_num_of_instances()
        if num_instances < min_number:
            logging.warning(f"{NetlistChecks.complexity.value} CHECK FAILED: Number of instances in {self.netlist_parser.top_module} is less than {min_number}.")
            return False

        logging.info(f"{NetlistChecks.complexity.value} CHECK PASSED: Netlist {self.netlist_parser.top_module} contains at least {min_number} instances ({num_instances} instances). ")
        return True

    def check_ports(self):
        golden_ports = self.golden_wrapper_parser.get_ports()
        golden_ports.sort()

        user_ports = self.netlist_parser.get_ports()
        user_ports.sort()

        if user_ports != golden_ports:
            mismatch = list(np.setdiff1d(user_ports, golden_ports)) + list(np.setdiff1d(golden_ports, user_ports))
            logging.warning(f"{NetlistChecks.ports.value} CHECK FAILED: {self.netlist_parser.top_module} ports do not match the golden wrapper ports. "
                            f"Mismatching ports are : {mismatch}")
            return False

        logging.info(f"{NetlistChecks.ports.value} CHECK PASSED: Netlist {self.netlist_parser.top_module} ports match the golden wrapper ports")
        return True

    def check_port_types(self):
        golden_ports = self.golden_wrapper_parser.get_port_types()
        user_ports = self.netlist_parser.get_port_types()

        golden_portnames = list(golden_ports.keys())

        for port in golden_portnames:
            if user_ports[port] != golden_ports[port] and golden_ports[port] != 'Inout':
                logging.warning(f"{NetlistChecks.port_types.value} CHECK FAILED: Port {port} should be declared as "
                                f"{golden_ports[port]}.")
                return False

        logging.info(f"{NetlistChecks.port_types.value} CHECK PASSED: Netlist {self.netlist_parser.top_module} "
                     f"port types match the golden wrapper port types.")
        return True

    def check_power_hooks(self, power_nets, ignored_instances):
        connected = self.netlist_parser.is_globally_connected(nets=power_nets, ignored_instances=ignored_instances)
        if connected:
            logging.info(f"{NetlistChecks.power.value} CONNECTIONS CHECK PASSED: All instances in "
                         f"{self.netlist_parser.top_module} are connected to power")
        else:
            logging.warning(f"{NetlistChecks.power.value} CONNECTIONS CHECK FAILED: Not all instances in"
                            f" {self.netlist_parser.top_module} are connected to power")
        return connected

    def check_submodule_hooks(self, module, module_power_pins, banned_power_nets):
        module_hooks = self.netlist_parser.get_hooks(module)
        golden_portnames = self.golden_wrapper_parser.get_ports()

        for port in golden_portnames:
            if port not in module_hooks.keys():
                logging.warning(f"{NetlistChecks.submodule_hooks.value} CHECK FAILED: Port {port} is not connected "
                                f"in the top level netlist: {self.netlist_parser.top_module}.")
                return False

                # Check: The power pins of the user_analog_project_wrapper instance in the top netlist aren't connected to a forbidden power domain
            if port in module_power_pins:
                if module_hooks[port] in banned_power_nets:
                    logging.warning(f"{NetlistChecks.submodule_hooks.value} CHECK FAILED: The user power port {port} is "
                                    f"connected to a management area power/ground net: {module_hooks[port]}.")
                    return False

        # Check: The power pins of the user_project_wrapper are connected to the correct power domain
        for pin in module_power_pins:
            try:
                if module_hooks[pin] != pin + '_core':
                    logging.warning(f"{NetlistChecks.submodule_hooks.value} CHECK FAILED: The user power port {pin} is "
                                    f"not connected to the correct power domain in the top level netlist. "
                                    f"It is connected to {module_hooks[pin]} but it should be connected to {pin}_core.")
                    return False
            except KeyError:
                logging.warning(f"{NetlistChecks.submodule_hooks.value} CHECK FAILED: The user power port {pin} is "
                                f"not connected to a power domain in the top level netlist.")
                return False

        logging.info(f"{NetlistChecks.submodule_hooks.value} CHECK PASSED: All module ports for {module} are correctly "
                     f"connected in the top level netlist {self.netlist_parser.top_module}.")
        return True

    def check_modeling(self):
        behavoiral = self.netlist_parser.is_behavoiral()
        if behavoiral:
            logging.warning(f"{NetlistChecks.modeling.value} CHECK FAILED: Netlist {self.netlist_parser.top_module} "
                            f"contains behavoiral code.")
        else:
            logging.info(f"{NetlistChecks.modeling.value} CHECK PASSED: Netlist {self.netlist_parser.top_module} is structural.")
        return not behavoiral

    def check_layout(self, layout_parser, ignored_cells=[]):
        layout_modules = layout_parser.get_children()
        netlist_modules = self.netlist_parser.get_modules()

        layout_modules = list(set(layout_modules) - set(ignored_cells))

        mismatch = np.setdiff1d(layout_modules, netlist_modules)
        if len(mismatch) != 0:
            logging.warning(f"{NetlistChecks.layout.value} CHECK FAILED: The GDS layout for {self.netlist_parser.top_module} "
                            f"doesn't match the provided structural netlist. Mismatching modules are: {mismatch}")
            return False

        logging.info(f"{NetlistChecks.layout.value} CHECK PASSED: The GDS layout for {self.netlist_parser.top_module} "
                     f"matches the provided structural netlist.")
        return True

    def check_layout_subcell(self, subcell, layout_parser, subcell_netlist_parser):
        layout_subcell_modules = layout_parser.get_grandchildren(subcell)
        layout_subcell_modules.sort()

        if len(layout_subcell_modules) == 0:
            logging.warning(f"{NetlistChecks.layout_subcell.value} CHECK FAILED: Cell {subcell} in "
                            f"{self.netlist_parser.top_module} doesn't contain any subcells.")
            return False

        netlist_subcell_modules = subcell_netlist_parser.get_modules()
        netlist_subcell_modules.sort()

        if layout_subcell_modules != netlist_subcell_modules:
            mismatch = list(np.setdiff1d(layout_subcell_modules, netlist_subcell_modules)) + \
                       list(np.setdiff1d(netlist_subcell_modules, layout_subcell_modules))
            logging.warning(f"{NetlistChecks.layout_subcell.value} CHECK FAILED: Cell {subcell} in "
                            f"{self.netlist_parser.top_module} layout does not match the structural netlist. "
                            f"Mismatching modules are: {mismatch}")
            return False

        logging.info(f"{NetlistChecks.layout_subcell.value} CHECK PASSED: Cell {subcell} in "
                     f"{self.netlist_parser.top_module} layout matches the {subcell} structural netlist.")
        return True
