#Qubes network server

This software lets you turn your [Qubes OS](https://www.qubes-os.org/) machine into a network server, enjoying all the benefits of Qubes OS (isolation, secure inter-VM process communication, ease of use) with none of the drawbacks of setting up your own Xen server.

##Why?

Qubes OS is a magnificent operating system, but there are so many use cases that its networking model cannot crack:

* As an automated integration testing system.  Qubes OS would be
  phenomenal for this, and its automation tools would make it
  extremely easy to bring up and tear down entire environments.
  If only those environments could network with each other securely!
* Remote management of Qubes OS instances.  Vanilla Qubes OS cannot
  easily be managed remotely.  A better networking model would allow
  for orchestration tools — such as
  [Ansible Qubes](https://github.com/Rudd-O/ansible-qubes) — to manage
  entire Qubes OS deployments, all of their VMs, and even minutiae
  within each VM.
* Anything that involves a secure server, serving data to people or
  machines, simply cannot be done under vanilla Qubes OS.

##Enhanced networking model

The traditional Qubes OS networking model contemplates a client-only
use case.  User VMs (AppVMs or StandaloneVMs) are attached to ProxyVMs,
which give the user control over outbound connections taking place from
user VMs.  ProxyVMs in turn attach to NetVMs, which provide outbound
connectivity for ProxyVMs and other user VMs alike.

![Standard Qubes OS network model](doc/Standard Qubes OS network model.png?raw=true "Standard Qubes OS network model")

No provision is made for running a server in a virtualized environment,
such that the server's ports are accessible by (a) other VMs (b) machines
beyond the perimeter of the NetVM.  To the extent that such a thing is
possible, it is only possible by painstakingly maintaining firewall rules
for multiple VMs, which need to carefully override the existing firewall
rules, and require careful thought not to open the system to unexpected
attack vectors.  The Qubes OS user interface provides no help either.

Qubes network server changes all that.

![Qubes network server model](doc/Qubes network server model.png?raw=true "Qubes network server model")

With the Qubes network server software, it becomes possible to make
network servers in user VMs available to other machines, be them
peer VMs in the same Qubes OS system or machines connected to
a physical link shared by a NetVM.  You get actual, full, GUI control
over network traffic, both exiting the VM and entering the VM, with
exactly the same Qubes OS user experience you are used to.

This is all, of course, opt-in, so the standard Qubes OS network security
model remains in effect until you decide to share network servers.

##How to use this software

Once installed (see below), usage of the software is straightforward.
Here are documents that will help you take advantage of Qubes
network server:

* [Setting up your first server](doc/Setting up your first server.md)
* [Setting up an SSH server](doc/Setting up an SSH server.md)


##Installation

Installation is extremely easy:

* Prepare an RPM with the `make rpm` command on the local
  directory of your clone.  This creates a file
  `qubes-network-server-*-noarch.rpm` on that directory.
* Copy the prepared RPM to the dom0 of your Qubes OS
  machine.
* Install the RPM in the dom0 with
  `rpm -ivh <RPM file name you just copied>`.
* Restart Qubes Manager, if it is running.
  (Right-click on its notification icon, select *Exit*, then
  relaunch it from the *System* menu.)

Qubes OS does not provide any facility to copy files from
a VM to the dom0.  To work around this, you can use `qvm-run`:

```
qvm-run --pass-io vmwiththerpm 'cat /home/user/path/to/qubes-network-server*rpm' > qns.rpm
```

This lets you fetch the RPM file to the dom0, and save it as `qns.rpm`,
which you can then feed to the `rpm -ivh` command.

### Upgrading to new / bug-fixing releases

Follow the same procedures as above, but when asked to install the package
with `rpm -ivh`, change it to `rpm -Uvh` (uppercase U for upgrade).

## Theory of operation

Qubes OS relies on layer 3 (IP) routing.  VMs in its networked tree send traffic through
their default route interfaces, which upstream VMs receive and masquerade out of their own
default route interfaces.

Qubes network server slightly changes this when a networked VM — a VM which has had its
`static_ip` attribute set with `qvm-static-ip` — exists on the networked tree.  As soon
as a networked VM boots up, Qubes network server:

* sets a static `/32` route on every upstream VM to the networked VM's static IP,
  directing the upstream VMs to route traffic for that IP to their VIFs where
  they may find the networked VM
* enables ARP neighbor proxying for the static IP on every upstream VM, such that
  every upstream VM announces itself to their own upstream VMs (and LAN, in the
  case of NetVMs) as the networked VM 
* sets firewall rules on every upstream VM that allow normal non-masquerading forwarding
  to and from the IP of the networked VM
* (depending on the Qubes firewall policy of the networked VM) sets rules on every
  upstream ProxyVM that allow for certain classes of inbound traffic
* (depending on the Qubes firewall policy of the networked VM) sets rules directly
  on the networked VM that allow for certain classes of inbound traffic

The end result is instantaneous networking — machines upstream from the networked VM,
including machines in the physical LAN, can "see", ping, and connect to the networked
VM, provided that the firewall policy permits it.  You do not need to set up any
special host-only routes on machines trying to access your networked VM — provided
that the static IP is on the same routable subnet as its upstream VM's, Qubes
network server does its magic automatically.

Of course, LAN machines connecting to the networked VM believe that the networked VM
possesses the MAC address of its upstream NetVM (just as if the upstream NetVM had a
second IP address and was serving traffic from it), but in reality, that is just an
illusion created by Qubes network server.  This does have implications for your own
network security policy, in that the networked VM appears (from a MAC perspective)
to share a network card with its upstream NetVM.

## Limitations

* HVMs are not supported at all at this time.  This will change over time, and
  you can help it change faster by submitting a pull request with HVM support.

## Troubleshooting

The actions that the network server software performs are logged to the journal of each of the involved VMs.  Generally, for each VM that has its own `static_ip` address set, this software will perform actions on that VM, on its parent ProxyVM, and on its grandparent NetVM.  In case of problems, tailing the journal (`sudo journalctl -b`) on those three VMs simultaneously can be extremely useful to figure out what is going on.
