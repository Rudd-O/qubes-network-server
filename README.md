# Qubes network server

This software lets you turn your [Qubes OS 4.2](https://www.qubes-os.org/) machine into
a network server, enjoying all the benefits of Qubes OS (isolation, secure
inter-VM process communication, ease of use) with none of the drawbacks
of setting up your own Xen server.

This release is only intended for use with Qubes OS 4.2.  Older Qubes OS releases
will not support it.  For Qubes OS 4.1, check branch `r4.1`.

## Why?

Qubes OS is a magnificent operating system.  That said, there are many use cases its networking
model does not work well for:

* Remote management of Qubes OS instances.  Vanilla Qubes OS cannot
  easily be managed remotely.  A better networking model would allow
  for orchestration tools — such as
  [Ansible Qubes](https://github.com/Rudd-O/ansible-qubes) — to manage
  entire Qubes OS deployments, all of their VMs, and even minutiae
  within each VM.
* Anything that involves a secure server, serving data to people or
  machines, simply cannot be done under vanilla Qubes OS.
* As an automated integration testing system.  Qubes OS would be
  phenomenal for this, and its automation tools would make it
  extremely easy to bring up and tear down entire environments.
  If only those environments could network with each other securely!

### The traditional Qubes networking model

The traditional Qubes OS networking model contemplates a client-only
use case.  User VMs (AppVMs or StandaloneVMs) are attached to ProxyVMs,
which give the user control over outbound connections taking place from
user VMs.  ProxyVMs in turn attach to NetVMs, which provide outbound
connectivity for ProxyVMs and other user VMs alike.

![Standard Qubes OS network model](./doc/Standard%20Qubes%20OS%20network%20model.png)

No provision is made for running a server in a virtualized environment,
such that the server's ports are accessible by (a) other VMs (b) machines
beyond the perimeter of the NetVM.  To the extent that such a thing is
possible, it is only possible by painstakingly maintaining firewall rules
for multiple VMs, which need to carefully override the existing firewall
rules, and require careful thought not to open the system to unexpected
attack vectors.  The Qubes OS user interface provides no help either.

### The Qubes network server networking model

Qubes network server builds on that.

![Qubes network server model](./doc/Qubes%20network%20server%20model.png)

With the Qubes network server software, it becomes possible to make
network servers in user VMs available to other machines, be them
peer VMs in the same Qubes OS system or machines connected to
a physical link shared by a NetVM.  Those network server VMs also
obey the Qubes OS outbound firewall rules controls, letting you run
services with outbound connections restricted.

This is all, of course, opt-in, so the standard Qubes OS network security
model remains in effect until you decide to enable the feature on any
particular VM.

The only drawback of this method is that it requires you to attach
VMs meant to be exposed to the network directly to a NetVM, rather than
through a ProxyVM.  VMs exposed through a ProxyVM will not be visible
to machines on the same network as the NetVM.

## How to use this software

Once installed (**see below for installation instructions**), usage of
the software is straightforward.

These sample instructions assume:

* the software is properly installed (see below),
* you understand the distinction between dom0 and qubes,
* you already have an AppVM VM set up, named `testvm`, and
* your `sys-net` VM is attached to a network with subnet `192.168.16.0/24`
  — this, of course, may vary depending on your local router configuration.

*Do not proceed any further if you do not yet meet these requirements.*
  
First, **attach** the VM you want to expose to the network
to a NetVM that has an active network connection:

`qvm-prefs -s testvm netvm sys-net`

Set an **IP** address on `testvm` belonging to the same LAN as `sys-net`:

`qvm-prefs -s testvm ip 192.168.16.25`

**Restart** the `testvm` VM if it was already running.

**Configure** routing method; to enable the network server feature for
your `testvm` VM, all you have to do in your AdminVM (`dom0`) is run
the following command:

`qvm-features testvm routing-method forward`

Now `testvm` is exposed to the network with address `192.168.16.25`, as well
as to other VMs attached to `NetVM`.

Finally, adjust **input firewall rules** on `testvm` to permit traffic coming from
machines in your LAN.  `testvm` will have the standard Qubes OS firewall
rules stopping inbound traffic.  To solve that issue, you can use a sample
rule in `testvm`:

```
sudo nft add rule qubes custom-input ip saddr 192.168.16.0/24 ct state new,established,related counter accept
```

You can make these rules persistent by [following instructions on the Qubes
OS firewall documentation page](https://www.qubes-os.org/doc/firewall/#enabling-networking-between-two-qubes).
Note that you do not need to change the `custom-forward` chain at all
on any qube -- Qubes network server manages that for you transparently
in your `NetVM`.

Here are documents that will help you take advantage of Qubes network server:

* [Setting up your first server](doc/Setting up your first server.md)
* [Setting up an SSH server](doc/Setting up an SSH server.md)

## Setup

Package installation consists of two steps (**the package creation instructions are below**):

1. Deploy the `qubes-core-admin-addon-network-server` RPM to your `dom0`.
2. Deploy the `qubes-network-server` RPM to the TemplateVM backing your
   NetVM (which must be a Fedora instance).  If your NetVM is a StandaloneVM,
   then you must deploy this RPM to the NetVM directly.

After that, to make it all take effect:

1. Power off the TemplateVM.
2. Reboot the NetVM.

You're done.  You can verify that the necessary component is running by launching
a terminal in your NetVM, then typing the following:

```
systemctl status qubes-routing-manager.service
```

The routing manager should show as `enabled` and `active` in the terminal
output, with no errors.  You can now follow the usage instructions above.

### How to build the packages to install

You will first build the `qubes-core-admin-addon-network-server` RPM.

To build this package, you will need to use a `chroot` jail containing
a Fedora installation of the exact same release as your `dom0` (Fedora 37
for Qubes 4.2).  You can do this using `toolbox` (for maximum safety
within a disposable qube):

```
dnf install -y toolbox
toolbox create -r 37
toolbox enter fedora-toolbox-37
# Bam!  You have a shell in an isolated Fedora 37 instance now.
```

Within the toolbox, all your normal files from your home directory are
visible.  Change into the directory that contains this source code,
then type `make rpm`.  You may have to install some packages within your
toolbox -- use `dnf install git rpm-build make coreutils tar gawk findutils systemd systemd-rpm-macros`
to get the minimum dependency set installed.  Don't worry -- nothing within
the toolbox affects

Once built, in the source directory you will find the
`qubes-core-admin-addon-network-server` RPM built for your dom0.

To build the `qubes-network-server` RPM that goes in your template, you
can simply use a DisposableVM running the same Fedora release as your NetVM.
Build said package as follows:

```
# Dependencies
dnf install git rpm-build make coreutils tar gawk findutils systemd systemd-rpm-macros
# Source code
cd /path/to/qubes-network-server
# <make sure you are in the correct branch now>
make rpm
```

The process will output a `qubes-network-server-*.noarch.rpm` in the
directory where it ran.  Fish it out and copy it into the template where
you'll install it.

You can power off the DisposableVM now.

### Upgrading to new / bug-fixing releases

Follow the same procedures as above, but when asked to install the packages
with `rpm -ivh`, change it to `rpm -Uvh` (uppercase U for upgrade).

Always restart your NetVMs between upgrades.

## Theory of operation

Qubes OS relies on layer 3 (IP) routing.  VMs in its networked tree send traffic through
their default route interfaces, which upstream VMs receive and masquerade out of their own
default route interfaces.

Qubes network server slightly changes this when a VM gets its `routing-method` feature set
to `forward`.  As soon as the feature is enabled with that value, or the VM in question
boots up, Qubes network server:

* enables ARP neighbor proxying (and, if using IPv6, NDP neighbor proxying) in the NetVM
* sets firewall rules in the NetVM that neuter IP masquerading on traffic coming from
  the networked VM
* sets firewall rules in the NetVM that allow traffic from other VMs to reach the
  networked VM, neutering the default Qubes OS rule that normally prohibits this

The above have the effect of exposing the networked VM to:

* other AppVMs attached to the same NetVM
* other machines attached to the same physical network the NetVM is attached to

Now all machines in the same LAN will be able to reach the networked VM.
Here is a step-by-step explanation of how IP traffic to and from the networked
VM happens, when the `routing-method` is set to `forward` on the networked VM:

1. Machine in LAN asks for the MAC address of the networked VM's IP address.
2. NetVM sees the ARP/NDP request and responds by proxying it to the networked VM.
3. Networked VM replies to the ARP/NDP request back to the NetVM.
4. NetVM relays the ARP/NDP reply back to the network, but substitutes its own
   MAC address in the reply.
5. Machine in LAN sends local IP packet to the IP of the networked VM's IP address,
   but destined to the MAC address of the NetVM.
6. The NetVM sees the IP packet, and routes it to the networked VM.
7. The Networked VM receives the IP packet.
8. If the networked VM needs to respond, it sends an IP packet back to the
   machine in LAN.
9. NetVM notices packet comes from the networked VM, and instead of masquerading it,
   it lets the packet through unmodified, with the source IP address of the
   networked VM.

The end result is practical networking with no need to set up routing tables on
machines attempting to access the networked VM.

Of course, if you want machines in the LAN to have access to the networked VM, you
must still set an appropriate `ip` preference on the networked VM.  For example, if
your physical LAN had subnet `1.2.3.0/24`, and you want machines in your physical LAN
to connect to a networked VM, you must set the `ip` preference of the networked VM
to a previously-unused IP within the range `1.2.3.1` and `1.2.3.255`.  Failing that,
you must assign a host-specific route on the source machine which uses the NetVM
as the gateway, and uses the IP address of the networked VM (see `qvm-prefs` output)
as the destination address.

## Limitations

* HVMs are not supported at all at this time.  This will change over time, and
  you can help it change faster by submitting a pull request with HVM support.
* Interposing a ProxyVM between a networked VM and the NetVM is not currently
  supported.  This is implementable in principle, but would require a recursive
  walk that encompasses the entire network link from NetVM through intermediate
  ProxyVMs.

## Troubleshooting

The actions that the `qubes-routing-manager` service performs are logged to the journal
of the NetVM where the `qubes-routing-manager` service is running.

In case of problems, tailing the journal (`sudo journalctl -fa`) on the NetVM will be
extremely useful to figure out what the problem is.
