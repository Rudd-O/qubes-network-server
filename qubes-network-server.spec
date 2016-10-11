%define debug_package %{nil}

Name:           qubes-network-server
Version:        0.0.2
Release:        1%{?dist}
Summary:        Turn your Qubes OS into a network server
BuildArch:      noarch

License:        GPLv3+
URL:            https://github.com/Rudd-O/qubes-network-server
Source0:	Source0: https://github.com/Rudd-O/%{name}/archive/{%version}.tar.gz#/%{name}-%{version}.tar.gz

BuildRequires:  go

%description
This package lets you turn your Qubes OS into a network server.

%prep
%setup -q

%build
# variables must be kept in sync with install
make DESTDIR=$RPM_BUILD_ROOT BINDIR=%{_bindir} LIBDIR=%{_libdir}

%install
rm -rf $RPM_BUILD_ROOT
# variables must be kept in sync with build
make install DESTDIR=$RPM_BUILD_ROOT BINDIR=%{_bindir} LIBDIR=%{_libdir}

%files
%attr(0755, root, root) %{_bindir}/qvm-static-ip
%attr(0644, root, root) %{_libdir}/python2.7/site-packages/qubes/modules/*.py*
%doc README.md TODO

%changelog
* Tue Oct 11 2016 Manuel Amador (Rudd-O) <rudd-o@rudd-o.com>
- Initial release
