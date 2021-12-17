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

# Note: to get cores or use gdb start like:   docker run --ulimit core=-1 --cap-add SYS_PTRACE ...

# syntax = docker/dockerfile:1.0-experimental
FROM centos:centos7 as build

# Common development tools and libraries (kitchen sink approach)
RUN yum -y install centos-release-scl && \
    yum -y install devtoolset-8 devtoolset-8-libatomic-devel && \
    yum clean all && \
    rm -rf /var/cache/yum

# Python 3.6
RUN yum install -y https://repo.ius.io/ius-release-el7.rpm && \
    yum clean all && \
    rm -rf /var/cache/yum
RUN yum install -y python36u python36u-devel python36u-libs python36u-pip python36u-tkinter && \
    yum clean all && \
    rm -rf /var/cache/yum
RUN alternatives --install /usr/bin/python3 python3 /usr/bin/python3.6 60
RUN pip3.6 install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir awscli boto3 colorama coloredlogs klayout numpy pyyaml requests strsimpy

# Install pyverilog & pyspice
RUN pip install --no-cache-dir https://github.com/PyHDI/Pyverilog/archive/develop.zip && \
    pip install --no-cache-dir pyspice

# General Utils
RUN yum install -y ruby tcllib git tcl tk libjpeg libgomp libXext libSM libXft libffi cairo gettext Xvfb gcc-c++ patch \
    gdb.x86_64 file.x86_64 time.x86_64 && \
    yum clean all && \
    rm -rf /var/cache/yum

# uninstall current version of git and install latest version instead
RUN yum -y remove git && yum -y remove git-* && \
    yum -y install https://packages.endpoint.com/rhel/7/os/x86_64/endpoint-repo-1.9-1.x86_64.rpm && \
    yum -y install git && \
    yum clean all && \
    rm -rf /var/cache/yum

# Install iverilog
RUN yum install -y iverilog && \
    yum clean all && \
    rm -rf /var/cache/yum

# Magic Dependencies
RUN yum install -y libglu tcl tk csh wget tcl-devel tk-devel libX11-devel ncurses-devel \
    yum clean all && \
    rm -rf /var/cache/yum

# Install Klayout
RUN yum install -y https://www.klayout.org/downloads/CentOS_7/klayout-0.27.5-0.x86_64.rpm && \
    yum clean all && \
    rm -rf /var/cache/yum

# Clone Magic
RUN git clone --depth=1 --branch 8.3.241 https://github.com/RTimothyEdwards/magic.git ./magic_8_3_241
WORKDIR magic_8_3_241
# Build Magic
# '-O0' : disable optimization so vars visible in gdb (not optimized away). Already the default of gcc.
# -g    : keep debugging info, incl. symbols.
# --disable-locking : recommended by tim due to cell-depth of sky130A PDK cells.
# scl enable devtoolset-8 --  : use the devtoolset-8 gcc-8.x (not the native gcc-4.x).
# Note: to use gdb start like:   docker run --ulimit core=-1 --cap-add SYS_PTRACE ...
RUN scl enable devtoolset-8 -- ./configure --disable-locking --prefix=/build CFLAGS='-g -O0 -m64 -fPIC' && \
    scl enable devtoolset-8 -- make -j4 && \
    scl enable devtoolset-8 -- make install

ENV PRECHECKER_ROOT=/opt/
ENV BUILD_PATH=/build/
ENV PATH=$PRECHECKER_ROOT:$PRECHECKER_ROOT/scripts:$BUILD_PATH/bin:$BUILD_PATH/bin/Linux-x86_64:$BUILD_PATH/pdn/scripts:$PATH
ENV LD_LIBRARY_PATH=$BUILD_PATH/lib:$BUILD_PATH/lib/Linux-x86_64:$LD_LIBRARY_PATH
ENV MANPATH=$BUILD_PATH/share/man:$MANPATH
ENV LANG en_US.UTF-8
ENV LC_ALL en_US.UTF-8
ENV LC_CTYPE en_US.UTF-8
WORKDIR $PRECHECKER_ROOT