# Setting up an SSH server

This tutorial will teach you how to set up an SSH server on your Qubes network server.

We assume:

1. That you have a desktop or laptop *manager* machine, from which you desire to manage a Qubes OS server.
2. That you have a Qubes OS *server*, which you want to manage.
3. That both machines share a physical network link (e.g. Wi-Fi or Ethernet).

## Set up Qubes network server

First of all, [install Qubes network server](https://github.com/Rudd-O/qubes-network-server#installation) on your Qubes OS server.

## Set up needed VMs

You'll need three VMs on the network server:

1. A NetVM which will be attached to the network interface mentioned above.
   For the purposes of this example, we'll call this `exp-net`.
2. A ProxyVM which will be attached to the NetVM.
   This we'll call `exp-firewall`.
3. A StandaloneVM which will be attached to the ProxyVM.  The role of this
   machine is to give you control over `dom0` and other VMs on the system.
   This we'call `exp-manager`.

Create them if you do not already have them.  Once you have created them,
start the StandaloneVM `exp-manager` you created, and then verify that you
can ping your manager machine from it.

Power off `exp-manager` when your test is complete.

## Set static address on `exp-manager`

On your server's `dom0`, run the command:

```
qvm-static-ip -s exp-manager static_ip x.y.z.w
```

`x.y.z.w` must be an IP address available on the same network that both
your `exp-net` and your manager machine share.

Power `exp-manager` back on, and verify that you can still ping your
manager machine from it.

Verify that you can ping the new IP address you gave to `exp-manager`
from your manager machine.  This should work fine.

## Harden the firewall on `exp-manager`

At this point, `exp-manager` is accessible on your network, so it's best
to set up a firewall rule permitting only SSH access from the manager
machine, and denying all other access to anyone.

If you are new to firewall rules in Qubes, [check out this quite
good overview of them](https://www.qubes-os.org/doc/qubes-firewall/).

Launch the Qubes Manager preferences window for the `exp-manager` VM.
Go to the *Firewall rules* tab and select *Deny network access
except...* from the top area.

Add a new network rule (use the plus button).  On the *Address* box,
you're going to write `from-a.b.c.d`, where `a.b.c.d` is the IP address
of your manager machine.  Select the *TCP* protocol, and type `22`
(the SSH port) on the *Service* box.  Click OK.

([See the documentation for qubes-network-server](https://github.com/Rudd-O/qubes-network-server)
to understand more about firewalling rules in Qubes network server.)

Back on the main dialog, click *OK*.

## Enable and start SSH on the `exp-manager` VM

In a terminal window of `exp-manager`, run:

```
sudo systemctl enable sshd.service
sudo systemctl start sshd.service
```

This will start the OpenSSH server on the `exp-manager` VM.

Test that you can connect via SSH from the manager machine to
the `exp-manager` VM.  You will not be able to log in, because
no password is set up, but we will fix that shortly.

## Set up SSH authentication

On the `exp-manager` VM, set a password on the `user` user:

```
sudo passwd user
```

On the manager machine, copy your SSH public key to `exp-manager`:

```
ssh-copy-id user@x.y.z.w
```

This will prompt you for the password you set up.  Enter it.

Now kill the `user` password on `exp-manager`:

```
sudo passwd -d user
sudo passwd -l user
```

Good news!  You can now remotely log in, from your manager machine,
to your Qubes OS server.

You can also [enable remote management of your Qubes network server](https://github.com/Rudd-O/ansible-qubes/tree/master/doc/Remote management of Qubes OS servers.md).
