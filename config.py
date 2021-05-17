# Initialize global variables

def init(project_type):
    global toplevel
    global user_module
    global golden_wrapper
    global link_prefix

    if project_type == "analog":
        toplevel = "caravan"
        user_module = "user_analog_project_wrapper"
        golden_wrapper = "user_analog_project_wrapper_empty"
    else:  # digital
        toplevel = "caravel"
        user_module = "user_project_wrapper"
        golden_wrapper = "user_project_wrapper_empty"

    link_prefix = 'https://raw.githubusercontent.com/efabless/caravel/master'
