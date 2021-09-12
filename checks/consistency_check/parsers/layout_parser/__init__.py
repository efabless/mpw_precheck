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

import klayout.db as pya


class DataError(Exception):
    pass


class LayoutParser:
    """Layout (GDS) parser
    
    Arguments:
        layout_path: Path to layout file.
        top_module: Layout Top module name.

    Attributes:
        layout: Klayout layout object.
        top_module: Top module name.
        cell_names: list of top module cell names.
        cells: List of top cell subcell objects.
    """

    def __init__(self, layout_path, top_module):
        """Create LayoutParser instance"""
        self.layout = None
        self.top_module = top_module
        self.cell_names = []
        self.cells = []

        self.layout = pya.Layout()
        self.layout.read(str(layout_path))
        top_cell = self.layout.top_cell()

        if top_cell.name != top_module:
            raise DataError(f"Top module: {top_module} is not found in {layout_path}.")

        for node in top_cell.each_child_cell():
            cell = self.layout.cell(node)
            self.cell_names.append(cell.name)
            self.cells.append(cell)

            is_empty = cell.is_empty()
            if is_empty:
                raise DataError(f"Layout {layout_path} contains empty cell: {cell.name}.")

            # Make sure that all subcells are part of the file 
            # TODO: flatten layout to catch all ghost cells
            is_ghost = cell.is_ghost_cell()
            if is_ghost:
                raise DataError(f"Layout {layout_path} contains a ghost cell: {cell.name}.")

    def get_children(self):
        """Get List of top module child cells names """
        return self.cell_names

    def get_grandchildren(self, cell_name):
        """Get List of child cells names for the given cell"""
        try:
            indx = self.cell_names.index(cell_name)
        except ValueError:
            return []

        grandchildren = []
        cell = self.cells[indx]
        subcells = cell.each_child_cell()

        for cell in subcells:
            cell_name = self.layout.cell(cell).name
            grandchildren.append(cell_name)

        return grandchildren
