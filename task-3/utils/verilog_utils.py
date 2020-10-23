import re


def find_module(verilog_netlist, module_name):
    try:
        verilogOpener = open(verilog_netlist)
        if verilogOpener.mode == 'r':
            verilogContent = verilogOpener.read()
        verilogOpener.close()
        pattern = re.compile(r'module\s*%s\s*\(' % module_name)
        if len(re.findall(pattern, verilogContent)):
            return True, 'instance found'
        else:
            return False, 'instance not found'
    except OSError:
        return False, 'Verilog file not found'

def confirm_complex_module(verilog_netlist,module_name,minimum_instantiations_number):
    try:
        verilogOpener = open(verilog_netlist)
        if verilogOpener.mode == 'r':
            verilogContent = verilogOpener.read()
        verilogOpener.close()
        pattern = re.compile(r'module\s*%s\s*\(' % module_name)
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
                return False, "The module doesn't contain the minimum number of instantiations required"
        else:
            return False, 'instance not found'
    except OSError:
        return False, 'Verilog file not found'


def confirm_circuit_hierarchy(verilog_netlist, toplevel, user_module):
    try:
        verilogOpener = open(verilog_netlist)
        if verilogOpener.mode == 'r':
            verilogContent = verilogOpener.read()
        verilogOpener.close()
        pattern = re.compile(r'module\s*%s\s*\(' % toplevel)
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
            return False, 'instance not found'
    except OSError:
        return False, 'verilog file not found'



def extract_connections_from_inst(verilog_netlist, toplevel,user_module):
    try:
        verilogOpener = open(verilog_netlist)
        if verilogOpener.mode == 'r':
            verilogContent = verilogOpener.read()
        verilogOpener.close()
        pattern = re.compile(r'module\s*%s\s*\(' % toplevel)
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
                    con_name = con.split('(')[0].strip()
                    start_idx = inst.find(con)
                    end_idx = inst.find(')',start_idx)
                    con = inst[start_idx:end_idx].split('(')[1]
                    concat=con.strip()[1:-1].split(',')
                    concat = [i.strip() for i in concat]
                    connections_map[con_name] = concat

                return True, connections_map
            else:
                return False, 'Hierarchy Check Failed'
        else:
            return False, 'instance not found'
    except OSError:
        return False, 'verilog file not found'


behavioral_keywords = ['always', 'initial', 'if', 'while', 'for', 'forever', 'repeat','reg', 'case','force']
control_characters = ['#', '$', '@']

def verify_non_behavioral_netlist(verilog_netlist):
    try:
        verilogOpener = open(verilog_netlist)
        if verilogOpener.mode == 'r':
            verilogContent = verilogOpener.read()
        verilogOpener.close()
        for keyword in behavioral_keywords:
            pattern = re.compile(r'\s*\b%s\b\s*' % keyword)
            occ = re.findall(pattern, verilogContent)
            if len(occ):
                return False, 'Behavioral Verilog Syntax Found in Netlist Code: '+ str(occ[0])
        for char in control_characters:
            if verilogContent.find(char) != -1:
                return False, 'Behavioral Verilog Syntax Found in Netlist Code: '+ str(char)
        return True, 'Netlist is Structural'        
    except OSError:
        return False, 'verilog file not found'