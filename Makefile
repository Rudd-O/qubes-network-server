SBINDIR=/usr/local/sbin
UNITDIR=/etc/systemd/system
DESTDIR=
PROGNAME=qubes-network-server
PYTHON=/usr/bin/python3

all: src/qubes-routing-manager.service

src/qubes-routing-manager.service: src/qubes-routing-manager.service.in
	sed 's|@SBINDIR@|$(SBINDIR)|g' < $< > $@

ROOT_DIR := $(shell dirname $(realpath $(firstword $(MAKEFILE_LIST))))

.PHONY: clean dist rpm srpm install-template install-dom0 test

clean:
	cd $(ROOT_DIR) || exit $$? ; find -name '*.pyc' -o -name '*~' -print0 | xargs -0 rm -f
	cd $(ROOT_DIR) || exit $$? ; rm -rf *.tar.gz *.rpm
	cd $(ROOT_DIR) || exit $$? ; rm -rf *.egg-info build .mypy_cache

dist: clean
	@which rpmspec || { echo 'rpmspec is not available.  Please install the rpm-build package with the command `dnf install rpm-build` to continue, then rerun this step.' ; exit 1 ; }
	cd $(ROOT_DIR) || exit $$? ; excludefrom= ; test -f .gitignore && excludefrom=--exclude-from=.gitignore ; DIR=`rpmspec -q --queryformat '%{name}-%{version}\n' *spec | head -1` && FILENAME="$$DIR.tar.gz" && tar cvzf "$$FILENAME" --exclude="$$FILENAME" --exclude=.git --exclude=.gitignore $$excludefrom --transform="s|^|$$DIR/|" --show-transformed *

srpm: dist
	@which rpmbuild || { echo 'rpmbuild is not available.  Please install the rpm-build package with the command `dnf install rpm-build` to continue, then rerun this step.' ; exit 1 ; }
	cd $(ROOT_DIR) || exit $$? ; rpmbuild --define "_srcrpmdir ." -ts `rpmspec -q --queryformat '%{name}-%{version}.tar.gz\n' *spec | head -1`

rpm: dist
	@which rpmbuild || { echo 'rpmbuild is not available.  Please install the rpm-build package with the command `dnf install rpm-build` to continue, then rerun this step.' ; exit 1 ; }
	cd $(ROOT_DIR) || exit $$? ; rpmbuild --define "_srcrpmdir ." --define "_rpmdir builddir.rpm" -ta `rpmspec -q --queryformat '%{name}-%{version}.tar.gz\n' *spec | head -1`
	cd $(ROOT_DIR) ; mv -f builddir.rpm/*/* . && rm -rf builddir.rpm

install-template: all
	PYTHONDONTWRITEBYTECODE=1 python3 routingmanagersetup.py install $(PYTHON_PREFIX_ARG) -O0 --root $(DESTDIR)
	install -Dm 755 src/qubes-routing-manager -t $(DESTDIR)/$(SBINDIR)/
	sed -i "s,^#!.*,#!$(PYTHON)," $(DESTDIR)/$(SBINDIR)/qubes-routing-manager
	install -Dm 644 src/qubes-routing-manager.service -t $(DESTDIR)/$(UNITDIR)/

# Python 3 is always used for Qubes admin package.
install-dom0:
	PYTHONDONTWRITEBYTECODE=1 python3 networkserversetup.py install $(PYTHON_PREFIX_ARG) -O0 --root $(DESTDIR)

install: install-dom0 install-template

test:
	tox --current-env
