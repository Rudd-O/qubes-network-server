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
  directory of your clone.
* Copy the prepared RPM to the dom0 of your Qubes OS
  machine.
* Install the RPM with `rpm -ivh`.
* Restart Qubes Manager, if it is running.
  (Right-click on its notification icon, select *Exit*, then
  relaunch it from the *System* menu.)

Qubes OS does not provide any facility to copy files from
a VM to the dom0.  To work around this, you can use `qvm-run`:

```
qvm-run --pass-io vmwiththerpm 'cat /home/user/path/to/qubes-network-server*rpm' > qns.rpm
```

This lets you fetch the RPM file to the dom0, and save it as `qns.rpm`.

##Troubleshooting

The actions that the network server software performs are logged to the journal of each of the involved VMs.  Generally, for each VM that has its own `static_ip` address set, this software will perform actions on that VM, on its parent ProxyVM, and on its grandparent NetVM.  In case of problems, tailing the journal (`sudo journalctl -b`) on those three VMs simultaneously can be extremely useful to figure out what is going on.
