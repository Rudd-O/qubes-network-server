#!/usr/bin/python3

"""
This program reads the /qubes-firewall/{ip}/qubes-routing-method file
for any firewall configuration, then configures the network to obey
the routing method for the VM.  If the routing method is "masquerade",
then nothing happens.  If, however, the routing method is "forward",
then VM-specific rules are enacted in the VM's attached NetVM to allow
traffic coming from other VMs and the outside world to reach this VM.
"""

import glob
import logging
import os
import socket

import qubesdb

from qubesroutingmanager import setup_plain_forwarding_for_address


FORWARD_ROUTING_METHOD = "forward"


def _s(v):
    if isinstance(v, bytes):
        return v.decode("utf-8")
    return v


class AdjunctWorker(object):
    def __init__(self):
        self.qdb = qubesdb.QubesDB()

    @staticmethod
    def is_ip6(addr):
        return addr.count(":") > 0

    def setup_proxy_arp_ndp(self, enabled, family):
        # If any of the IP addresses is assigned the forward routing method,
        # then enable proxy ARP/NDP on the upstream interfaces, so that the
        # interfaces in question will impersonate the IP addresses in question.
        # Ideally, this impersonation would be exclusively done for the
        # specific IP addresses in question, but it is not clear to me how
        # to cause this outcome to take place.
        if family == 6:
            globber = "/proc/sys/net/ipv6/conf/*/proxy_ndp"
            name = "proxy NDP"
        elif family == 4:
            globber = "/proc/sys/net/ipv4/conf/*/proxy_arp"
            name = "proxy ARP"
        else:
            return

        if enabled:
            action = "Enabling"
            val = "1\n"
        else:
            action = "Disabling"
            val = "0\n"

        matches = glob.glob(globber)
        for m in matches:
            iface = m.split("/")[6]
            if iface in ("all", "lo") or iface.startswith("vif"):
                # No need to enable it for "all", or VIFs, or loopback.
                continue
            with open(m, "w+") as f:
                oldval = f.read()
                if oldval != val:
                    logging.info("%s %s on interface %s.", action, name, iface)
                    f.seek(0)
                    f.write(val)

    def handle_addr(self, addr):
        # Setup plain forwarding for this specific address.
        routing_method = _s(self.qdb.read("/qubes-routing-method/{}".format(addr)))
        setup_plain_forwarding_for_address(
            addr,
            routing_method == FORWARD_ROUTING_METHOD,
            6 if self.is_ip6(addr) else 4,
        )

        # Manipulate proxy ARP for all known addresses.
        methods = [
            (_s(k).split("/")[2], _s(v))
            for k, v in self.qdb.multiread("/qubes-routing-method/").items()
        ]
        mmethods = {
            4: [m[1] for m in methods if not self.is_ip6(m[0])],
            6: [m[1] for m in methods if self.is_ip6(m[0])],
        }
        for family, methods in mmethods.items():
            self.setup_proxy_arp_ndp(
                FORWARD_ROUTING_METHOD in methods,
                family,
            )

    def list_targets(self):
        return set(_s(t).split("/")[2] for t in self.qdb.list("/qubes-routing-method/"))

    def sd_notify(self, state):
        """Send notification to systemd, if available"""
        # based on sdnotify python module
        if "NOTIFY_SOCKET" not in os.environ:
            return
        addr = os.environ["NOTIFY_SOCKET"]
        if addr[0] == "@":
            addr = "\0" + addr[1:]
        try:
            sock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
            sock.connect(addr)
            sock.sendall(state.encode())
        except BaseException:
            # generally ignore error on systemd notification
            pass

    def main(self):
        logging.basicConfig(level=logging.INFO)
        self.qdb.watch("/qubes-routing-method/")
        for source_addr in self.list_targets():
            self.handle_addr(source_addr)
        self.sd_notify("READY=1")
        try:
            for watch_path in iter(self.qdb.read_watch, None):
                # ignore writing rules itself - wait for final write at
                # source_addr level empty write (/qubes-firewall/SOURCE_ADDR)
                watch_path = _s(watch_path)
                if watch_path.count("/") != 2:
                    continue
                source_addr = watch_path.split("/")[2]
                self.handle_addr(source_addr)
        except OSError:  # EINTR
            # signal received, don't continue the loop
            return
