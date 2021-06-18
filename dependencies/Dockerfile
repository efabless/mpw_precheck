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
RUN yum install -y tcllib git tcl tk libjpeg libgomp libXext libSM libXft libffi cairo gettext Xvfb gcc-c++ patch && \
	yum clean all && \
	rm -rf /var/cache/yum

# Install Klayout
RUN yum install -y https://www.klayout.org/downloads/CentOS_7/klayout-0.26.9-0.x86_64.rpm && \
        yum clean all && \
        rm -rf /var/cache/yum

# Install Magic
RUN git clone https://github.com/RTimothyEdwards/magic ./magic_36f61ca

WORKDIR magic_36f61ca

RUN git checkout 36f61ca6010cc1d46ffec07606213b990a865235

# build
RUN ./configure --prefix=/build && \
    make -j4 && \
    make install

# Grab default user_project 
ENV DEFAULT=/tmp/caravel_user_project
RUN git clone https://github.com/efabless/caravel_user_project $DEFAULT


ENV PRECHECKER_ROOT=/usr/local/bin/
ENV BUILD_PATH=/build/

ENV PATH=$PRECHECKER_ROOT:$PRECHECKER_ROOT/scripts:$BUILD_PATH/bin:$BUILD_PATH/bin/Linux-x86_64:$BUILD_PATH/pdn/scripts:$PATH
ENV LD_LIBRARY_PATH=$BUILD_PATH/lib:$BUILD_PATH/lib/Linux-x86_64:$LD_LIBRARY_PATH
ENV MANPATH=$BUILD_PATH/share/man:$MANPATH


RUN mkdir -p /build/version/

RUN date +"Build Timestamp: %Y-%m-%d_%H-%M-%S" > /build/version/magic.version
RUN git rev-parse HEAD >> /build/version/magic.version
RUN tar -czf /build.tar.gz /build

WORKDIR $PRECHECKER_ROOT

