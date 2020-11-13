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


def find_subckt(spice_netlist, subckt_name):
    try:
        spiceOpener = open(spice_netlist)
        if spiceOpener.mode == 'r':
            spiceContent = spiceOpener.read()
        spiceOpener.close()
        pattern = re.compile(r'\.subckt\s*\b%s\b\s*' % subckt_name)
        if len(re.findall(pattern, spiceContent)):
            return True, 'instance '+subckt_name+ ' found'
        else:
            return False, 'instance '+subckt_name+ ' not found'
    except OSError:
        return False, 'Spice file '+str(spice_netlist)+ ' not found'

def confirm_complex_subckt(spice_netlist,subckt_name,minimum_devices_number):
    try:
        spiceOpener = open(spice_netlist)
        if spiceOpener.mode == 'r':
            spiceContent = spiceOpener.read()
        spiceOpener.close()
        pattern = re.compile(r'\.subckt\s*\b%s\b\s*' % subckt_name)
        subckts = re.findall(pattern, spiceContent)
        if len(subckts):
            start_idx = spiceContent.find(subckts[0])
            end_idx =spiceContent.find('.ends',start_idx)
            subckt = spiceContent[start_idx:end_idx]
            pattern2 = re.compile(r'\nX[\S+]+\s*')
            instances = re.findall(pattern2, subckt)
            if len(instances) > minimum_devices_number:
                return True, 'Design is complex and contains: '+str(len(instances))+' subckts'
            else:
                return False, "The subckt "+subckt_name + " doesn't contain the minimum number of devices required"
        else:
            return False, 'instance '+subckt_name+ ' not found'
    except OSError:
        return False, 'Spice file '+str(spice_netlist)+ ' not found'


def confirm_circuit_hierarchy(spice_netlist, toplevel, user_module):
    try:
        spiceOpener = open(spice_netlist)
        if spiceOpener.mode == 'r':
            spiceContent = spiceOpener.read()
        spiceOpener.close()
        pattern = re.compile(r'\.subckt\s*\b%s\b\s*' % toplevel)
        subckts = re.findall(pattern, spiceContent)
        if len(subckts):
            start_idx = spiceContent.find(subckts[0])
            end_idx =spiceContent.find('.ends',start_idx)
            subckt = spiceContent[start_idx:end_idx]
            pattern = re.compile(r'\nX[\S+]+\s*')
            instances = re.findall(pattern, subckt)
            instances.append('.ends')
            if len(instances)>1:
                ins_start_idx = 0
                for ins in instances[1:]:
                    ins_end_idx = subckt.find(ins,ins_start_idx)
                    instantiation = subckt[ins_start_idx:ins_end_idx]
                    if instantiation.strip().split()[-1] == user_module:
                        return True, user_module + ' is part of ' + toplevel
                    ins_start_idx = ins_end_idx
            return False, 'Hierarchy Check Failed'
        else:
            return False, 'instance '+toplevel+ ' not found'
    except OSError:
        return False, 'Spice file '+str(spice_netlist)+ ' not found'

def extract_connections_from_inst(spice_netlist, toplevel,user_module):
    try:
        spiceOpener = open(spice_netlist)
        if spiceOpener.mode == 'r':
            spiceContent = spiceOpener.read()
        spiceOpener.close()
        # Extract what it's connected to, in the toplevel
        connections = list()
        pattern = re.compile(r'\.subckt\s*\b%s\b\s*' % toplevel)
        subckts = re.findall(pattern, spiceContent)
        if len(subckts):
            start_idx = spiceContent.find(subckts[0])
            end_idx =spiceContent.find('.ends',start_idx)
            subckt = spiceContent[start_idx:end_idx]
            pattern = re.compile(r'\nX[\S+]+\s*')
            instances = re.findall(pattern, subckt)
            instances.append('.ends')
            if len(instances)>1:
                ins_start_idx = 0
                for ins in instances[1:]:
                    ins_end_idx = subckt.find(ins,ins_start_idx)
                    instantiation = subckt[ins_start_idx:ins_end_idx]
                    if instantiation.strip().split()[-1] == user_module:
                        connections = instantiation.replace('+',' ').split()[1:-1]
                        break
                    ins_start_idx = ins_end_idx
            # Extract the pinlist in the user_module
            pins_list= list()
            if len(connections):
                pattern = re.compile(r'\.subckt\s*\b%s\b\s*' % user_module)
                subckts = re.findall(pattern, spiceContent)
                if len(subckts):
                    start_idx = spiceContent.find(subckts[0])
                    end_idx =spiceContent.find('.ends',start_idx)
                    subckt = spiceContent[start_idx:end_idx]
                    pattern = re.compile(r'\nX[\S+]+\s*')
                    instances = re.findall(pattern, subckt)
                    if len(instances):
                        subckt = subckt[:subckt.find(instances[0])]
                    pins_list =  subckt.replace('+',' ').split()[2:]
                if len(pins_list):
                    if len(pins_list) == len(connections):
                        connections_map=dict(zip(pins_list,connections))
                        return True, connections_map
                    else:
                        return False, "Couldn't match the pins and connections of the user module"
                else:
                    return False, "Couldn't find the user module subcircuit in the toplevel spice"
            return False, 'Hierarchy Check Failed'
        else:
            return False, 'Hierarchy Check Failed'
    except OSError:
        return False, 'Spice file '+str(spice_netlist)+ ' not found'

