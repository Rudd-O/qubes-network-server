%{!?python2_sitearch: %define python2_sitearch %(%{__python2} -c "from distutils.sysconfig import get_python_lib; print get_python_lib(1)")}

%define debug_package %{nil}

%define mybuildnumber %{?build_number}%{?!build_number:1}

Name:           qubes-network-server
Version:        0.0.12
Release:        %{mybuildnumber}%{?dist}
Summary:        Turn your Qubes OS into a network server
BuildArch:      noarch

License:        GPLv3+
URL:            https://github.com/Rudd-O/qubes-network-server
Source0:        https://github.com/Rudd-O/%{name}/archive/{%version}.tar.gz#/%{name}-%{version}.tar.gz

BuildRequires:  make
BuildRequires:  coreutils
BuildRequires:  tar
BuildRequires:  gawk
BuildRequires:  findutils
BuildRequires:  systemd
BuildRequires:  systemd-rpm-macros

Requires:       qubes-core-agent-networking >= 4.1
Requires:       python3
Requires:       python3-qubesdb

%description
This package lets you turn your Qubes OS into a network server.

Please see README.md enclosed in the package for instructions on how to use this.

%prep
%setup -q

%build
# variables must be kept in sync with install
make DESTDIR=$RPM_BUILD_ROOT SBINDIR=%{_sbindir} UNITDIR=%{_unitdir}

%install
rm -rf $RPM_BUILD_ROOT
# variables must be kept in sync with build
make install DESTDIR=$RPM_BUILD_ROOT SBINDIR=%{_sbindir} UNITDIR=%{_unitdir}
mkdir -p "$RPM_BUILD_ROOT"/%{_presetdir}
echo 'enable qubes-routing-manager.service' > "$RPM_BUILD_ROOT"/%{_presetdir}/75-%{name}.preset

%files
%attr(0755, root, root) %{_sbindir}/qubes-routing-manager
%attr(0644, root, root) %{_presetdir}/75-%{name}.preset
%config %attr(0644, root, root) %{_unitdir}/qubes-routing-manager.service
%doc README.md TODO

%post
%systemd_post qubes-routing-manager.service

%preun
%systemd_preun qubes-routing-manager.service

%postun
%systemd_postun_with_restart qubes-routing-manager.service

%changelog
* Mon Apr 13 2020 Manuel Amador (Rudd-O) <rudd-o@rudd-o.com>
- Update to Qubes 4.0

* Tue Oct 11 2016 Manuel Amador (Rudd-O) <rudd-o@rudd-o.com>
- Initial release
