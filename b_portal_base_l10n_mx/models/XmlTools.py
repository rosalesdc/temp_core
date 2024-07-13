# -*- encoding: utf-8 -*-
#
# Module written to Odoo, Open Source Management Solution
#
# Copyright (c) 2020 Telematel - http://www.telematel.com/
# All Rights Reserved.
#
# Developer(s): Sergio Ernesto Tostado Sánchez
#               (sergio.tostado@telematel.com)
#
########################################################################
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
########################################################################
#
#  HOW TO USE THIS CLASS
#
# x = XmlTools.XmlTools()
# 
# paths = [
#     "/home/sets/Descargas/Descargas.zip",
#     "/home/sets/Descargas/ams_calcul_preu_cost_view.xml",
#     "/home/sets/Descargas/"
# ]
# 
# print x.get_xml_dict_from_attachment(paths[1])
# 


import logging
import os
import xmltodict
import shutil
import base64

import datetime
import tempfile

from pyunpack import Archive
from datetime import datetime

_logger = logging.getLogger(__name__)


class XmlTools:

    # For patools format
    COMPRESS_FORMATS = [
        ".7z", ".ace", ".alz", ".a", ".arc", ".arj", ".bz2", ".cab",
        ".Z", ".cpio", ".deb", ".dms", ".gz", ".lrz", ".lha", ".lzh",
        ".lz", ".lzma", ".lzo", ".rpm", ".rar", ".rz", ".tar", ".xz",
        ".zip", ".jar", ".zoo"
    ]

    # param compressed_path: Any path to compressed file
    # returns: str
    def get_uncompress_dir(self, compressed_path):
        filepath = compressed_path[:compressed_path.rfind(os.sep)]
        uncompressed_dir = datetime.today().strftime(
            "%d%m%Y-%H%M")
        return os.path.join(filepath, uncompressed_dir)

    # param compressed_path: Any path to compressed file
    # returns: list
    def get_xml_paths_from_compressed(self, compressed_path):
        """ Get xml paths at compressed file """
        xml_paths = []
        to_dir = self.get_uncompress_dir(compressed_path)
        os.makedirs(to_dir)
        Archive(compressed_path, backend="auto").extractall(to_dir)
        xml_paths = [os.path.join(dir,f) for (dir, subdirs, fs) in os.walk(to_dir) for f in fs if self.is_xml_file(f)]
        return xml_paths

    def is_compressed_file(self, xml_path):
        return xml_path[xml_path.rfind("."):] in self.COMPRESS_FORMATS

    def is_xml_file(self, xml_path):
        return xml_path.endswith(".xml") or xml_path.endswith(".XML")

    # param xml_path: Path to xml file
    # returns: str
    def get_string_from_xml_file(self, xml_path):
        xml_string = ""
        with open(xml_path, "r") as xml:
            for line in xml:
                xml_string += line
        return [xml_string,
                xml_path[xml_path.rfind(os.sep)+1:],
                base64.b64encode(xml_string.encode('utf-8'))] # TODO: THINK IN POST-COMPABILITY python3 enconding('utf-8')

    # param xml_str: xml string from an xml file
    # returns: dict
    def get_dict_from_xml(self, xml_str):
        """ Use xmltodict lib to get xml string -> dict """
        return xmltodict.parse(xml_str)

    # param path: Path of file
    # returns: list of dicts
    def get_xml_dict_from_attachment(self, path):
        """ Get xml data represented via a list of dict """
        if os.path.isfile(path):
            xml_dicts = []
            # xml treatment
            if self.is_xml_file(path):
                xml_str = self.get_string_from_xml_file(path)
                xml_dicts = [[self.get_dict_from_xml(xml_str[0]), xml_str[1], xml_str[2]]]
            # compressed file like rar or zip treatment
            elif self.is_compressed_file(path):
                #import pdb;pdb.set_trace()
                xml_strs = [self.get_string_from_xml_file(xml) for xml in self.get_xml_paths_from_compressed(path)]
                shutil.rmtree(self.get_uncompress_dir(path)) # For disc space reasons
                xml_dicts = [[self.get_dict_from_xml(xml_str[0]), xml_str[1], xml_str[2]] for xml_str in xml_strs]
            else:
                _logger.info("%s: skipped" % path)
            os.remove(path) # For disc space reasons
            return xml_dicts
        elif os.path.isdir(path):
            _logger.exception("It's a directory, not a file/attachment")
        else:
            _logger.exception("Path %s doesn't exists!" % path)

    def _get_xml_pairs(self,attachments):
        dir_temp = tempfile.gettempdir()
        xml_pairs = []
        # Start importing
        for attachment in attachments:
            fname = attachment['fname']
            content = base64.b64decode(attachment['content'])
            attach_path = os.path.join(dir_temp, fname)
            with open(attach_path, "wb") as attach_file:
                attach_file.write(content)
            for result in self.get_xml_dict_from_attachment(attach_path):
                xml_pairs.append(result)
        return xml_pairs

    def get_dict_from_compressed_file(self, path, uncompressed_files_attach):
        if os.path.isfile(path):
            for path in self.get_xml_paths_from_compressed(path):
                with open(path, "r") as xml:
                    xml_string = ""
                    for line in xml:
                        xml_string += line
                    uncompressed_files_attach.append({'fname': path[path.rfind(os.sep)+1:], 
                                                    'content' : base64.b64encode(xml_string.encode('utf-8'))})
    
    def get_uncompressed_files(self,attachments):
        """
        Return all files compressed in a file.

        Args:
            attachments (dict): dict with filename and b64 file encoded

        Returns:
            [list]: Uncompressed files in format {'fname': file_name, 'content': b64_content }
        """        
        dir_temp = tempfile.gettempdir()
        uncompressed_files_attach = []
        for attachment in attachments:
            fname = attachment['fname']
            content = base64.b64decode(attachment['content'])
            attach_path = os.path.join(dir_temp, fname)
            with open(attach_path, "wb") as attach_file:
                attach_file.write(content)  
            self.get_dict_from_compressed_file(attach_path,uncompressed_files_attach) 
        return uncompressed_files_attach    
