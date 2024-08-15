# SPDX-FileCopyrightText: 2024 Efabless Corporation
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
FROM rockylinux:9.3 as build

# Common development tools and libraries (kitchen sink approach)
RUN dnf -y update
RUN dnf -y groupinstall "Development Tools"

RUN dnf -y install cairo-devel csh gperf && \
    dnf -y install mesa-libGLU mesa-libGLU-devel ncurses-devel python3-devel python3-tkinter && \
    dnf -y install readline-devel tcl-devel time.x86_64 tk tk-devel wget Xvfb && \
    dnf -y --enablerepo=crb install epel-release nasm && \
    dnf clean all

# Install Python Requirements
RUN pip3 install --no-cache-dir --upgrade pip && \
    pip3 install --no-cache-dir awscli boto3 colorama coloredlogs klayout numpy PySpice pyverilog pyyaml requests strsimpy

# Installation for Iverilog
ENV IVERILOG_ROOT=./iverilog
RUN git clone https://github.com/steveicarus/iverilog.git $IVERILOG_ROOT
WORKDIR $IVERILOG_ROOT
RUN sh autoconf.sh && ./configure && make install

# Download & Install Klayout
ENV KLAYOUT_ROOT=./klayout
RUN mkdir $KLAYOUT_ROOT
WORKDIR $KLAYOUT_ROOT
RUN wget https://www.klayout.org/downloads/RockyLinux_9/klayout-0.29.2-0.x86_64.rpm
RUN dnf -y install ./klayout-0.29.2-0.x86_64.rpm && \
    dnf clean all

# Clone Magic
ENV MAGIC_ROOT=./magic
RUN git clone --depth=1 --branch 8.3.471 https://github.com/RTimothyEdwards/magic.git ${MAGIC_ROOT}
WORKDIR $MAGIC_ROOT
# Build Magic
# '-O0' : disable optimization so vars visible in gdb (not optimized away). Already the default of gcc.
# -g    : keep debugging info, incl. symbols.
# --disable-locking : recommended by tim due to cell-depth of sky130A PDK cells.
# scl enable devtoolset-8 --  : use the devtoolset-8 gcc-8.x (not the native gcc-4.x).
# Note: to use gdb start like:   docker run --ulimit core=-1 --cap-add SYS_PTRACE ...
RUN ./configure --prefix=/build CFLAGS='-g -O0 -m64 -fPIC' &&  make -j4 && make install

# Clone netgen
ENV NETGEN_ROOT=./netgen
RUN git clone --depth=1 --branch 1.5.272 https://github.com/RTimothyEdwards/netgen.git ${NETGEN_ROOT}
WORKDIR $NETGEN_ROOT
RUN ./configure --prefix=/build && make -j4 && make install

# Clone cvc
RUN dnf -y --enablerepo=crb install libstdc++-static
ENV CVC_ROOT=./cvc_rv
RUN git clone --depth=1 --branch v1.1.5 https://github.com/d-m-bailey/cvc.git ${CVC_ROOT}
WORKDIR $CVC_ROOT
RUN autoreconf -vif && ./configure --disable-nls --prefix=/build && sed -i 's/api.parser.class/parser_class_name/' src/cdlParser.yy && make -j4 && make install

# ENV VARIABLES
ENV BUILD_PATH=/build/
ENV LD_LIBRARY_PATH=/usr/local/lib:$BUILD_PATH/lib:$BUILD_PATH/lib:$BUILD_PATH/lib/Linux-x86_64:$LD_LIBRARY_PATH
ENV MANPATH=$BUILD_PATH/share/man:$MANPATH
ENV PRECHECKER_ROOT=/opt/
ENV PATH=$PRECHECKER_ROOT:$PRECHECKER_ROOT/scripts:$BUILD_PATH/bin:$BUILD_PATH/bin/Linux-x86_64:$BUILD_PATH/pdn/scripts:$PATH
WORKDIR $PRECHECKER_ROOT

# GOLDEN CARAVEL
ENV GOLDEN_CARAVEL=/opt/caravel
RUN git clone --depth=1 https://github.com/efabless/caravel-lite.git ${GOLDEN_CARAVEL} && make -C ${GOLDEN_CARAVEL} uncompress
