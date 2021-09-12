# SPDX-FileCopyrightText: 2020 Efabless Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# SPDX-License-Identifier: Apache-2.0

import re

from PySpice.Spice import Parser
from pyverilog.vparser.parser import ParseError, parse


class NetlistParserNotFound(Exception):
    pass


class DataError(Exception):
    pass


class Port:
    """A verilog module port.
    
    Attributes:
        name: Port name. 
        type: Port type (Input, Output, Inout).
        lsb: Least significant bit of the port (None if it is a scalar port)
        msb: Most significant bit of the port (None if it is a scalar port)
    """

    def __init__(self, name, type, lsb=None, msb=None):
        self.name = name
        self.type = type
        self.lsb = lsb
        self.msb = msb

    @property
    def width(self):
        if self.lsb is not None:
            return int(self.msb) - int(self.lsb)
        else:  # Return None if it is a scalar port
            return None

    def split(self):
        """Split a vector port to scalar ports.

        Returns a list of scalar ports. Example:
        "a[3:0]" is split to [a[0], a[1], a[2], a[3]]
        """
        if self.width is None:  # if a scalar port, then just return the port name as is in a list
            port_split = [self.name]
        else:  # if not a scalar port, then split
            port_split = [f"{self.name}[{i}]" for i in range(int(self.lsb), int(self.msb) + 1)]
        return port_split


class NetlistParser:
    """Base class for netlist parsers. 

    Arguments:
        netlist: Netlist file path. 
        top_module: Top module name.

    Attributes: 
        top_module: Netlist top module name. 
        behavoiral: True if netlist contains behavoiral constructs, False otherwise. 
        instances: List of instance names.
        modules: List of module names. 
        ports: List of top module ports. 
        nodes: List of the parser abstract syntax tree nodes.
    """

    def __init__(self, netlist, top_module):
        """Create NetlistParser instance."""
        self.top_module = top_module
        self.behavoiral = False
        self.instances = []
        self.modules = []
        self.ports = []
        self.nodes = []

    def get_instances(self):
        """Get list of instance names in the top module"""
        return self.instances

    def get_modules(self):
        """Get list of module names in the top module"""
        return self.modules

    def get_ports(self):
        """Get list of ports of the top module"""
        return self.ports

    def get_instance_name(self, module_name):
        """Get instance name for the given module name"""
        try:
            indx = self.modules.index(module_name)
        except ValueError:
            return ''
        return self.instances[indx]

    def get_num_of_instances(self):
        """Get the number of instances in the top module"""
        length = len(self.instances)
        return length

    def get_hooks(self, module_name):
        """Get instance port connection for the given module name. 
        
        It returns a dictionary of the module instance connection. The 
        dictionary keys represent the port names, and the values represent 
        the port argument name. Example, for the given module instance:          
        a_module a_instance (.x(in1), .y(out1)) The returned dict is { x: in1, y: out1 }
        """
        pass

    def find_instance(self, module_name):
        """Look for an instance with the given module name. Returns True 
        if the module instance is found, False otherwise
        """
        found = module_name in self.modules
        return found

    def is_behavoiral(self):
        """Check if the parsed netlist contains behavoiral code or not."""
        return self.behavoiral

    def is_globally_connected(self, nets, ignored_instances=[]):
        """Check if any of the given nets is connected to all instances 
        minus the given ignored instances.
        
        Return True if at least one of the given nets is connected, False otherwise. 
        """
        pass


