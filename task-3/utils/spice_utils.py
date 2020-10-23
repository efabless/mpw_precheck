import re


def find_subckt(spice_netlist, subckt_name):
    try:
        spiceOpener = open(spice_netlist)
        if spiceOpener.mode == 'r':
            spiceContent = spiceOpener.read()
        spiceOpener.close()
        pattern = re.compile(r'\.subckt\s*%s \s*?' % subckt_name)
        #print(pattern)
        if len(re.findall(pattern, spiceContent)):
            return True, 'instance found'
        else:
            return False, 'instance not found'
        #for signal in re.findall(pattern, spiceContent):
        #    return signal
    except OSError:
        return False, 'Spice file not found'

def confirm_complex_subckt(spice_netlist,subckt_name,minimum_devices_number):
    try:
        spiceOpener = open(spice_netlist)
        if spiceOpener.mode == 'r':
            spiceContent = spiceOpener.read()
        spiceOpener.close()
        pattern = re.compile(r'\.subckt\s*%s \s*?' % subckt_name)
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
                return False, "The subckt doesn't contain the minimum number of devices required"
        else:
            return False, 'instance not found'
    except OSError:
        return False, 'Spice file not found'


def confirm_circuit_hierarchy(spice_netlist, toplevel, user_module):
    try:
        spiceOpener = open(spice_netlist)
        if spiceOpener.mode == 'r':
            spiceContent = spiceOpener.read()
        spiceOpener.close()
        pattern = re.compile(r'\.subckt\s*%s \s*?' % toplevel)
        subckts = re.findall(pattern, spiceContent)
        if len(subckts):
            start_idx = spiceContent.find(subckts[0])
            end_idx =spiceContent.find('.ends',start_idx)
            subckt = spiceContent[start_idx:end_idx]
            pattern = re.compile(r'\nX[\S+]+\s*')
            instances = re.findall(pattern, subckt)
            ins_start_idx = 0
            for ins in instances:
                ins_end_idx = subckt.find(ins,ins_start_idx)
                instantiation = subckt[ins_start_idx:ins_end_idx]
                if instantiation.strip().split()[-1] == user_module:
                    return True, user_module + ' is part of ' + toplevel
                ins_start_idx = ins_end_idx
            return False, 'Hierarchy Check Failed'
        else:
            return False, 'instance not found'
    except OSError:
        return False, 'Spice file not found'


def extract_connections_from_inst(spice_netlist, toplevel,user_module):
    try:
        spiceOpener = open(spice_netlist)
        if spiceOpener.mode == 'r':
            spiceContent = spiceOpener.read()
        spiceOpener.close()
        # Extract what it's connected to, in the toplevel
        connections = list()
        pattern = re.compile(r'\.subckt\s*%s \s*?' % toplevel)
        subckts = re.findall(pattern, spiceContent)
        if len(subckts):
            start_idx = spiceContent.find(subckts[0])
            end_idx =spiceContent.find('.ends',start_idx)
            subckt = spiceContent[start_idx:end_idx]
            pattern = re.compile(r'\nX[\S+]+\s*')
            instances = re.findall(pattern, subckt)
            instances.append('.ends')
            ins_start_idx = 0
            for ins in instances:
                ins_end_idx = subckt.find(ins,ins_start_idx)
                instantiation = subckt[ins_start_idx:ins_end_idx]
                if instantiation.strip().split()[-1] == user_module:
                    connections = instantiation.replace('+',' ').split()[1:-1]
                    break
                ins_start_idx = ins_end_idx
        # Extract the pinlist in the user_module
        pins_list= list()
        if len(connections):
            pattern = re.compile(r'\.subckt\s*%s \s*?' % user_module)
            subckts = re.findall(pattern, spiceContent)
            if len(subckts):
                start_idx = spiceContent.find(subckts[0])
                end_idx =spiceContent.find('.ends',start_idx)
                subckt = spiceContent[start_idx:end_idx]
                pattern = re.compile(r'\nX[\S+]+\s*')
                instances = re.findall(pattern, subckt)
                if len(instances):
                    subckt = subckt[:subckt.find(instances[0])]
                pins_list =  subckt.replace('+',' ').split()[1:-1]
            if len(pins_list):
                if len(pins_list) == len(connections):
                    connections_map=dict(zip(pins_list,connections))
                    return True, connections_map
                else:
                    return False, "Couldn't match the pins and connections of the user module"
            else:
                return False, "Couldn't find the user module subcircuit in the toplevel spice"
        else:
            return False, 'Hierarchy Check Failed'
    except OSError:
        return False, 'Spice file not found'
