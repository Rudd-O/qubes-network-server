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
from datetime import datetime

import sys
import libvirt
import pipes

from qubes.qubes import QubesProxyVm as OriginalQubesProxyVm
from qubes.qubes import register_qubes_vm_class,vmm,dry_run
from qubes.qubes import defaults,system_path,vm_files
from qubes.qubes import QubesVmCollection,QubesException


yum_proxy_ip = '10.137.255.254'
yum_proxy_port = '8082'


class QubesProxyVm(OriginalQubesProxyVm):

    def write_iptables_qubesdb_entry(self):
        self.qdb.rm("/qubes-iptables-domainrules/")
        iptables =  "# Generated by Qubes Core on {0}\n".format(datetime.now().ctime())
        iptables += "*filter\n"
        iptables += ":INPUT DROP [0:0]\n"
        iptables += ":FORWARD DROP [0:0]\n"
        iptables += ":OUTPUT ACCEPT [0:0]\n"
        iptables += ":PR-QBS-FORWARD - [0:0]\n"

        # Strict INPUT rules
        iptables += "-A INPUT -i vif+ -p udp -m udp --dport 68 -j DROP\n"
        iptables += "-A INPUT -m conntrack --ctstate RELATED,ESTABLISHED " \
                    "-j ACCEPT\n"
        iptables += "-A INPUT -p icmp -j ACCEPT\n"
        iptables += "-A INPUT -i lo -j ACCEPT\n"
        iptables += "-A INPUT -j REJECT --reject-with icmp-host-prohibited\n"

        iptables += "-A FORWARD -m conntrack --ctstate RELATED,ESTABLISHED " \
                    "-j ACCEPT\n"
        # Allow dom0 networking
        iptables += "-A FORWARD -i vif0.0 -j ACCEPT\n"
        # Engage in firewalling for VMs
        iptables += "-A FORWARD -j PR-QBS-FORWARD\n"
        # Deny inter-VMs networking
        iptables += "-A FORWARD -i vif+ -o vif+ -j DROP\n"
        iptables += "COMMIT\n"
        self.qdb.write("/qubes-iptables-header", iptables)

        vms = [vm for vm in self.connected_vms.values()]
        vms_rulesets = []
        for vm in vms:
            vm_iptables = ""

            iptables="*filter\n"
            conf = vm.get_firewall_conf()

            xid = vm.get_xid()
            if xid < 0: # VM not active ATM
                continue

            ip = vm.ip
            if ip is None:
                continue

            # Anti-spoof rules are added by vif-script (vif-route-qubes), here we trust IP address

            accept_action = "ACCEPT"
            reject_action = "REJECT --reject-with icmp-host-prohibited"

            if conf["allow"]:
                default_action = accept_action
                rules_action = reject_action
            else:
                default_action = reject_action
                rules_action = accept_action

            for rule in conf["rules"]:
                if getattr(vm, "static_ip", None) and rule["address"].startswith("from-"):
                    ruletext = "-s {0} -d {1}".format(rule["address"][len("from-"):], ip)
                    if rule["netmask"] != 32:
                        ruletext += "/{0}".format(rule["netmask"])

                    if rule["proto"] is not None and rule["proto"] != "any":
                        ruletext += " -p {0}".format(rule["proto"])
                        if rule["portBegin"] is not None and rule["portBegin"] > 0:
                            ruletext += " --dport {0}".format(rule["portBegin"])
                            if rule["portEnd"] is not None and rule["portEnd"] > rule["portBegin"]:
                                ruletext += ":{0}".format(rule["portEnd"])

                    ruletext += " -j {0}\n".format(rules_action)
                    iptables += "-A PR-QBS-FORWARD " + ruletext
                    vm_iptables += "-A FORTRESS-INPUT " + ruletext
                    continue

                iptables += "-A PR-QBS-FORWARD -s {0} -d {1}".format(ip, rule["address"])
                if rule["netmask"] != 32:
                    iptables += "/{0}".format(rule["netmask"])

                if rule["proto"] is not None and rule["proto"] != "any":
                    iptables += " -p {0}".format(rule["proto"])
                    if rule["portBegin"] is not None and rule["portBegin"] > 0:
                        iptables += " --dport {0}".format(rule["portBegin"])
                        if rule["portEnd"] is not None and rule["portEnd"] > rule["portBegin"]:
                            iptables += ":{0}".format(rule["portEnd"])

                iptables += " -j {0}\n".format(rules_action)

            if conf["allowDns"] and self.netvm is not None:
                # PREROUTING does DNAT to NetVM DNSes, so we need self.netvm.
                # properties
                iptables += "-A PR-QBS-FORWARD -s {0} -p udp -d {1} --dport 53 -j " \
                            "ACCEPT\n".format(ip,self.netvm.gateway)
                iptables += "-A PR-QBS-FORWARD -s {0} -p udp -d {1} --dport 53 -j " \
                            "ACCEPT\n".format(ip,self.netvm.secondary_dns)
                iptables += "-A PR-QBS-FORWARD -s {0} -p tcp -d {1} --dport 53 -j " \
                            "ACCEPT\n".format(ip,self.netvm.gateway)
                iptables += "-A PR-QBS-FORWARD -s {0} -p tcp -d {1} --dport 53 -j " \
                            "ACCEPT\n".format(ip,self.netvm.secondary_dns)
            if conf["allowIcmp"]:
                iptables += "-A PR-QBS-FORWARD -s {0} -p icmp -j ACCEPT\n".format(ip)
                if getattr(vm, "static_ip", None):
                    iptables += "-A PR-QBS-FORWARD -d {0} -p icmp -j ACCEPT\n".format(ip)
                    vm_iptables += "-A FORTRESS-INPUT -d {0} -p icmp -j ACCEPT\n".format(ip)
            if conf["allowYumProxy"]:
                iptables += "-A PR-QBS-FORWARD -s {0} -p tcp -d {1} --dport {2} -j ACCEPT\n".format(ip, yum_proxy_ip, yum_proxy_port)
            else:
                iptables += "-A PR-QBS-FORWARD -s {0} -p tcp -d {1} --dport {2} -j DROP\n".format(ip, yum_proxy_ip, yum_proxy_port)

            iptables += "-A PR-QBS-FORWARD -s {0} -j {1}\n".format(ip, default_action)
            if getattr(vm, "static_ip", None):
                iptables += "-A PR-QBS-FORWARD -d {0} -j {1}\n".format(ip, default_action)
                vm_iptables += "-A FORTRESS-INPUT -d {0} -j {1}\n".format(ip, default_action)
                vm_iptables += "COMMIT\n"
                vms_rulesets.append((vm, vm_iptables))
            iptables += "COMMIT\n"
            self.qdb.write("/qubes-iptables-domainrules/"+str(xid), iptables)

        # no need for ending -A PR-QBS-FORWARD -j DROP, cause default action is DROP

        self.write_netvm_domid_entry()

        self.rules_applied = None
        self.qdb.write("/qubes-iptables", 'reload')

        for vm, ruleset in vms_rulesets:
            shell_ruleset = "echo Adjusting firewall rules to: >&2\n"
            shell_ruleset += "echo %s >&2\n" % pipes.quote(ruleset.strip())
            shell_ruleset += "data=$(iptables-save -t filter)\n"
            shell_ruleset += 'if ! echo "$data" | grep -q -- "^:FORTRESS-INPUT" ; then\n'
            shell_ruleset += '    data=$(echo "$data" | sed "s/^:INPUT/:FORTRESS-INPUT - [0:0]\\n\\0/")\n'
            shell_ruleset += "fi\n"
            shell_ruleset += 'if ! echo "$data" | grep -q -- "-A INPUT -j FORTRESS-INPUT" ; then\n'
            shell_ruleset += '    data=$(echo "$data" | sed -r "s|-A INPUT -i vif. -j REJECT --reject-with icmp-host-prohibited|-A INPUT -j FORTRESS-INPUT\\n\\0|")\n'
            shell_ruleset += "fi\n"
            shell_ruleset += 'data=$(echo "$data" | grep -v ^COMMIT$)\n'
            shell_ruleset += 'data=$(echo "$data" | grep -v -- "-A FORTRESS-INPUT")\n'
            shell_ruleset += 'data="$data\n"%s\n' % pipes.quote(ruleset)
            shell_ruleset += 'echo "$data" | iptables-restore -T filter\n'
            vm.adjust_own_firewall_rules(shell_ruleset)


register_qubes_vm_class(QubesProxyVm)