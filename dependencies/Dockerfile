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

# python 3.6
RUN yum install -y https://repo.ius.io/ius-release-el7.rpm && \
        yum clean all && \
        rm -rf /var/cache/yum
RUN yum install -y python36u python36u-libs python36u-devel python36u-pip python36u-tkinter && \
        yum clean all && \
        rm -rf /var/cache/yum
RUN alternatives --install /usr/bin/python3 python3 /usr/bin/python3.6 60

RUN pip3.6 install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir \
                pyyaml \
                awscli \
                requests \
                boto3 \
                strsimpy \
                textdistance

# magic dependencies
RUN yum install -y libglu tcl tk csh wget tcl-devel tk-devel libX11-devel ncurses-devel

# General utils
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

# Install Klayout
RUN yum install -y https://www.klayout.org/downloads/CentOS_7/klayout-0.27.3-0.x86_64.rpm && \
        yum clean all && \
        rm -rf /var/cache/yum

# Install Magic
# RUN git clone https://github.com/RTimothyEdwards/magic ./magic_597ef48
RUN git clone -n git://opencircuitdesign.com/magic \
         ./magic_597ef48
WORKDIR    magic_597ef48
RUN git checkout 597ef4857a02f1d0748475dcff118801e91b0e88

# build
# '-O0' : disable optimization so vars visible in gdb (not optimized away). Already the default of gcc.
# -g    : keep debugging info, incl. symbols.
# --disable-locking : recommended by tim due to cell-depth of sky130A PDK cells.
# scl enable devtoolset-8 --  : use the devtoolset-8 gcc-8.x (not the native gcc-4.x).
# Note: to use gdb start like:   docker run --ulimit core=-1 --cap-add SYS_PTRACE ...
RUN scl enable devtoolset-8 -- ./configure --disable-locking --prefix=/build CFLAGS='-g -O0 -m64 -fPIC' && \
    scl enable devtoolset-8 -- make -j4 && \
    scl enable devtoolset-8 -- make install

# ENV CARAVEL_USER_PROJECT_PATH=/tmp/caravel_user_project
ENV PRECHECKER_ROOT=/usr/local/bin/
ENV BUILD_PATH=/build/
ENV PATH=$PRECHECKER_ROOT:$PRECHECKER_ROOT/scripts:$BUILD_PATH/bin:$BUILD_PATH/bin/Linux-x86_64:$BUILD_PATH/pdn/scripts:$PATH
ENV LD_LIBRARY_PATH=$BUILD_PATH/lib:$BUILD_PATH/lib/Linux-x86_64:$LD_LIBRARY_PATH
ENV MANPATH=$BUILD_PATH/share/man:$MANPATH
ENV LANG en_US.UTF-8
ENV LC_ALL en_US.UTF-8
ENV LC_CTYPE en_US.UTF-8
ENV LANG C.UTF-8

# Grab default user_project
# RUN git clone https://github.com/efabless/caravel_user_project $CARAVEL_USER_PROJECT_PATH

RUN mkdir -p /build/version/

RUN date +"Build Timestamp: %Y-%m-%d_%H-%M-%S" > /build/version/magic.version
RUN git rev-parse HEAD >> /build/version/magic.version
RUN tar -czf /build.tar.gz /build

WORKDIR $PRECHECKER_ROOT