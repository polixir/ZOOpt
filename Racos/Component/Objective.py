"""
The class Objective was implemented in this file.
This class contains a func and  a dim

Author:
    Yu-Ren Liu

Time:
    2017.1.20
"""

"""
 This program is free software; you can redistribute it and/or
 modify it under the terms of the GNU General Public License
 as published by the Free Software Foundation; either version 2
 of the License, or (at your option) any later version.

 This program is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.

 You should have received a copy of the GNU General Public License
 along with this program; if not, write to the Free Software
 Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.

 Copyright (C) 2015 Nanjing University, Nanjing, China
"""

from Instance import Instance


class Objective:

    def __init__(self, func=None, dim=None):
        self.__func = func
        self.__dim = dim

    # Construct an instance from
    def construct_instance(self, coordinate):
        new_ins = Instance()
        new_ins.set_coordinates(coordinate)
        new_ins.set_value(self.__func(coordinate))
        return new_ins

    def set_func(self, func):
        self.__func = func

    def set_dim(self, dim):
        self.__dim = dim

    def get_func(self):
        return self.__func

    def get_dim(self):
        return self.__dim