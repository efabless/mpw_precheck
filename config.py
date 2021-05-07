
# Initialize global variables 

def init(args):
    global toplevel
    global user_module
    global golden_wrapper
    global link_prefix

    if args.analog_project:
        toplevel        = "caravan"
        user_module     = "user_analog_project_wrapper"
        golden_wrapper  = "user_analog_project_wrapper_empty"
    else:
        toplevel        = "caravel"
        user_module     = "user_project_wrapper"
        golden_wrapper  = "user_project_wrapper_empty"
    
    link_prefix = 'https://raw.githubusercontent.com/efabless/caravel/master'
