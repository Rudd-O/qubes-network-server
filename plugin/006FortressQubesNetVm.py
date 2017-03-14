#!/usr/bin/python2
# -*- coding: utf-8 -*-
#
# The Qubes OS Project, http://www.qubes-os.org
#
# Copyright (C) 2010  Joanna Rutkowska <joanna@invisiblethingslab.com>
# Copyright (C) 2013  Marek Marczykowski <marmarek@invisiblethingslab.com>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#
#
import sys
import libvirt

from qubes.qubes import QubesNetVm as OriginalQubesNetVm
from qubes.qubes import register_qubes_vm_class,vmm,dry_run
from qubes.qubes import defaults,system_path,vm_files
from qubes.qubes import QubesVmCollection,QubesException


class QubesNetVm(OriginalQubesNetVm):

    @property
    def netmask(self):
        if getattr(self, "static_ip"):
            return "255.255.255.255"
        return self.__netmask

    @property
    def network(self):
        return self.__network


register_qubes_vm_class(QubesNetVm)
