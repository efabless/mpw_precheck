# Copyright 2020 Efabless Corporation
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

import re


def find_module(verilog_netlist, module_name):
    try:
        verilogOpener = open(verilog_netlist)
        if verilogOpener.mode == 'r':
            verilogContent = verilogOpener.read()
        verilogOpener.close()
        pattern = re.compile(r'module\s*\b%s\b\s*\(' % module_name)
        if len(re.findall(pattern, verilogContent)):
            return True, 'instance '+module_name+ ' found'
        else:
            return False, 'instance '+module_name+ ' not found'
    except OSError:
        return False, 'Verilog file '+verilog_netlist+' not found'

def confirm_complex_module(verilog_netlist,module_name,minimum_instantiations_number):
    try:
        verilogOpener = open(verilog_netlist)
        if verilogOpener.mode == 'r':
            verilogContent = verilogOpener.read()
        verilogOpener.close()
        pattern = re.compile(r'module\s*\b%s\b\s*\(' % module_name)
        modules = re.findall(pattern, verilogContent)
        if len(modules):
            start_idx = verilogContent.find(modules[0])
            end_idx =verilogContent.find('endmodule',start_idx)
            module = verilogContent[start_idx:end_idx]
            pattern2 = re.compile(r'\s*\b\S+\s*\b\S+\s*\(')
            instances = re.findall(pattern2, module)
            if len(instances) > minimum_instantiations_number:
                return True, 'Design is complex and contains: '+str(len(instances))+' modules'
            else:
                return False, "The module "+str(module_name) +" doesn't contain the minimum number of instantiations required"
        else:
            return False, 'instance '+(module_name)+ ' not found'
    except OSError:
        return False, 'Verilog file '+verilog_netlist+' not found'


def confirm_circuit_hierarchy(verilog_netlist, toplevel, user_module):
    try:
        verilogOpener = open(verilog_netlist)
        if verilogOpener.mode == 'r':
            verilogContent = verilogOpener.read()
        verilogOpener.close()
        pattern = re.compile(r'module\s*\b%s\b\s*\(' % toplevel)
        modules = re.findall(pattern, verilogContent)
        if len(modules):
            start_idx = verilogContent.find(modules[0])
            end_idx =verilogContent.find('endmodule',start_idx)
            module = verilogContent[start_idx:end_idx]
            pattern2 = re.compile(r'\s*\b%s\s*\S+\s*\(' % user_module)
            instances = re.findall(pattern2, module)
            if len(instances) == 1:
                return True, user_module + ' is part of ' + toplevel
            else:
                return False, 'Hierarchy Check Failed'
        else:
            return False, 'instance '+ str(toplevel) +' not found'
    except OSError:
        return False, 'Verilog file '+verilog_netlist+' not found'



def extract_connections_from_inst(verilog_netlist, toplevel,user_module):
    try:
        verilogOpener = open(verilog_netlist)
        if verilogOpener.mode == 'r':
            verilogContent = verilogOpener.read()
        verilogOpener.close()
        pattern = re.compile(r'module\s*\b%s\b\s*\(' % toplevel)
        modules = re.findall(pattern, verilogContent)
        if len(modules):
            start_idx = verilogContent.find(modules[0])
            end_idx =verilogContent.find('endmodule',start_idx)
            module = verilogContent[start_idx:end_idx]
            pattern = re.compile(r'\s*\b%s\s*\S+\s*\(' % user_module)
            instances = re.findall(pattern, module)
            if len(instances) == 1:
                start_idx = module.find(instances[0])
                end_idx = module.find(');',start_idx)
                inst = module[start_idx+len(instances[0]):end_idx]
                pattern = re.compile(r'\s*\.\S+\s*\(\S+\s*\)')
                cons = re.findall(pattern, inst)
                pattern = re.compile(r'\s*\.\S+\s*\(\s*\{')
                comp_cons = re.findall(pattern, inst)
                connections_map = dict()
                for con in cons:
                    con = con.strip()[1:-1]
                    sec = con.split('(')
                    connections_map[sec[0].strip()] = sec[1].strip()
                for con in comp_cons:
                    con_name = con.split('(')[0].strip()[1:]
                    start_idx = inst.find(con)
                    end_idx = inst.find(')',start_idx)
                    con = inst[start_idx:end_idx].split('(')[1]
                    concat=con.strip()[1:-1].split(',')
                    concat = [i.strip() for i in concat]
                    for idx in range(len(concat)):
                        connections_map[str(con_name)+'['+str(idx)+']'] = concat[idx]
                return True, connections_map
            else:
                return False, 'Hierarchy Check Failed'
        else:
            return False, 'instance '+toplevel+ ' not found'
    except OSError:
        return False, 'Verilog file '+verilog_netlist+' not found'


