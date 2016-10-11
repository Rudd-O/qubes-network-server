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

import datetime
import base64
import hashlib
import fcntl
import logging
import lxml.etree
import os
import pipes
import re
import shutil
import subprocess
import sys
import textwrap
import time
import uuid
import xml.parsers.expat
import signal
from qubes import qmemman
from qubes import qmemman_algo
import libvirt

from qubes.qubes import QubesException
from qubes.qubes import QubesVm as OriginalQubesVm
from qubes.qubes import register_qubes_vm_class
from qubes.qubes import dry_run


fw_encap = textwrap.dedent("""
    mkdir -p /run/fortress/firewall
    f=$(mktemp --tmpdir=/run/fortress/firewall)
    cat > "$f"
    chmod +x "$f"
    bash -e "$f"
    ret=$?
    rm -f "$f"
    exit $ret
""")


def locked(programtext):
    if not programtext.strip():
        return programtext
    return "(\nflock 200\n" + programtext + "\n) 200>/var/run/xen-hotplug/vif-lock\n"


def logger(programtext):
    if not programtext.strip():
        return programtext
    return "exec 1> >(logger -s -t fortress) 2>&1\n" + programtext


class QubesVm(OriginalQubesVm):

    def get_attrs_config(self):
        attrs = OriginalQubesVm.get_attrs_config(self)
        attrs["static_ip"] = {
            "attr": "static_ip",
            "default": None,
            "order": 70,
            "save": lambda: str(getattr(self, "static_ip")) if getattr(self, "static_ip") is not None else 'none'
        }
        return attrs

    @property
    def ip(self):
        if self.netvm is not None:
            if getattr(self, "static_ip") is not None:
                return getattr(self, "static_ip")
            return self.netvm.get_ip_for_vm(self.qid)
        else:
            return None

    @property
    def netmask(self):
        if self.netvm is not None:
            if getattr(self, "static_ip") is not None:
                # Netmasks for VMs that have a static IP are always host-only.
                return "255.255.255.255"
            return self.netvm.netmask
        else:
            return None

    def start(self, verbose = False, preparing_dvm = False, start_guid = True,
              notify_function = None, mem_required = None):
        if dry_run:
            return
        xid = OriginalQubesVm.start(self, verbose, preparing_dvm, start_guid, notify_function, mem_required)
        if not preparing_dvm:
            self.adjust_proxy_arp(verbose=verbose, notify_function=notify_function)
            self.adjust_own_firewall_rules()
        return xid

    def unpause(self):
        self.log.debug('unpause()')
        if dry_run:
            return

        if not self.is_paused():
            raise QubesException ("VM not paused!")

        self.libvirt_domain.resume()
        self.adjust_proxy_arp()
        self.adjust_own_firewall_rules()

    def attach_network(self, verbose = False, wait = True, netvm = None):
        self.log.debug('attach_network(netvm={!r})'.format(netvm))
        if dry_run:
            return
        ret = OriginalQubesVm.attach_network(self, verbose, wait, netvm)
        self.adjust_proxy_arp(verbose)
        return ret

    def adjust_proxy_arp(self, verbose = False, notify_function=None):

        def collect_downstream_vms(vm, vif):
            if not hasattr(vm, "connected_vms"):
                return list()
            vms_below_me = list(vm.connected_vms.values())
            vms_below_me = [(vm, vif if vif else vm.vif) for vm in vms_below_me]
            for v, vif in vms_below_me:
                vms_below_me.extend(collect_downstream_vms(v, vif))
            return vms_below_me

        def addroute(ip, dev, netmask):
            # This function adds routes and proxy ARP entries for the IP pointed at the
            # device that the VM (IP) is behind.
            dev = dev.replace("+", "0")
            return "\n".join([
                "if ! ip route | grep -qF %s\\ dev\\ %s ; then" % (pipes.quote(ip), pipes.quote(dev)),
                "ip route replace %s/%s dev %s metric 20001" % (pipes.quote(ip), pipes.quote(netmask), pipes.quote(dev)),
                "fi",
                "echo 1 > /proc/sys/net/ipv4/conf/%s/forwarding" % (pipes.quote(dev),),
                "echo 1 > /proc/sys/net/ipv4/conf/%s/proxy_arp" % (pipes.quote(dev),),
                "for dev in `ip link | awk -F ':' '/^[0-9]+: (eth|en|wl)/ { print $2 }'`",
                "do",
                "    ip neigh add proxy %s dev $dev" % (pipes.quote(ip),),
                "done",
            ])

        class addfwrule(object):
            rules = None
            addrule = textwrap.dedent("""
            declare -A savedrules
            addrule() {
                local table="$1"
                local chain="$2"
                local rule="$3"
                local before="$4"

                if [ "${savedrules[$table]}" == "" ] ; then
                    savedrules["$table"]=$(iptables-save -t "$table")
                fi

                if echo "${savedrules[$table]}" | grep -q :"${chain}" ; then
                    true
                else
                    savedrules["$table"]=$(
                        echo "${savedrules[$table]}" | while read x
                        do
                            echo "$x"
                            if [ "$x" == '*'"$table" ]
                            then
                                echo "${table}: new chain ${chain}" >&2
                                echo ":${chain} - [0:0]"
                            fi
                        done
                    )
                fi

                if [ "x$before" == "x" ] ; then
                    before=COMMIT
                elif [ "x$before" == "xbeginning" ] ; then
                    before=beginning
                else
                    before="-A $chain $before"
                fi

                if [ "$before" != "beginning" ] && echo "${savedrules[$table]}" | grep -qF -- "-A $chain $rule" ; then
                    return
                fi

                local echoed=false
                savedrules["$table"]=$(
                    echo "${savedrules[$table]}" | while read x
                    do
                        if [ "beginning" == "$before" -a "$echoed" == "false" ] && echo "$x" | grep -q '^-A '
                        then
                            echo "${table}: adding rule -A ${chain} ${rule} to the beginning" >&2
                            echo "-A $chain $rule"
                            echoed=true
                        elif [ "$x" == "$before" ]
                        then
                            echo "${table}: adding rule -A ${chain} ${rule} before ${before}" >&2
                            echo "-A $chain $rule"
                        fi
                        if [ "beginning" == "$before" -a "$x" == "-A $chain $rule" ]
                        then
                            true
                        else
                            echo "$x"
                        fi
                    done
                )
            }
            flushrules() {
                local table="$1"
                local chain="$2"

                if [ "${savedrules[$table]}" == "" ] ; then
                    savedrules["$table"]=$(iptables-save -t "$table")
                fi

                savedrules["$table"]=$(
                    echo "${savedrules[$table]}" | while read x
                    do
                        if echo "$x" | grep -q "^-A $chain " ; then
                            echo "${table}: flushing rule $x" >&2
                        else
                            echo "$x"
                        fi
                    done
                )
            }
            addfwrules() {
                # This function creates the FORTRESS-ALLOW-FORWARD filter chain
                # and adds rules permitting forwarding of traffic
                # sent by the VM and destined to the VM.
                local ipnetmask="$1"
                addrule filter FORWARD "-j FORTRESS-ALLOW-FORWARD" "-i vif+ -o vif+ -j DROP"
                addrule filter FORTRESS-ALLOW-FORWARD "-s $ipnetmask -j ACCEPT"
                addrule filter FORTRESS-ALLOW-FORWARD "-d $ipnetmask -j ACCEPT"
            }
            addprrules() {
                # This function creates the FORTRESS-SKIP-MASQ nat chain
                # and the FORTRESS-ANTISPOOF raw chain
                # and adds rules defeating masquerading and anti-spoofing
                # for the IP (machine) so long as it comes from / goes to
                # the VIF that the machine is behind.
                local ipnetmask="$1"
                local vif="$2"
                addrule nat POSTROUTING "-j FORTRESS-SKIP-MASQ" "-j MASQUERADE"
                addrule nat FORTRESS-SKIP-MASQ "-s $ipnetmask -j ACCEPT"
                addrule nat FORTRESS-SKIP-MASQ "-d $ipnetmask -j ACCEPT"
                addrule raw PREROUTING "-j FORTRESS-ANTISPOOF" beginning
                addrule raw FORTRESS-ANTISPOOF "-s $ipnetmask -j ACCEPT"
            }
            commitrules() {
                for table in "${!savedrules[@]}" ; do
                    echo "${savedrules[$table]}" | iptables-restore -T "$table"
                done
            }
            flushrules filter FORTRESS-ALLOW-FORWARD
            flushrules nat FORTRESS-SKIP-MASQ
            flushrules raw FORTRESS-ANTISPOOF
            """)

            def _add(self, ip, dev, netmask, typ):
                netmask = sum([bin(int(x)).count('1') for x in netmask.split('.')])
                dev = dev.replace("+", "0")
                text = ""
                if typ == "forward":
                    text += "addfwrules %s/%s\n" % (pipes.quote(ip), netmask)
                elif typ == "postrouting":
                    text += "addprrules %s/%s %s\n" % (pipes.quote(ip), netmask, pipes.quote(dev))
                if not self.rules:
                    self.rules = []
                self.rules.append(text)

            def addfw(self, ip, dev, netmask):
                return self._add(ip, dev, netmask, "forward")

            def addpr(self, ip, dev, netmask):
                return self._add(ip, dev, netmask, "postrouting")

            def commit(self):
                if not self.rules:
                    return ""
                return self.addrule + "\n".join(self.rules) + "\ncommitrules\n"

        programs = []
        staticipvms = []
        ruler = addfwrule()

        # For every VM downstream of mine.
        for vm, vif in collect_downstream_vms(self, None):
            # If the VM is running, and it has an associated VIF
            # and it has a static IP:
            if vm.static_ip and vif and vm.is_running():
                staticipvms.append(vm.name)
                # Add ip neighs of and routes to the VM.
                # pointed at the VIF that the VM is behind.
                programs.append(addroute(vm.ip, vif, vm.netmask))
                # Add prerouting and postrouting rules for the VM
                # that defeat masquerading and anti-spoofing.
                ruler.addpr(vm.ip, vif, vm.netmask)
                # If I am a NetVM, then, additionally.
                if self.type == "NetVM":
                    # Add filter rules for the VM
                    # that allow it to communicate with other VMs.
                    ruler.addfw(vm.ip, vif, vm.netmask)
        if ruler.commit():
            programs.append(ruler.commit())

        if not programs:
            pass
        elif not self.is_running() or self.is_paused():
            msg = "Not running routing programs on %s (VM is paused or off)" % (self.name,)
            if notify_function:
                notify_function("info", msg)
            elif verbose:
                print >> sys.stderr, "-->", msg
        else:
            programs = logger(locked("\n".join(programs)))
            if not staticipvms:
                msg = "Enabling preliminary routing configuration on %s" % (self.name,)
            else:
                msg = "Enabling routing of %s on %s" % (", ".join(staticipvms), self.name)
            if notify_function:
                notify_function("info", msg)
            elif verbose:
                print >> sys.stderr, "-->", msg
                # for x in programs.splitlines(False):
                #     print >> sys.stderr, "---->", x
            p = self.run(fw_encap, user="root", gui=False, wait=True, passio_popen=True, autostart=False)
            p.stdin.write(programs)
            p.stdin.close()
            p.stdout.read()
            retcode = p.wait()
            if retcode:
                msg = "Routing commands on %s failed with return code %s" % (self.name, retcode)
                if notify_function:
                    notify_function("error", msg)
                elif verbose:
                    print >> sys.stderr, "-->", msg

        if self.netvm:
            self.netvm.adjust_proxy_arp(
                verbose=verbose,
                notify_function=notify_function
            )

    def adjust_own_firewall_rules(self, ruleset_script=None):
        ruleset_script_path = os.path.join(
            os.path.dirname(self.firewall_conf),
            "firewall.conf.sh"
        )
        f = open(ruleset_script_path, "a+b")
        fcntl.flock(f.fileno(), fcntl.LOCK_EX)
        try:
            if ruleset_script:
                f.seek(0)
                f.truncate(0)
                f.write(ruleset_script)
                f.flush()
            else:
                f.seek(0)
                ruleset_script = f.read()

            if ruleset_script:
                try:
                    ruleset_script = logger(locked(ruleset_script))
                    p = self.run(fw_encap, user="root", gui=False, wait=True, passio_popen=True, autostart=False)
                    p.stdin.write(ruleset_script)
                    p.stdin.close()
                    p.stdout.read()
                    retcode = p.wait()
                    f.seek(0)
                    f.truncate(0)
                    f.flush()
                except QubesException, e:
                    pass

        finally:
            f.close()

register_qubes_vm_class(QubesVm)
