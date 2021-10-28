# Setting up your first server under Qubes network server

To illustrate, we'll proceed with an example VM `httpserver` which
is meant to be a standalone VM that contains files, being served by
a running HTTP server (port 80) within it.  This VM is attached to a
NetVM `sys-net`, with IP address `192.168.1.4` on a local network
`192.168.1.0/24`.  Our goal will be to make `httpserver` accessible
to your client laptop on the same physical network, which we'll
assume has IP address `192.168.1.8`.

##Assign a static address

First step is to assign an address — let's make it `192.168.1.6` —
to `httpserver` (of course, you should make sure that this IP
address isn't used by any other equipment in your network):

```
qvm-prefs -s httpserver ip 192.168.1.6
```

##Restart VM

Due to limitations in how the IP address is set on the VM, you must
power off the `httpserver` VM and then power it back on.

## Enable forward-style routing to the VM

```
qvm-feature httpserver routing-method forward
```

Now the IP of the `httpserver` VM is visible to your laptop, but
it's got the standard Qubes OS firewall rules that all AppVMs have,
so next we'll adjust that.

##Set firewall rules on VM

The normal way to set up AppVM firewall rules is
[documented here](https://www.qubes-os.org/doc/firewall/#where-to-put-firewall-rules).

For the purposes of this demo, all you have to run inside `httpserver`
is this:

```
sudo iptables -I INPUT 1 -p tcp --dport 8080 -j ACCEPT
```

(This method of setting firewall rules makes them go away when you
restart the AppVM.  Refer to the link in this section to make them
stick around after a VM restart.)

## Start a Python HTTP server

In your `httpserver` VM, run:

```
python3 -m http.server
```

##That's it!

You will now be able to point your browser at http://192.168.1.6:8080/,
and it will render the served pages from the HTTP server running
directly on `httpserver`.

##Inter-VM network communication

This software isn't limited to just letting network servers be
accessible from your physical network.  VMs can talk among each
other too.  A pair of VMs whose feature `routing-method` has been
set to `forward` are authorized to talk to each other over the
network, so long as they are attached to the same NetVM.

##Disabling network server

One-step process:

```
qvm-feature --delete httpserver routing-method
```

You're done.