def extract_instance_name(spice_netlist, toplevel,instance):
    try:
        spiceOpener = open(spice_netlist)
        if spiceOpener.mode == 'r':
            spiceContent = spiceOpener.read()
        spiceOpener.close()
        pattern = re.compile(r'\.subckt\s*\b%s\b\s*' % toplevel)
        subckts = re.findall(pattern, spiceContent)
        if len(subckts):
            start_idx = spiceContent.find(subckts[0])
            end_idx =spiceContent.find('.ends',start_idx)
            subckt = spiceContent[start_idx:end_idx]
            pattern = re.compile(r'\nX[\S+]+\s*')
            instances = re.findall(pattern, subckt)
            instances.append('.ends')
            if len(instances)>1:
                ins_start_idx = 0
                prev_ins=instances[0]
                for ins in instances[1:]:
                    ins_end_idx = subckt.find(ins,ins_start_idx)
                    instantiation = subckt[ins_start_idx:ins_end_idx]
                    if instantiation.strip().split()[-1] == instance:
                        instance_name = prev_ins.strip()[1:]
                        return True, instance_name
                    prev_ins = ins
                    ins_start_idx = ins_end_idx
            return False, 'Hierarchy Check Failed'
        else:
            return False, 'Hierarchy Check Failed'
    except OSError:
        return False, 'Spice file '+str(spice_netlist)+ ' not found'



def remove_backslashes(name):
    return name.replace('\\','')

def extract_cell_list(spice_netlist, toplevel,exclude_prefix=None):
    try:
        spiceOpener = open(spice_netlist)
        if spiceOpener.mode == 'r':
            spiceContent = spiceOpener.read()
        spiceOpener.close()
        pattern = re.compile(r'\.subckt\s*\b%s\b\s*' % toplevel)
        subckts = re.findall(pattern, spiceContent)
        if len(subckts):
            start_idx = spiceContent.find(subckts[0])
            end_idx =spiceContent.find('.ends',start_idx)
            subckt = spiceContent[start_idx:end_idx]
            pattern = re.compile(r'\nX[\S+]+\s*')
            instances = re.findall(pattern, subckt)
            instances.append('.ends')
            if len(instances)>1:
                name_list = list()
                type_list = list()
                ins_start_idx = 0
                prev_ins=instances[0]
                for ins in instances[1:]:
                    ins_end_idx = subckt.find(ins,ins_start_idx)
                    instantiation = subckt[ins_start_idx:ins_end_idx]
                    inst_type = instantiation.strip().split()[-1]
                    inst_name = prev_ins.strip()[1:]
                    if exclude_prefix is None:
                        name_list.append(remove_backslashes(inst_name))
                        type_list.append(inst_type)
                    else:
                        if inst_name.startswith(exclude_prefix) == False:
                            name_list.append(remove_backslashes(inst_name))
                            type_list.append(inst_type)
                    prev_ins = ins
                    ins_start_idx = ins_end_idx
                return True, name_list, type_list
            return False, 'Hierarchy Check Failed'
        else:
            return False, 'Hierarchy Check Failed'
    except OSError:
        return False, 'Spice file '+str(spice_netlist)+ ' not found'
