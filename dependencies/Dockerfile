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

FROM gcr.io/hdl-containers/debian/bullseye/build/base

# klayout deps
COPY --from=gcr.io/hdl-containers/debian/bullseye/pkg/klayout /klayout /
RUN apt-get update -qq \
 && DEBIAN_FRONTEND=noninteractive apt-get -y install --no-install-recommends \
    libpulse-mainloop-glib0 libpython3.9 libqt5core5a libqt5designer5 libqt5gui5 libqt5multimedia5 libqt5multimediawidgets5 libqt5printsupport5 libqt5sql5 libqt5svg5 libqt5widgets5 libqt5xml5 libqt5xmlpatterns5 libruby \
 && apt-get autoclean && apt-get clean && apt-get -y autoremove \    
 && rm -rf /var/lib/apt/lists/*
COPY --from=gcr.io/hdl-containers/debian/bullseye/pkg/klayout /klayout/ /  
RUN klayout -v

# magic deps
COPY --from=gcr.io/hdl-containers/debian/bullseye/pkg/magic /magic/ /
RUN apt-get update -qq \
 && DEBIAN_FRONTEND=noninteractive apt-get -y install --no-install-recommends \
    libcairo2 libglu1-mesa libncurses6 libx11-6 tcl tk \
 && apt-get autoclean && apt-get clean && apt-get -y autoremove \
 && rm -rf /var/lib/apt/lists/*
COPY --from=gcr.io/hdl-containers/debian/bullseye/pkg/magic /magic/ / 
RUN magic --version

# iverilog deps
RUN apt-get update -qq \
 && DEBIAN_FRONTEND=noninteractive apt-get -y install --no-install-recommends \
    perl \
 && apt-get autoclean && apt-get clean && apt-get -y autoremove \
 && rm -rf /var/lib/apt/lists/*
COPY --from=gcr.io/hdl-containers/debian/bullseye/pkg/iverilog /iverilog/ /
RUN iverilog -V

# precheck deps
RUN apt-get update -qq \
 && DEBIAN_FRONTEND=noninteractive apt-get -y install --no-install-recommends \
    python3 python3-pip git make procps \
 && apt-get autoclean && apt-get clean && apt-get -y autoremove \
 && rm -rf /var/lib/apt/lists/*
RUN python3 -m pip install awscli boto3 colorama coloredlogs klayout numpy PySpice pyverilog pyyaml requests strsimpy

ENV PRECHECKER_ROOT=/opt/
ENV PATH=$PRECHECKER_ROOT:$PRECHECKER_ROOT/scripts:$BUILD_PATH/bin:$BUILD_PATH/bin/Linux-x86_64:$BUILD_PATH/pdn/scripts:$PATH
WORKDIR $PRECHECKER_ROOT

# GOLDEN CARAVEL SKY130
ENV GOLDEN_CARAVEL=/opt/caravel
RUN git clone --branch mpw-8c --depth=1 https://github.com/efabless/caravel-lite.git ${GOLDEN_CARAVEL} && make -C ${GOLDEN_CARAVEL} uncompress

# GOLDEN CARAVEL GF180MCU
ENV GOLDEN_CARAVEL_GF180MCU=/opt/caravel-gf180mcu
RUN git clone --branch gfmpw-0d --depth=1 https://github.com/efabless/caravel-gf180mcu.git ${GOLDEN_CARAVEL_GF180MCU} && make -C ${GOLDEN_CARAVEL_GF180MCU} uncompress
