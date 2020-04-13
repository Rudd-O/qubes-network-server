# Setting up an SSH server

This tutorial will teach you how to set up an SSH server on your Qubes network server.

We assume:

1. That you have a desktop or laptop *manager* machine.
2. That you have a Qubes OS *server*.
3. That both machines share a physical network link (e.g. Wi-Fi or Ethernet).

## Set up Qubes network server

First of all, [install Qubes network server](https://github.com/Rudd-O/qubes-network-server#installation) on your Qubes OS server.

## Set up needed VMs

You'll need two VMs on the network server:

1. A NetVM which will be attached to the network interface mentioned above.
   For the purposes of this example, we'll call this `exp-net`.
3. A StandaloneVM which will be attached to the ProxyVM.  The role of this
   machine is to give you control over `dom0` and other VMs on the system.
   This we'call `exp-ssh`.

Create them if you do not already have them.  Once you have created them,
start the StandaloneVM `exp-ssh` you created, and then verify that networking
works within `exp-ssh`.

## Set static address on `exp-ssh`

On your server's `dom0`, run the command:

```
qvm-prefs -s exp-ssh static_ip x.y.z.w
```

`x.y.z.w` must be an IP address available on the same network that both
your `exp-net` and your manager machine share.

Shut down `exp-ssh` back on, start it back up again,
and verify that you can still ping your manager machine from it.

## Enable forward-style routing for `exp-ssh`

```
qvm-features exp-ssh routing-method forward
```

Now verify that you can ping the new IP address you gave to `exp-ssh`
from your manager machine.  This should work fine.

## Adjust the firewall on `exp-ssh`

At this point, `exp-ssh` is accessible on your network, so it's best
to set up a firewall rule permitting only SSH access from the manager
machine, and denying all other access to anyone.

[See the documentation for Qubes OS](https://www.qubes-os.org/doc/firewall/#where-to-put-firewall-rules)
to understand more about firewalls in AppVMs

## Enable and start SSH on the `exp-ssh` VM

In a terminal window of `exp-ssh`, run:

```
sudo systemctl enable --now sshd.service
```

This will start the OpenSSH server on the `exp-ssh` VM.

Test that you can connect via SSH from the manager machine to
the `exp-ssh` VM.  You will not be able to log in, because
no password is set up, but we will fix that shortly.

## Set up SSH authentication

On the `exp-ssh` VM, set a password on the `user` user:

```
sudo passwd user
```

On the manager machine, copy your SSH public key to `exp-ssh`:

```
ssh-copy-id user@x.y.z.w
```

This will prompt you for the password you set up.  Enter it.

Now kill the `user` password on `exp-ssh`:

```
sudo passwd -d user
sudo passwd -l user
```

Good news!  You can now remotely log in, from your manager machine,
to your Qubes OS server.  You are also able to run commands on the
`exp-ssh` VM, directly from your manager machine.

Should you want to run commands on *other* VMs of your Qubes OS server,
then learn how to [enable remote management of your Qubes network server](https://github.com/Rudd-O/ansible-qubes/tree/master/doc/Remote management of Qubes OS servers.md).
