import os
import re
import yaml
import textdistance
import hashlib
import gzip
from glob import glob
from pathlib import Path

# default_content_path = os.getenv('DEFAULT')
# target_path = os.getenv('TARGET_PATH')

# views = ['gds', 'lef', 'def', 'mag',
#         'maglef','verilog/rtl', 'verilog/gl',
#         'spi/lvs']

views = ['gds']

# excludes = ['user_project_wrapper']

excludes = []

must_change = ['owner', 'orgranization', 'organization_url',
                'description', 'git_url', 'project_name']

def is_binary_file(filename):
    file_extensions = Path(filename).suffix
    return 'gds' in file_extensions or 'gz' in file_extensions

def not_binary_file(filename):
    return not is_binary_file(filename)

def is_compressed(filename):
    with open(filename, 'rb') as f:
        return f.read(2) == b'\x1f\x8b'

def file_hash(filename):
    print(filename)
    sha1 = hashlib.sha1()
    BSIZE = 65536
    if is_compressed(filename):
        f = gzip.open(filename, 'rb')
    else:
        f = open(filename, 'rb')
    while True:
        try:
            data = f.read(BSIZE)
            if not data:
                break
            sha1.update(data)
        except EOFError:
            # To handle split gds files during tapeout
            break
    f.close()
    return sha1.hexdigest()

def view(name, directory):
    return glob(str(Path(directory, name, '*')))

def default_view(default_content_path, name):
    return view(name, default_content_path)

def updated_view(target_path, name):
    return view(name, target_path)

def too_similar(default_txt, txt):
    return textdistance.hamming.normalized_similarity(default_txt, txt) > 0.8

def has_default_README(target_path, default_content_path):
    errors = ""
    failed = False
    try:
        with open('%s/README.md'%target_path, 'r') as readme, \
             open('%s/README.md'%default_content_path, 'r') as default_readme:
                txt = readme.read()
                default_txt = default_readme.read()
                if too_similar(default_txt, txt):
                    failed = True
                    errors += "\nREADME.md has not been changed"
    except FileNotFoundError as notFound:
        failed = True
        errors += "\nCould not open file %s"%notFound.filename
    return (failed, errors)

def has_default_project_config(target_path, default_content_path):
    errors = ""
    failed = False
    try:
        with open('%s/info.yaml'%target_path, 'r') as config_file, \
            open('%s/info.yaml'%default_content_path, 'r') as default_config_file:
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

def has_default_content(target_path, default_content_path):
    def excluded(filename):
        filename = str(filename)
        is_in_anexclude = False
        for anexclude in excludes:
            is_in_anexclude = is_in_anexclude or (anexclude in filename)
        return is_in_anexclude
    failed = False
    errors = ""
    for view_name in views:
        try:
            for anupdated_file in updated_view(target_path, view_name):
                anupdated_file = Path(anupdated_file)
                for adefault_file in default_view(default_content_path, view_name):
                    adefault_file = Path(adefault_file)
                    if excluded(adefault_file) or excluded(anupdated_file):
                        continue
                    if not_binary_file(adefault_file) and not_binary_file(anupdated_file):
                        with open(adefault_file, 'r') as default, \
                            open(anupdated_file, 'r') as updated:
                            if too_similar(str(default.read()), str(updated.read())):
                                errors += "\n%s file has too much similarity with default caravel_user_project file %s"%(
                                adefault_file.name,
                                anupdated_file.name)
                                failed = True
                    else:
                        if file_hash(adefault_file) == file_hash(anupdated_file):
                            errors += "\n%s file is identical to default caravel_user_project file %s"%(
                            adefault_file.name,
                            anupdated_file.name)
                            failed = True
        except FileNotFoundError as not_found:
            errors += "\ncould not open %s"%not_found.filename
            continue
    return (failed, errors)