class SpiceParser(NetlistParser):
    """Spice (ngspice/xyce) netlist parser
    
    Arguments:
        netlist: Netlist file path. 
        top_module: Top module name.
    
    Attributes: 
        Parent class attributes
        subcircuits: List of subcircuit definition nodes. 
    """

    def __init__(self, netlist, top_module):
        """Create SpiParser instance."""
        super().__init__(netlist=netlist, top_module=top_module)
        # List of subcircuit definitions
        self.subcircuits = []

        try:
            parser = Parser.SpiceParser(path=netlist, end_of_line_comment=('$', '*', '//', ';'))
        except Parser.ParseError as e:
            raise DataError(f"Netlist {netlist} fails parsing because {str(e)}")

        self.subcircuits = parser.subcircuits

        found = False
        for subcircuit in self.subcircuits:
            if subcircuit.name == top_module:
                found = True
                self.ports = subcircuit.nodes
                self.nodes = subcircuit._statements
                self.instances = [instance.name for instance in subcircuit]
                self.modules = [instance._parameters[0] for instance in subcircuit]
                break

        if not found:
            raise DataError(f"Top module {top_module} not found in {netlist}.")

        # TODO: make sure that all instantiated modules have a subcircuit definition

    def find_subcircuit(self, subcircuit):
        """Look for a subcircuit definition"""
        names = [subcircuit.name for subcircuit in self.subcircuits]
        found = subcircuit in names
        return found

    def get_hooks(self, module_name):
        hooks = dict()
        subckt_instance = None
        for instance in self.nodes:
            if instance._parameters[0] == module_name:
                subckt_instance = instance
                break

        if not subckt_instance:
            raise DataError(f"Module instance {module_name} not found.")

        subckt_definition = None
        for subcircuit in self.subcircuits:
            if subcircuit.name == module_name:
                subckt_definition = subcircuit
                break

        if not subckt_definition:
            raise DataError(f"Module definition {module_name} not found.")

        ports = subckt_definition._nodes
        conn = subckt_instance._nodes

        if len(conn) < len(ports):
            print("{{Warning}}: Not all ports are connected")

        hooks = {ports[i]: conn[i] for i in range(0, len(conn))}
        hooks.update({ports[i]: None for i in range(len(conn), len(ports))})

        return hooks

    def is_globally_connected(self, nets, ignored_instances=[]):
        connected = False
        for instance in self.nodes:
            if instance._parameters[0] not in ignored_instances:
                locally_connected = [hook in nets for hook in instance._nodes]
                connected = any(locally_connected)
                if not connected:
                    print(f"Instance {instance._parameters[0]} isn't connected to any of the nets: {nets} .")
                    break

        return connected


