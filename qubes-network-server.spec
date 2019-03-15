%{!?python2_sitearch: %define python2_sitearch %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib(1)")}

%define debug_package %{nil}

%define mybuildnumber %{?build_number}%{?!build_number:1}

Name:           qubes-network-server
Version:        0.0.9
Release:        %{mybuildnumber}%{?dist}
Summary:        Turn your Qubes OS into a network server
BuildArch:      noarch

License:        GPLv3+
URL:            https://github.com/Rudd-O/qubes-network-server
Source0:	https://github.com/Rudd-O/%{name}/archive/{%version}.tar.gz#/%{name}-%{version}.tar.gz

BuildRequires:  make
BuildRequires:  coreutils
BuildRequires:  tar
BuildRequires:  gawk
BuildRequires:  findutils

Requires:       qubes-core-dom0

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
%attr(0644, root, root) %{python2_sitearch}/qubes/modules/*.py*
%attr(0644, root, root) %{python2_sitearch}/qubes/modules/qubes-appvm-firewall
%doc README.md TODO

%changelog
* Tue Oct 11 2016 Manuel Amador (Rudd-O) <rudd-o@rudd-o.com>
- Initial release
