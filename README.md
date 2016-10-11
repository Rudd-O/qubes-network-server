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

##Usage

Once installed (see below), usage of the software is straightforward.

To illustrate, we'll proceed with an example VM `httpserver` which
is meant to be a standalone VM that contains files, being served by
a running HTTP server (port 80) within it.  This VM is attached to
a ProxyVM `server-proxy`, which in turn is connected to a NetVM
`sys-net`, with IP address `192.168.1.4` on a local network
`192.168.1.0/24`.  Our goal will be to make `httpserver` accessible
to your laptop on the same physical network, which we'll assume has
IP address `192.168.1.8`.

###Assign a static address

First step is to assign an address — let's make it `192.168.1.6` —
to `httpserver`:

```
qvm-static-ip -s httpserver static_ip 192.168.1.6
```

###Restart VM

Due to limitations in this release of the code, you must power off
the `httpserver` VM and then power it back on.

###Set firewall rules on VM

Launch the Qubes Manager preferences window for the `httpserver` VM.
Go to the *Firewall rules* tab and select *Deny network access
except...* from the top area.  *Allow ICMP traffic* but deny
*DNS queries*.

Finally, add a new network rule (use the plus button).  On the
*Address* box, you're going to write `from-192.168.1.8`.  Select
the *TCP* protocol, and type `80` on the *Service* box.  Click OK.

Note the trick here — any address whose text begins with
`from-` gets transformed into an incoming traffic rule, as opposed
to the standard rules that control only outbound traffic.

**Security note**: the default "allow all" firewall leaves all ports
of the VM accessible to the world.  To the extent that you can avoid
it, do not use the "allow all" firewall setting at all.

Back on the main dialog, click *OK*.

###That's it!

You'll be able to ping, from your laptop, the address `192.168.1.6`.
You will also be able to point your browser at it, and it will
render the served pages from the HTTP server running directly on
`httpserver`.

Save from ICMP, no other port or protocol will be allowed for
inbound connections.

You'll also note that `httpserver` has received no permission to
engage in any sort of outbound network traffic.

###Inter-VM network communication

This software isn't limited to just letting network servers be
accessible from your physical network.  VMs can talk among each
other too.  Simple instructions:

* Set up a static IP address for each VM.
* Set up the appropriate rules to let them talk to each other.

VMs so authorized can talk to each other over the network,
even when they do not share a ProxyVM between them, of course,
so long as their ProxyVMs share the same NetVM.

###Disabling network server

Two-step process.  Step one:

```
qvm-static-ip -s httpserver static_ip none
```

Step two: power the VM off, then start it back up.

##Installation

Installation is extremely easy:

* Prepare an RPM with the `make rpm` command on the local
  directory of your clone.
* Copy the prepared RPM to the dom0 of your Qubes OS
  machine.
* Install the RPM with `rpm -ivh`.

Qubes OS does not provide any facility to copy files from
a VM to the dom0.  To work around this, you can use `qvm-run`:

```
qvm-run --pass-io vmwiththerpm 'cat /home/user/path/to/qubes-network-server*rpm' > qns.rpm
```

This lets you fetch the RPM file to the dom0, and save it as `qns.rpm`.

##Troubleshooting

The actions that the network server software performs are logged to the journal of each of the involved VMs.  Generally, for each VM that has its own `static_ip` address set, this software will perform actions on that VM, on its parent ProxyVM, and on its grandparent NetVM.  In case of problems, tailing the journal (`sudo journalctl -b`) on those three VMs simultaneously can be extremely useful to figure out what is going on.
