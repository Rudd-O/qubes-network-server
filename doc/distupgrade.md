# How to upgrade a Qubes network server from Qubes OS 4.1 to Qubes OS 4.2

The [standard instructions to upgrade Qubes OS systems](https://www.qubes-os.org/doc/upgrade/4.2/)
will fail to work.  The instructions tell you to run something to the effect of:

```
qubes-dist-upgrade --all-pre-reboot <other flags>
```

then reboot, then run:

```
qubes-dist-upgrade --all-post-reboot <other flags>
```

The pre-reboot phase will fail if run without the following precautions.

## Step by step instructions

First, build a `qubes-network-server` RPM with the instructions provided
by this package's [README.md](../README.md) file.  Then, for each template
where `qubes-network-server` is installed, deposit your build of the
`qubes-network-server` RPM in a folder `/root/update` of the template,
and run the command `createrepo_c /root/update` (you may have to install
package `createrepo_c` via `dnf` to run it).

Now build a `qubes-core-admin-addon-network-server` package for your dom0,
then copy the file to your profile directory into dom0.  Remember this
package has to be built *in the same Fedora release (37)* as the Qubes OS
4.2 dom0 (the `toolbox` command in a disposable qube is handy for this!).

Now open the file `/etc/dnf/dnf.conf` on every template qube where you
did the above, then add an `exclude=qubes-network-server` setting under
its `[main]` section.

Remove the currently-installed `qubes-core-admin-addon-network-server`
package from your dom0 (using `dnf remove`).

Run the pre-reboot phase.

Install the recently-built `qubes-core-admin-addon-network-server` package
into dom0 (using `dnf install` with the path to the RPM file).

Reboot.

Before running the post-reboot phase, remove the setting you added to the
`dnf.conf` file of each template you modified.  Finally, add the file
`/etc/yum.repos.d/local.repo` with the following contents:

```
[local]
name=Local packages
baseurl=file:///root/update
enabled=1
gpgcheck=0
metadata_expire=15
```

Now run the post-reboot phase.  The template upgrade should succeed now.

To finalize, delete folder `/root/update` and file `/etc/yum.repos.d/local.repo`
from every template that has it.

You are now updated to Qubes OS 4.2 and `qubes-network-server` is ready.
