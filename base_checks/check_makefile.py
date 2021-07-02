# SPDX-FileCopyrightText: 2020 Efabless Corporation
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
# SPDX-License-Identifier: Apache-2.0

# makefileTargets = ["verify", "clean", "compress", "uncompress"]
makefileTargets = ["verify", "clean"]


def checkMakefile(target_path):
    succeeded = True
    errors = ""
    try:
        makefileOpener = open(target_path + "/Makefile")
        if makefileOpener.mode == "r":
            makefileContent = makefileOpener.read()
        makefileOpener.close()

        for target in makefileTargets:
            if makefileContent.count(target + ":") == 0:
                succeeded = False
                errors += "Makefile missing target: " + target + ":"
            if target == "compress":
                if makefileContent.count(target + ":") < 2:
                    succeeded = False
                    errors += "Makefile missing target: " + target + ":"
    except OSError:
        succeeded = False
        errors += "Makefile not found at top level"

    return succeeded, errors
