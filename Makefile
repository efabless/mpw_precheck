# Copyright 2020 Efabless Corporation
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

THREADS ?= $(shell nproc)
STD_CELL_LIBRARY ?= sky130_fd_sc_hd
SPECIAL_VOLTAGE_LIBRARY ?= sky130_fd_sc_hvl
PRIMITIVES_LIBRARY ?= sky130_fd_pr
IO_LIBRARY ?= sky130_fd_io

SKYWATER_COMMIT ?= bb2f842ac8d1b750677ca25bc71fb312859edb82
OPEN_PDKS_COMMIT ?= cc82b606c3f50baedfcbd99567652e828739ff41

.DEFAULT_GOAL := pdk

.PHONY: pdk
pdk: skywater-pdk skywater-library open_pdks build-pdk

$(PDK_ROOT)/skywater-pdk:
	git clone https://github.com/google/skywater-pdk.git $(PDK_ROOT)/skywater-pdk

.PHONY: skywater-pdk
skywater-pdk: check-env $(PDK_ROOT)/skywater-pdk
	cd $(PDK_ROOT)/skywater-pdk && \
		git checkout main && git pull && \
		git checkout -qf $(SKYWATER_COMMIT)

.PHONY: skywater-library
skywater-library: check-env $(PDK_ROOT)/skywater-pdk
	cd $(PDK_ROOT)/skywater-pdk && \
		git submodule update --init libraries/$(STD_CELL_LIBRARY)/latest && \
		git submodule update --init libraries/$(IO_LIBRARY)/latest && \
		git submodule update --init libraries/$(SPECIAL_VOLTAGE_LIBRARY)/latest && \
		git submodule update --init libraries/$(PRIMITIVES_LIBRARY)/latest

### OPEN_PDKS
$(PDK_ROOT)/open_pdks:
	git clone https://github.com/RTimothyEdwards/open_pdks.git $(PDK_ROOT)/open_pdks

.PHONY: open_pdks
open_pdks: check-env $(PDK_ROOT)/open_pdks
	cd $(PDK_ROOT)/open_pdks && \
		git checkout master && git pull && \
		git checkout -qf $(OPEN_PDKS_COMMIT)

.PHONY: build-pdk
build-pdk: check-env $(PDK_ROOT)/open_pdks $(PDK_ROOT)/skywater-pdk
	[ -d $(PDK_ROOT)/sky130A ] && \
		(echo "Warning: A sky130A build already exists under $(PDK_ROOT). It will be deleted first!" && \
		sleep 5 && \
		rm -rf $(PDK_ROOT)/sky130A) || \
		true
	cd $(PDK_ROOT)/open_pdks && \
		./configure --enable-sky130-pdk=$(PDK_ROOT)/skywater-pdk --with-sky130-local-path=$(PDK_ROOT) --enable-sram-sky130 --disable-xschem-sky130 && \
		cd sky130 && \
		$(MAKE) veryclean && \
		$(MAKE) && \
		$(MAKE) install-local && \
		$(MAKE) clean

check-env:
ifndef PDK_ROOT
	$(error PDK_ROOT is undefined, please export it before running make)
endif
