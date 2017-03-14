%{!?python_sitearch: %define python_sitearch %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib(1)")}

%{!?version: %define version %(cat version)}

Name:           qubes-network-server
Version:        %{version}
Release:        1%{?dist}
Summary:        Turn your Qubes OS into a network server

License:        GPL
URL:            https://github.com/Rudd-O/qubes-network-server

Requires:       qubes-core-dom0

%define _builddir %(pwd)

%description
This package lets you turn your Qubes OS into a network server.

%build
python -m compileall plugin
python -O -m compileall plugin

%install
mkdir -p $RPM_BUILD_ROOT%{python_sitearch}/qubes/modules
cp plugin/*.py* $RPM_BUILD_ROOT%{python_sitearch}/qubes/modules
install -D qvm-static-ip $RPM_BUILD_ROOT%{_bindir}/qvm-static-ip

%clean
rm -rf $RPM_BUILD_ROOT
rm -f plugin/*.py[co]

%files
%defattr(0644, root, root, -)
%{python_sitearch}/qubes/modules/001FortressQubesVm.py*
%{python_sitearch}/qubes/modules/006FortressQubesNetVm.py*
%{python_sitearch}/qubes/modules/007FortressQubesProxyVm.py*
%attr(0755, -, -) %{_bindir}/qvm-static-ip
%doc README.md TODO

%changelog
* Tue Oct 11 2016 Manuel Amador (Rudd-O) <rudd-o@rudd-o.com>
- Initial release
