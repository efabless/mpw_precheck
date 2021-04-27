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

import os
import re

docExts = [".rst", ".html", ".md", ".doc", ".docx", ".odt"]
bannedList = ["slave", "blacklist", "whitelist"]
IGNORED_DIRS = ["third_party", ".git"]


def getListOfFiles(dirName):
    # create a list of file and sub directories
    # names in the given directory
    allFiles = list()
    if os.path.basename(dirName) in IGNORED_DIRS:
        return allFiles
    listOfFile = os.listdir(dirName)
    # Iterate over all the entries
    for entry in listOfFile:
        # Create full path
        fullPath = os.path.join(dirName, entry)
        # If entry is a directory then get the list of files in this directory
        if os.path.isdir(fullPath):
            allFiles = allFiles + getListOfFiles(fullPath)
        else:
            allFiles.append(fullPath)
    return allFiles


def checkInclusiveLang(file):
    docOpener = open(file, 'r', encoding='utf-8')
    if docOpener.mode == 'r':
        docContent = docOpener.read()
    docOpener.close()
    for word in bannedList:
        if docContent.find(word) != -1:
            return False, word
    return True, ""


def checkDocumentation(target_path):
    found = os.path.exists(target_path + "/README")
    if found == False:
        for ext in docExts:
            if os.path.exists(target_path + "/README" + str(ext)):
                found = True
                break
    if found:
        files = getListOfFiles(target_path)
        for f in files:
            extension = os.path.splitext(f)[1]
            if extension in docExts:
                check, reason = checkInclusiveLang(f)
                if check == False:
                    return False, "The documentation file " + str(f) + " contains non-inclusive language: " + reason
        return True, ""
    else:
        return False, "Documentation Not Found"
