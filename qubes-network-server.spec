%define debug_package %{nil}

%define mybuildnumber %{?build_number}%{?!build_number:1}

Name:           qubes-network-server
Version:        0.1.2
Release:        %{mybuildnumber}%{?dist}
Summary:        Turn your Qubes OS into a network server
BuildArch:      noarch

License:        GPLv2+
URL:            https://github.com/Rudd-O/qubes-network-server
Source0:        https://github.com/Rudd-O/%{name}/archive/{%version}.tar.gz#/%{name}-%{version}.tar.gz

BuildRequires:  make
BuildRequires:  coreutils
BuildRequires:  tar
BuildRequires:  findutils
BuildRequires:  python3
BuildRequires:  python3-rpm-macros
BuildRequires:  systemd-rpm-macros

Requires:       qubes-core-agent-networking >= 4.2
Requires:       python3
Requires:       python3-qubesdb
Requires:       nftables

%description
This package lets you turn your Qubes OS into a network server.  Install this
in the TemplateVM of your NetVM.  Then install the companion
qubes-core-admin-addon-network-server package in your dom0.

Please see README.md enclosed in the package for instructions on how to use
this software.

%package -n     qubes-core-admin-addon-network-server
Summary:        dom0 administrative extension for Qubes network server

BuildRequires:  make
BuildRequires:  coreutils
BuildRequires:  tar
BuildRequires:  findutils
BuildRequires:  python3
BuildRequires:  python3-rpm-macros
BuildRequires:  python3-setuptools

Requires:       python3
Requires:       qubes-core-dom0 >= 4.2

%description -n qubes-core-admin-addon-network-server
This package lets you turn your Qubes OS into a network server.  Install this
in your dom0.  Then install the companion qubes-network-server package in the
TemplateVM of your NetVM.

Please see README.md enclosed in the package for instructions on how to use
this software.

%prep
%setup -q

%build
# variables must be kept in sync with install
make DESTDIR=$RPM_BUILD_ROOT SBINDIR=%{_sbindir} UNITDIR=%{_unitdir} PYTHON=%{__python3}

%install
rm -rf $RPM_BUILD_ROOT
# variables must be kept in sync with build
make install DESTDIR=$RPM_BUILD_ROOT SBINDIR=%{_sbindir} UNITDIR=%{_unitdir} PYTHON=%{__python3}
mkdir -p "$RPM_BUILD_ROOT"/%{_presetdir}
echo 'enable qubes-routing-manager.service' > "$RPM_BUILD_ROOT"/%{_presetdir}/75-%{name}.preset

%files
%attr(0755, root, root) %{_sbindir}/qubes-routing-manager
%attr(0644, root, root) %{python3_sitelib}/qubesroutingmanager/*
%{python3_sitelib}/qubesroutingmanager-*.egg-info
%attr(0644, root, root) %{_presetdir}/75-%{name}.preset
%config %attr(0644, root, root) %{_unitdir}/qubes-routing-manager.service
%doc README.md TODO

%files -n     qubes-core-admin-addon-network-server
%attr(0644, root, root) %{python3_sitelib}/qubesnetworkserver/*
%{python3_sitelib}/qubesnetworkserver-*.egg-info

%post
%systemd_post  qubes-routing-manager.service

%preun
%systemd_preun qubes-routing-manager.service

%postun
%systemd_postun_with_restart qubes-routing-manager.service

%post -n      qubes-core-admin-addon-network-server
%systemd_post qubesd.service

%postun -n    qubes-core-admin-addon-network-server
%systemd_postun_with_restart qubesd.service

%changelog
* Mon Apr 13 2020 Manuel Amador (Rudd-O) <rudd-o@rudd-o.com>
- Update to Qubes 4.0

* Tue Oct 11 2016 Manuel Amador (Rudd-O) <rudd-o@rudd-o.com>
- Initial release
