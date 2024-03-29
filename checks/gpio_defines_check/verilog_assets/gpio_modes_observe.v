// SPDX-FileCopyrightText: 2022 Efabless Corporation
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//      http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.
// SPDX-License-Identifier: Apache-2.0

// artifical modules, just so pyverilog:parse can collect/report values of the directives.
// Load verilog files in order:
//    gpio-modes-base.v
//    .../userProject/verilog/rtl/user_defines.v
//    gpio-modes-observe.v         <-- this file

module __gpioModeObserve1;
wire [12:0]USER_CONFIG_GPIO_5_INIT  = `USER_CONFIG_GPIO_5_INIT;
wire [12:0]USER_CONFIG_GPIO_6_INIT  = `USER_CONFIG_GPIO_6_INIT;
wire [12:0]USER_CONFIG_GPIO_7_INIT  = `USER_CONFIG_GPIO_7_INIT;
wire [12:0]USER_CONFIG_GPIO_8_INIT  = `USER_CONFIG_GPIO_8_INIT;
wire [12:0]USER_CONFIG_GPIO_9_INIT  = `USER_CONFIG_GPIO_9_INIT;
wire [12:0]USER_CONFIG_GPIO_10_INIT = `USER_CONFIG_GPIO_10_INIT;
wire [12:0]USER_CONFIG_GPIO_11_INIT = `USER_CONFIG_GPIO_11_INIT;
wire [12:0]USER_CONFIG_GPIO_12_INIT = `USER_CONFIG_GPIO_12_INIT;
wire [12:0]USER_CONFIG_GPIO_13_INIT = `USER_CONFIG_GPIO_13_INIT;

wire [12:0]USER_CONFIG_GPIO_25_INIT = `USER_CONFIG_GPIO_25_INIT;
wire [12:0]USER_CONFIG_GPIO_26_INIT = `USER_CONFIG_GPIO_26_INIT;
wire [12:0]USER_CONFIG_GPIO_27_INIT = `USER_CONFIG_GPIO_27_INIT;
wire [12:0]USER_CONFIG_GPIO_28_INIT = `USER_CONFIG_GPIO_28_INIT;
wire [12:0]USER_CONFIG_GPIO_29_INIT = `USER_CONFIG_GPIO_29_INIT;
wire [12:0]USER_CONFIG_GPIO_30_INIT = `USER_CONFIG_GPIO_30_INIT;
wire [12:0]USER_CONFIG_GPIO_31_INIT = `USER_CONFIG_GPIO_31_INIT;
wire [12:0]USER_CONFIG_GPIO_32_INIT = `USER_CONFIG_GPIO_32_INIT;
wire [12:0]USER_CONFIG_GPIO_33_INIT = `USER_CONFIG_GPIO_33_INIT;
wire [12:0]USER_CONFIG_GPIO_34_INIT = `USER_CONFIG_GPIO_34_INIT;
wire [12:0]USER_CONFIG_GPIO_35_INIT = `USER_CONFIG_GPIO_35_INIT;
wire [12:0]USER_CONFIG_GPIO_36_INIT = `USER_CONFIG_GPIO_36_INIT;
wire [12:0]USER_CONFIG_GPIO_37_INIT = `USER_CONFIG_GPIO_37_INIT;
endmodule

// Configurations of GPIO 14 to 24 are used on caravel but not caravan.
module __gpioModeObserve2;
wire [12:0]USER_CONFIG_GPIO_14_INIT = `USER_CONFIG_GPIO_14_INIT;
wire [12:0]USER_CONFIG_GPIO_15_INIT = `USER_CONFIG_GPIO_15_INIT;
wire [12:0]USER_CONFIG_GPIO_16_INIT = `USER_CONFIG_GPIO_16_INIT;
wire [12:0]USER_CONFIG_GPIO_17_INIT = `USER_CONFIG_GPIO_17_INIT;
wire [12:0]USER_CONFIG_GPIO_18_INIT = `USER_CONFIG_GPIO_18_INIT;
wire [12:0]USER_CONFIG_GPIO_19_INIT = `USER_CONFIG_GPIO_19_INIT;
wire [12:0]USER_CONFIG_GPIO_20_INIT = `USER_CONFIG_GPIO_20_INIT;
wire [12:0]USER_CONFIG_GPIO_21_INIT = `USER_CONFIG_GPIO_21_INIT;
wire [12:0]USER_CONFIG_GPIO_22_INIT = `USER_CONFIG_GPIO_22_INIT;
wire [12:0]USER_CONFIG_GPIO_23_INIT = `USER_CONFIG_GPIO_23_INIT;
wire [12:0]USER_CONFIG_GPIO_24_INIT = `USER_CONFIG_GPIO_24_INIT;
endmodule
