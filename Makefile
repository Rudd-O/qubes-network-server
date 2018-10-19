BINDIR=/usr/bin
LIBDIR=/usr/lib64
DESTDIR=

clean:
	find -name '*.pyc' -o -name '*~' -print0 | xargs -0 rm -f
	rm -f *.tar.gz *.rpm

dist: clean
	excludefrom= ; test -f .gitignore && excludefrom=--exclude-from=.gitignore ; DIR=$(PROGNAME)-`awk '/^Version:/ {print $$2}' $(PROGNAME).spec` && FILENAME=$$DIR.tar.gz && tar cvzf "$$FILENAME" --exclude="$$FILENAME" --exclude=.git --exclude=.gitignore $$excludefrom --transform="s|^|$$DIR/|" --show-transformed *

rpm: dist
	@which rpmbuild || { echo 'rpmbuild is not available.  Please install the rpm-build package with the command `dnf install rpmbuild` to continue, then rerun this step.' ; exit 1 ; }
	T=`mktemp -d` && rpmbuild --define "_topdir $$T" -ta qubes-network-server-`awk '/^Version:/ {print $$2}' qubes-network-server.spec`.tar.gz || { rm -rf "$$T"; exit 1; } && mv "$$T"/RPMS/*/* "$$T"/SRPMS/* . || { rm -rf "$$T"; exit 1; } && rm -rf "$$T"

srpm: dist
	T=`mktemp -d` && rpmbuild --define "_topdir $$T" -ts qubes-network-server-`awk '/^Version:/ {print $$2}' qubes-network-server.spec`.tar.gz || { rm -rf "$$T"; exit 1; } && mv "$$T"/SRPMS/* . || { rm -rf "$$T"; exit 1; } && rm -rf "$$T"

install:
	install -Dm 755 src/usr/bin/qvm-static-ip -t $(DESTDIR)/$(BINDIR)/
	install -Dm 644 src/usr/lib64/python2.7/site-packages/qubes/modules/*.py -t $(DESTDIR)/$(LIBDIR)/python2.7/site-packages/qubes/modules
