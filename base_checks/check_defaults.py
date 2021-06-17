import os
import re
import yaml
import textdistance
from glob import glob
from pathlib import Path

default_path = os.getenv('DEFAULT')
target_path = os.getenv('TARGET_PATH')

views = ['gds', 'lef', 'def', 'mag',
        'maglef','verilog/rtl', 'verilog/gl',
        'spi/lvs']

excludes = ['user_project_wrapper']

must_change = ['owner', 'orgranization', 'organization_url',
                'description', 'git_url', 'project_name', 'project_id']
def view(name, directory):
    return glob(str(Path(directory, name, '*')))

def default_view(name):
    return view(name, default_path)

def updated_view(name):
    return view(name, target_path)

def too_similar(default_txt, txt):
    return textdistance.hamming.normalized_similarity(default_txt, txt) > 0.8

def has_default_README():
    errors = ""
    failed = False
    try:
        with open('%s/README.md'%target_path, 'r') as readme, \
             open('%s/README.md'%default_path, 'r') as default_readme:
                txt = readme.read()
                default_txt = default_readme.read()
                if too_similar(default_txt, txt):
                    failed = True
                    errors += "\nREADME.md has not been changed"
                    return (True, "README.md has not been changed")
    except FileNotFoundError as notFound:
        return (True, "Could not open file %s"%notFound.filename)

def has_default_project_config():
    errors = ""
    failed = False
    try:
        with open('%s/info.yaml'%target_path, 'r') as config_file, \
            open('%s/info.yaml'%default_path, 'r') as default_config_file:
            user_prj_config = yaml.safe_load(config_file)['project']
            default_config = yaml.safe_load(default_config_file)['project']
            for key in user_prj_config.keys():
                if key in must_change:
                    if user_prj_config[key] == default_config[key]:
                        failed = True
                        errors += "\nThe parameter %s in info.yaml is default" % key
    except FileNotFoundError as not_found:
        failed = True
        errors += "\nCould not open file %s" % not_found.filename
    return (failed, errors)


def has_empty_documentation():
    errors = ""
    failed = False
    try:
        with open('%s/README.md'%target_path, 'r') as readme:
            # between ###Documentation and the next header of the same
            # level
            readme_txt = readme.read()
            doc = None
            if "Documentation" in readme_txt:
                header_level = re.search(r'(#*)[ *]Documentation', readme_txt)[1]
                doc = re.search(r"(#+)[ *]Documentation(.*)%s"%(header_level), readme_txt, flags=re.DOTALL)[2]
            if not doc or doc.isspace():
                failed = True
                errors += "\nDocumentation is empty"
    except FileNotFoundError :
        failed = True
        errors +=  "\nCould not open %s/README.md"%directory

    return (failed, errors)

def has_default_content(lc):
    def excluded(filename):
        filename = str(filename)
        is_in_anexclude = False
        for anexclude in excludes:
            is_in_anexclude = is_in_anexclude or (anexclude in filename)
        return is_in_anexclude
    failed = False
    errors = ""
    for name in views:
        try:
            for anupdated_file in updated_view(name):
                anupdated_file = Path(anupdated_file)
                lc.print_control("{{PROGRESS}} Check if %s is default "%anupdated_file.name)
                for adefault_file in default_view(name):
                    adefault_file = Path(adefault_file)
                    if excluded(adefault_file) or excluded(anupdated_file):
                        continue
                    with open(adefault_file, 'rb') as default, \
                        open(anupdated_file, 'rb') as updated:
                        if too_similar(str(default.read()), str(updated.read())):
                            errors += "\n%s file has too much similarity with default caravel_user_project file %s"%(
                            adefault_file.name,
                            anupdated_file.name)
                            failed = True
        except FileNotFoundError as not_found:
            errors += "\ncould not open %s"%not_found.filename
            continue
    return (failed, errors)
