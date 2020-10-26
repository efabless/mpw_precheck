import os
import yaml
from typing import NamedTuple

_yaml_filename = 'info.yaml'

class YamlStructure(NamedTuple):
    name: str
    description: str
    git_url: str
    version: int = 1


def check_yaml(path):
    try:
        content = yaml.load(open(os.path.join(path, _yaml_filename)).read())
        obj = YamlStructure(**content)
        return True
    except TypeError as e:
        return False
    except FileNotFoundError as e:
        return False


if __name__ == "__main__":
    if check_yaml('.'):
        print("YAML file valid!")
    else:
        print("YAML file not valid!")
