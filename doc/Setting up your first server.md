# Setting up your first server under Qubes network server

To illustrate, we'll proceed with an example VM `httpserver` which
is meant to be a standalone VM that contains files, being served by
a running HTTP server (port 80) within it.  This VM is attached to
a ProxyVM `server-proxy`, which in turn is connected to a NetVM
`sys-net`, with IP address `192.168.1.4` on a local network
`192.168.1.0/24`.  Our goal will be to make `httpserver` accessible
to your laptop on the same physical network, which we'll assume has
IP address `192.168.1.8`.

##Assign a static address

First step is to assign an address — let's make it `192.168.1.6` —
to `httpserver`:

```
qvm-static-ip -s httpserver static_ip 192.168.1.6
```

##Restart VM

Due to limitations in this release of the code, you must power off
the `httpserver` VM and then power it back on.

##Set firewall rules on VM

If you are new to firewall rules in Qubes, [check out this quite
good overview of them](https://www.qubes-os.org/doc/qubes-firewall/).

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

##That's it!

You'll be able to ping, from your laptop, the address `192.168.1.6`.
You will also be able to point your browser at it, and it will
render the served pages from the HTTP server running directly on
`httpserver`.

Save from ICMP, no other port or protocol will be allowed for
inbound connections.

You'll also note that `httpserver` has received no permission to
engage in any sort of outbound network traffic.

##Inter-VM network communication

This software isn't limited to just letting network servers be
accessible from your physical network.  VMs can talk among each
other too.  Simple instructions:

* Set up a static IP address for each VM.
* Set up the appropriate rules to let them talk to each other.

VMs so authorized can talk to each other over the network,
even when they do not share a ProxyVM between them, of course,
so long as their ProxyVMs share the same NetVM.

##Disabling network server

Two-step process.  Step one:

```
qvm-static-ip -s httpserver static_ip none
```

Step two: power the VM off, then start it back up.
