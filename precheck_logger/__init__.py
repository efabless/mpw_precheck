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

import logging
import logging.config
import sys

import coloredlogs


def get_file_handler(log_path):
    verbose_formatter = {'format': "%(asctime)s - [%(levelname)s] - %(message)s", 'datefmt': '%Y-%m-%d %H:%M:%S'}
    file_handler = logging.FileHandler(filename=log_path, encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter(verbose_formatter['format'], datefmt=verbose_formatter['datefmt']))
    return file_handler


def get_stream_handler(stream):
    brief_formatter = {'format': '%(message)s'}
    stream_handler = logging.StreamHandler(stream=stream)
    stream_handler.setLevel(logging.INFO)
    stream_handler.setFormatter(logging.Formatter(brief_formatter['format']))
    return stream_handler


def initialize_root_logger(log_path):
    stream_handler = get_stream_handler(sys.stdout)
    file_handler = get_file_handler(log_path)

    logging.root.setLevel(logging.DEBUG)
    logging.root.handlers.clear()
    logging.root.addHandler(stream_handler)
    logging.root.addHandler(file_handler)
    coloredlogs.install(level=logging.INFO, fmt='%(message)s', stream=sys.stdout, reconfigure=True)
