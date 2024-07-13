#########################################################
# Module written to Odoo, Open Source Management Solution
#
# Copyright (c) 2023 Birtum - https://www.birtum.com
# All Rights Reserved.
#
# Developer(s): Eddy Luis Pérez Vila <epv@birtum.com>
#########################################################
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
##########################################################


class CaselessDictionary(dict):
    _description = "CaselessDictionary"

    """Dictionary that enables case insensitive searching while preserving case sensitivity
when keys are listed, ie, via keys() or items() methods.
Works by storing a lowercase version of the key as the new key and stores the original key-value
pair as the key's value (values become dictionaries)."""

    def __init__(self, initval={}):
        if isinstance(initval, dict):
            for key, value in initval.items():
                self.__setitem__(key, value)
        elif isinstance(initval, list):
            for key, value in initval:
                self.__setitem__(key, value)

    def __contains__(self, key):
        return dict.__contains__(self, key.lower())

    def __getitem__(self, key):
        return dict.__getitem__(self, key.lower())["val"]

    def __setitem__(self, key, value):
        return dict.__setitem__(self, key.lower(), {"key": key, "val": value})

    def get(self, key, default=None):
        try:
            v = dict.__getitem__(self, key.lower())
        except KeyError:
            return default
        else:
            return v["val"]

    def has_key(self, key):
        if self.get(key):
            return True
        else:
            return False

    def items(self):
        return [(v["key"], v["val"]) for v in dict.values(self)]

    def keys(self):
        return [v["key"] for v in dict.values(self)]

    def values(self):
        return [v["val"] for v in dict.values(self)]

    def iteritems(self):
        for v in dict.values(self):
            yield v["key"], v["val"]

    def iterkeys(self):
        for v in dict.values(self):
            yield v["key"]

    def itervalues(self):
        for v in dict.values(self):
            yield v["val"]