behavioral_keywords = ['always', 'initial', 'if', 'while', 'for', 'forever', 'repeat','reg', 'case','force']
control_characters = ['#', '$', '@']

def verify_non_behavioral_netlist(verilog_netlist):
    try:
        verilogOpener = open(verilog_netlist)
        if verilogOpener.mode == 'r':
            verilogContent = verilogOpener.read().split("\n")
        verilogOpener.close()
        skipper=False
        for lineIdx in range(len(verilogContent)):
            line = verilogContent[lineIdx].split("//")[0]
            if skipper:
                if line.find("*/") != -1:
                    skipper =False
            elif line.line.find("/*") != -1:
                skipper = True
            else:
                for keyword in behavioral_keywords:
                    pattern = re.compile(r'\s*\b%s\b\s*' % keyword)
                    occ = re.findall(pattern, line)
                    if len(occ):
                        return False, 'Behavioral Verilog Syntax Found in Netlist Code: '+ str(occ[0])+' file: '+verilog_netlist+' line: '+str(lineIdx+1)
                for char in control_characters:
                    if line.find(char) != -1:
                        return False, 'Behavioral Verilog Syntax Found in Netlist Code: '+ str(char) +' file: '+verilog_netlist+' line: '+str(lineIdx+1)
                return True, 'Netlist is Structural'
    except OSError:
        return False, 'Verilog file '+verilog_netlist+' not found'

def extract_instance_name(verilog_netlist, toplevel, instance):
    try:
        verilogOpener = open(verilog_netlist)
        if verilogOpener.mode == 'r':
            verilogContent = verilogOpener.read()
        verilogOpener.close()
        pattern = re.compile(r'module\s*\b%s\b\s*\(' % toplevel)
        modules = re.findall(pattern, verilogContent)
        if len(modules):
            start_idx = verilogContent.find(modules[0])
            end_idx =verilogContent.find('endmodule',start_idx)
            module = verilogContent[start_idx:end_idx]
            pattern = re.compile(r'\s*\b%s\s*\S+\s*\(' % instance)
            instances = re.findall(pattern, module)
            if len(instances) == 1:
                instance_name = instances[0].replace('(','').strip().split()[1]
                return True, instance_name
            else:
                return False, 'Hierarchy Check Failed'
        else:
            return False, 'instance '+toplevel+ ' not found'
    except OSError:
        return False, 'Verilog file '+verilog_netlist+' not found'


def remove_backslashes(name):
    return name.replace('\\','')

def extract_cell_list(verilog_netlist, toplevel,exclude_prefix=None):
    try:
        verilogOpener = open(verilog_netlist)
        if verilogOpener.mode == 'r':
            verilogContent = verilogOpener.read()
        verilogOpener.close()
        pattern = re.compile(r'module\s*\b%s\b\s*\(' % toplevel)
        modules = re.findall(pattern, verilogContent)
        if len(modules):
            start_idx = verilogContent.find(modules[0])
            end_idx =verilogContent.find('endmodule',start_idx)
            module = verilogContent[start_idx:end_idx]
            pattern = re.compile(r'\s*\b\S+\b\s*\S+\s*\(')
            instances = re.findall(pattern, module)
            if len(instances[1:]):
                name_list = list()
                type_list = list()
                for instance in instances[1:]:
                    sinstance = instance.strip()[:-1].split()
                    if exclude_prefix is None:
                        name_list.append(remove_backslashes(sinstance[1]))
                        type_list.append(sinstance[0])
                    else:
                        if sinstance[0].startswith(exclude_prefix) == False:
                            name_list.append(remove_backslashes(sinstance[1]))
                            type_list.append(sinstance[0])
                return True, name_list, type_list
            else:
                return False, 'Hierarchy Check Failed'
        else:
            return False, 'instance '+toplevel+ ' not found'
    except OSError:
        return False, 'Verilog file '+verilog_netlist+' not found'
