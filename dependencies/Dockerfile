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

# ENV VARIABLES
ENV LANG en_US.UTF-8
ENV LC_ALL en_US.UTF-8
ENV LC_CTYPE en_US.UTF-8

# Common development tools and libraries (kitchen sink approach)
RUN yum -y install deltarpm.x86_64 centos-release-scl && \
    yum -y install devtoolset-8 devtoolset-8-libatomic-devel && \
    yum -y install https://repo.ius.io/ius-release-el7.rpm && \
    yum -y install -y python36u python36u-devel python36u-libs python36u-pip python36u-tkinter && \
    yum clean all && \
    rm -rf /var/cache/yum

# Set python 3.6 as default python3
RUN alternatives --install /usr/bin/python3 python3 /usr/bin/python3.6 60
RUN pip3.6 install --no-cache-dir --upgrade pip && \
    pip3.6 install --no-cache-dir awscli boto3 colorama coloredlogs klayout numpy PySpice pyverilog pyyaml requests strsimpy

# General Dependencies
RUN yum install -y tcllib tcl tk libjpeg libgomp libXext libSM libXft libffi cairo gettext Xvfb gcc-c++ gdb.x86_64 file.x86_64 time.x86_64 && \
    yum install -y csh libglu libX11-devel ncurses-devel tcl-devel tk-devel wget && \
    yum install -y git patch ruby && \
    yum install -y iverilog && \
    yum install -y m4 && \
    yum install -y gettext-devel bison byacc readline-devel && \
    yum install -y flex autotools-dev build-essential autoconf pkg-config nasm libtool automake && \
    yum install -y https://www.klayout.org/downloads/CentOS_7/klayout-0.27.12-0.x86_64.rpm && \
    yum clean all && \
    rm -rf /var/cache/yum

# uninstall current version of git and install latest version available in rhel/7
RUN yum -y remove git && yum -y remove git-* && \
    yum -y install https://repo.ius.io/7/x86_64/packages/g/git236-2.36.1-2.el7.ius.x86_64.rpm && \
    yum clean all && \
    rm -rf /var/cache/yum

# Clone Magic
ENV MAGIC_ROOT=/opt/magic
RUN git clone --depth=1 --branch 8.3.394 https://github.com/RTimothyEdwards/magic.git ${MAGIC_ROOT}
WORKDIR $MAGIC_ROOT
# Build Magic
# '-O0' : disable optimization so vars visible in gdb (not optimized away). Already the default of gcc.
# -g    : keep debugging info, incl. symbols.
# --disable-locking : recommended by tim due to cell-depth of sky130A PDK cells.
# scl enable devtoolset-8 --  : use the devtoolset-8 gcc-8.x (not the native gcc-4.x).
# Note: to use gdb start like:   docker run --ulimit core=-1 --cap-add SYS_PTRACE ...
RUN scl enable devtoolset-8 -- ./configure --prefix=/build CFLAGS='-g -O0 -m64 -fPIC' && \
    scl enable devtoolset-8 -- make -j4 && \
    scl enable devtoolset-8 -- make install

# ENV VARIABLES
ENV BUILD_PATH=/build/
ENV LD_LIBRARY_PATH=$BUILD_PATH/lib:$BUILD_PATH/lib/Linux-x86_64:$LD_LIBRARY_PATH
ENV MANPATH=$BUILD_PATH/share/man:$MANPATH
ENV PRECHECKER_ROOT=/opt/
ENV PATH=$PRECHECKER_ROOT:$PRECHECKER_ROOT/scripts:$BUILD_PATH/bin:$BUILD_PATH/bin/Linux-x86_64:$BUILD_PATH/pdn/scripts:$PATH
WORKDIR $PRECHECKER_ROOT

# GOLDEN CARAVEL
ENV GOLDEN_CARAVEL=/opt/caravel
RUN git clone --branch mpw-9a --depth=1 https://github.com/efabless/caravel-lite.git ${GOLDEN_CARAVEL} && make -C ${GOLDEN_CARAVEL} uncompress


# Clone netgen
ENV NETGEN_ROOT=/opt/netgen
RUN git clone --depth=1 --branch 1.5.253 https://github.com/RTimothyEdwards/netgen.git ${NETGEN_ROOT}
WORKDIR $NETGEN_ROOT
RUN scl enable devtoolset-8 -- ./configure --prefix=/build && \
    scl enable devtoolset-8 -- make -j4 && \
    scl enable devtoolset-8 -- make install


# Clone cvc
ENV CVC_ROOT=/opt/cvc_rv
WORKDIR $CVC_ROOT
RUN git clone --depth=1 --branch v1.1.5 https://github.com/d-m-bailey/cvc.git ${CVC_ROOT}
RUN scl enable devtoolset-8 -- autoreconf -vif ; \
    scl enable devtoolset-8 -- ./configure --disable-nls --prefix=/build ; \
    scl enable devtoolset-8 -- sed -i 's/api.parser.class/parser_class_name/' src/cdlParser.yy ; \
    scl enable devtoolset-8 -- make -j4 ; \
    scl enable devtoolset-8 -- make install
