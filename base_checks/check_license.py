import os
import hashlib
from urllib.request import urlopen


_license_filename = 'LICENSE'
_lib_license_filename = 'LICENSE'
_apache_license_url = 'http://www.apache.org/licenses/LICENSE-2.0.txt'

def check_main_license(path):
    data = urlopen(_apache_license_url).read().strip()
    remote_hash = hashlib.md5(data)
    try:
        local_hash = hashlib.md5(open(os.path.join(path, _license_filename), 'rb').read().strip())
        return remote_hash.hexdigest() == local_hash.hexdigest()
    except OSError:
        return False

def check_lib_license(path):
    libs = []
    if os.path.exists(path):
        for lib_path in next(os.walk(path))[1]:
            try:
                size = os.path.getsize(os.path.join(lib_path, _lib_license_filename))
                libs.append((lib_path, bool(size)))
            except OSError:
                libs.append((lib_path, False))
    return libs

if __name__ == "__main__":
    if check_main_license('.'):
        print("License there!")
    else:
        print("License not there or empty!")

    print(check_lib_license('.'))
