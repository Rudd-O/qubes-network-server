SBINDIR=/usr/local/sbin
UNITDIR=/etc/systemd/system
DESTDIR=
PROGNAME=qubes-network-server

all: src/qubes-routing-manager.service

src/qubes-routing-manager.service: src/qubes-routing-manager.service.in
	sed 's|@SBINDIR@|$(SBINDIR)|g' < $< > $@

ROOT_DIR := $(shell dirname $(realpath $(firstword $(MAKEFILE_LIST))))

.PHONY: clean dist rpm srpm install

clean:
	find -name '*.pyc' -o -name '*~' -print0 | xargs -0 rm -f
	rm -rf *.tar.gz *.rpm

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

install: all
	install -Dm 755 src/qubes-routing-manager -t $(DESTDIR)/$(SBINDIR)/
	install -Dm 644 src/qubes-routing-manager.service -t $(DESTDIR)/$(UNITDIR)/