class VerilogParser(NetlistParser):
    """Verilog HDL netlist parser
    
    Arguments:
        netlist: Netlist file path. 
        top_module: Top module name.
        include_files: List of extra .v files to include with the netlist. 
        preprocess_define: List of macro defines to pass to the preprocessor (iverilog). 
        
    Attributes: 
        Parent class attributes
    """

    def __init__(self, netlist, top_module, **kwargs):
        """Create VerilogParser instance."""
        super().__init__(netlist=netlist, top_module=top_module)
        include_files = kwargs.get('include_files', [])
        preprocess_define = kwargs.get('preprocess_define', None)
        # Pyverilog specific types for IO ports and verilog keywords 
        io_port_types = ['Inout', 'Input', 'Output']
        behavioral_keywords = [
            'Always', 'Case', 'CaseStatement', 'DelayStatement', 'EventStatement',
            'ForeverStatement', 'ForStatement', 'Function', 'FunctionCall', 'IfStatement', 'Initial',
            'Reg', 'Repeat', 'Task', 'TaskCall', 'WaitStatement', 'WhileStatement'
        ]

        netlists = include_files + [netlist]
        try:
            root_ast, _ = parse(filelist=netlists, preprocess_define=preprocess_define, debug=False)
        except ParseError as e:
            raise DataError(f"Parsing netlist {netlist} failed because {str(e)}")

        # Look for the top module definition node in the abstract syntax tree
        top_definition = None
        for definition in root_ast.description.definitions:
            def_type = type(definition).__name__
            if def_type == 'ModuleDef':
                if definition.name == top_module:
                    top_definition = definition
                    break

        if not top_definition:
            raise DataError(f"Top module {top_module} not found in {netlist}.")

        # Loop over each node under the top module definition 
        for item in top_definition.items:
            item_type = type(item).__name__
            if item_type == 'InstanceList':  # Module instances
                instance = item.instances[0]
                self.nodes.append(instance)
                self.instances.append(instance.name)
                self.modules.append(instance.module)
            elif item_type in behavioral_keywords:
                self.behavoiral = True
            elif item_type == 'Decl' and type(item.list[0]).__name__ in io_port_types:  # IO Port statements
                decl = item.list[0]
                if decl.width is not None:
                    lsb = min(decl.width.lsb.value, decl.width.msb.value)
                    msb = max(decl.width.lsb.value, decl.width.msb.value)
                else:
                    lsb = None
                    msb = None

                port = Port(name=decl.name, lsb=lsb, msb=msb, type=type(item.list[0]).__name__)
                self.ports.append(port)

        # If the port decleration is part of the header, for example: 
        # module (input clk, input rst, ...), then it won't be parsed by the previous loop
        if not self.ports:
            portlist = top_definition.portlist.ports
            for port in portlist:
                if port.first.width is not None:
                    lsb = self._evaluate_expr(port.first.width.lsb)
                    msb = self._evaluate_expr(port.first.width.msb)
                else:
                    lsb = None
                    msb = None

                port = Port(name=port.first.name, lsb=lsb, msb=msb, type=type(port.first).__name__)
                self.ports.append(port)

    def get_ports(self):
        """Get list of port names"""
        names = [element for port in self.ports for element in port.split()]
        return names

    def get_port_types(self, split_bus=True):
        """Get port types, it returns a dictionary. The
        dictionary keys are the port names, and the dictionary 
        values are the port type (Input, Output, Inout)
        """
        ports = dict()
        if split_bus:
            for port in self.ports:
                split_port = port.split()
                for element in split_port:
                    ports[element] = port.type
        else:
            for port in self.ports:
                ports[port.name] = port.type

        return ports

        # TODO: Needs to be with instance name (can have more than on instance with the same module)

    def get_hooks(self, module_name):
        hooks = dict()
        try:
            node_idx = self.modules.index(module_name)
        except ValueError:
            raise DataError(f"Module {module_name} not found.")

        node = self.nodes[node_idx]
        if node.module == module_name:
            for hook in node.portlist:
                argname_type = type(hook.argname).__name__
                if argname_type == 'Concat':
                    for i in range(0, len(hook.argname.list)):
                        portname = f"{hook.portname}[{i}]"
                        hooks[portname] = hook.argname.list[i]
                else:
                    hooks[hook.portname] = str(hook.argname)

        return hooks

    def is_globally_connected(self, nets, ignored_instances=[]):
        connected = False
        for node in self.nodes:
            if node.name not in ignored_instances:
                locally_connected = [str(hook.argname) in nets if type(hook.argname).__name__ != 'Concat'
                                     else len(set(list(hook.argname.list)) & set(nets)) > 0 for hook in node.portlist]
                connected = any(locally_connected)
                if not connected:
                    print(f"Instance {node.name} isn't connected to any of the nets: {nets} .")
                    break

        return connected

    def _evaluate_expr(self, expr):
        # TODO: Hanlde all supported pyverilog operators 
        operators = {
            'Plus': lambda a, b: a + b,
            'Minus': lambda a, b: a - b,
            'Times': lambda a, b: a * b,
            'Divide': lambda a, b: a / b,
            'Mod': lambda a, b: a % b,
            'Power': lambda a, b: a ** b,
            'Sll': lambda a, b: a >> b
        }
        expr_type = type(expr).__name__
        if expr_type in list(operators.keys()):
            left = self._evaluate_expr(expr.left)
            right = self._evaluate_expr(expr.right)
            value = operators[expr_type](left, right)
        elif expr_type == 'IntConst':
            value = expr.value
        else:
            raise DataError(f"Got an unknown expression type {expr_type} in netlist .")

        return int(value)

    @staticmethod
    def remove_cells(input_netlist, output_netlist, cells):
        def filter_out_cell(cell, content):
            regex = fr'\s+sky130_fd_sc_.*__{cell}_[\d]+\s+.*\s+\([\s\S]*?(?:\;)'
            return re.sub(regex, '', content)

        with open(input_netlist) as f:
            lines = f.read()
            for cell in cells:
                lines = filter_out_cell(cell, lines)

        if not lines:
            raise DataError(f"File {input_netlist} is empty.")

        with open(output_netlist, 'w+') as f:
            f.write(lines)


def get_netlist_parser(netlist, top_module, netlist_type, **kwargs):
    if netlist_type == 'spice':
        return SpiceParser(netlist, top_module)
    elif netlist_type == 'verilog':
        return VerilogParser(netlist, top_module, **kwargs)
    else:
        raise NetlistParserNotFound()
