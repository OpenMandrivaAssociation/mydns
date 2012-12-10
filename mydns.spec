%define webadminroot /var/www/html/admin

Summary:	A MySQL-based Internet DNS server
Name:		mydns
Version:	1.1.0
Release:	10
License:	GPL
Group:		System/Servers
URL:		http://mydns.bboy.net/
Source0:	http://mydns.bboy.net/download/%{name}-%{version}.tar.bz2
Source1:	%{name}.init
Patch0:		mydns-0.11.0-conf.patch
BuildRequires:	mysql-static-devel
BuildRequires:	zlib-devel
BuildRequires:	docbook-utils-pdf
BuildRequires:	gettext-devel
BuildRequires:	texinfo

%description
MyDNS is a free DNS server for UNIX implemented from scratch and
designed to utilize the MySQL database for data storage.

Its primary objectives are stability, security, interoperability,
and speed, though not necessarily in that order.

MyDNS does not include recursive name service, nor a resolver
library. It is primarily designed for organizations with many
zones and/or resource records who desire the ability to perform
real-time dynamic updates on their DNS data via MySQL.

MyDNS starts and is ready to answer questions immediately, no
matter how much DNS data you have in the database. It is extremely
fast and memory-efficient. It includes complete documentation,
including a manual and a FAQ. It supports a few frills, including
round robin DNS, dynamic load balancing, and outgoing AXFR for
non-MyDNS nameservers.

%package	admin
Summary:	Web admin GUI written in php for %{name}
Group:		System/Servers
Requires:	mod_php
Requires:	php-mysql
Requires:	%{name} = %{version}

%description	admin
This package contains a web admin GUI written in php for %{name}

%package	devel
Summary:	Development libraries and headers for %{name}
Group:		Development/C

%description	devel
This package contains the development libraries and headers for
%{name}

%prep

%setup -q
%patch0 -p0

# path fix
find -type f | xargs perl -pi -e "s|/usr/local/bin/php|%{_bindir}/php|g"

%build
autoreconf -fi
%configure2_5x \
    --with-mysql \
    --with-mysql-lib=%{_libdir} \
    --with-mysql-include=%{_includedir}/mysql \
    --with-zlib=%{_libdir} \
    --without-pgsql \
    --enable-status \
    --enable-alias

# use "--without-pgsql" until people complain about it ;)

%make

# build the pdf
pushd doc
    make pdf
popd

%install
rm -rf %{buildroot}

# don't fiddle with the initscript!
export DONT_GPRINTIFY=1

%makeinstall

install -d %{buildroot}%{_initrddir}
install -d %{buildroot}%{webadminroot}/%{name}
install -d %{buildroot}/var/run/%{name}

install -m644 contrib/admin.php %{buildroot}%{webadminroot}/%{name}/index.php
install -m644 contrib/stats.php %{buildroot}%{webadminroot}/%{name}/

# generate and fix the config on the fly
%{buildroot}%{_sbindir}/mydns --dump-config > %{buildroot}%{_sysconfdir}/%{name}.conf
perl -pi -e "s|^user = nobody|user = %{name}|g" %{buildroot}%{_sysconfdir}/%{name}.conf
perl -pi -e "s|^group = nogroup|group = %{name}|g" %{buildroot}%{_sysconfdir}/%{name}.conf
chmod 640 %{buildroot}%{_sysconfdir}/%{name}.conf

# install sysv script
install -m0755 %{SOURCE1} %{buildroot}%{_initrddir}/%{name}

# devel stuff
install -d %{buildroot}%{_includedir}
install -d %{buildroot}%{_libdir}
install src/lib/mydns.h %{buildroot}%{_includedir}/
install src/lib/libmydns.a %{buildroot}%{_libdir}/

%{find_lang} %{name}

%pre
%_pre_useradd %{name} /var/lib/%{name} /bin/false

%post
%_post_service %{name}

%preun
%_preun_service %{name}

%postun
%_postun_userdel %{name}

%files -f %{name}.lang
%doc AUTHORS BUGS ChangeLog NEWS QUICKSTART* README* TODO doc/*.pdf
%doc contrib/README.alias
%config(noreplace) %attr(0640,root,root) %{_sysconfdir}/%{name}.conf
%attr(0755,root,root) %{_initrddir}/%{name}
%{_bindir}/%{name}*
%{_sbindir}/%{name}
%{_mandir}/man?/*
%{_infodir}/*
%dir %attr(0755,%{name},%{name}) /var/run/%{name}

%files admin
%doc contrib/README
%dir %{webadminroot}/%{name}
%config(noreplace) %attr(0644,root,root) %{webadminroot}/%{name}/index.php
%attr(0644,root,root) %{webadminroot}/%{name}/stats.php

%files devel
%{_libdir}/*.a
%{_includedir}/*.h



%changelog
* Mon Jun 04 2012 Andrey Bondrov <abondrov@mandriva.org> 1.1.0-10
+ Revision: 802238
- Drop some legacy junk

  + Oden Eriksson <oeriksson@mandriva.com>
    - relink against libmysqlclient.so.18

* Mon Dec 06 2010 Oden Eriksson <oeriksson@mandriva.com> 1.1.0-8mdv2011.0
+ Revision: 612972
- the mass rebuild of 2010.1 packages

* Mon Apr 19 2010 Funda Wang <fwang@mandriva.org> 1.1.0-7mdv2010.1
+ Revision: 536598
- BR gettext-devel
- fix spec file
- rebuild

* Mon Oct 05 2009 Guillaume Rousse <guillomovitch@mandriva.org> 1.1.0-6mdv2010.0
+ Revision: 454243
- fix dependencies

* Fri Sep 04 2009 Thierry Vignaud <tv@mandriva.org> 1.1.0-5mdv2010.0
+ Revision: 430138
- rebuild

* Mon Jun 16 2008 Thierry Vignaud <tv@mandriva.org> 1.1.0-4mdv2009.0
+ Revision: 220145
- rebuild
- kill re-definition of %%buildroot on Pixel's request
- import mydns

  + Olivier Blin <blino@mandriva.org>
    - restore BuildRoot


* Mon Sep 04 2006 Oden Eriksson <oeriksson@mandriva.com> 1.1.0-1mdv2007.0
- rebuilt against MySQL-5.0.24a-1mdv2007.0 due to ABI changes

* Thu Apr 06 2006 Michael Scherer <misc@mandriva.org> 1.1.0-2mdk
- correct the requires, fix #21880

* Fri Feb 24 2006 Oden Eriksson <oeriksson@mandriva.com> 1.1.0-1mdk
- 1.1.0
- drop upstream patches; P1
- fix deps

* Fri Nov 18 2005 Oden Eriksson <oeriksson@mandriva.com> 1.0.0-4mdk
- rebuilt against openssl-0.9.8a

* Sun Oct 30 2005 Oden Eriksson <oeriksson@mandriva.com> 1.0.0-3mdk
- rebuilt against MySQL-5.0.15

* Tue May 10 2005 Oden Eriksson <oeriksson@mandriva.com> 1.0.0-2mdk
- lib64 fixes
- added one gcc4 patch (debian)
- rpmlint fixes

* Mon Jan 24 2005 Oden Eriksson <oeriksson@mandrakesoft.com> 1.0.0-1mdk
- 1.0.0
- rebuilt against MySQL-4.1.x system libs
- drop the daemontools stuff
- own the %%{webadminroot}/%%{name} dir

* Sat May 22 2004 Oden Eriksson <oeriksson@mandrakesoft.com> 0.11.0-1mdk
- 0.11.0
- new P0
- fix deps
- added the stats.php file
- fix ownership of the /var/run/mydns directory
- misc spec file fixes

* Tue Dec 16 2003 Lenny Cartier <lenny@mandrakesoft.com> 0.10.1-1mdk
- 0.10.1

* Sun Aug 17 2003 Oden Eriksson <oden.eriksson@kvikkjokk.net> 0.10.0-1mdk
- 0.10.0

* Thu Jul 31 2003 Oden Eriksson <oden.eriksson@kvikkjokk.net> 0.9.13-1mdk
- 0.9.13

* Fri Jul 25 2003 Oden Eriksson <oden.eriksson@kvikkjokk.net> 0.9.12-1mdk
- 0.9.12
- use the %%configure2_5x macro
- added P0
- fixed S1
- misc spec file fixes

* Thu Jul 10 2003 Oden Eriksson <oden.eriksson@kvikkjokk.net> 0.9.10-2mdk
- rebuild

* Sun May 04 2003 Oden Eriksson <oden.eriksson@kvikkjokk.net> 0.9.10-1mdk
- 0.9.10

* Fri Apr 25 2003 Marcel Pol <mpol@gmx.net> 0.9.9-3mdk
- buildrequires

* Sun Apr 13 2003 Marcel Pol <mpol@gmx.net> 0.9.9-2mdk
- buildrequires

* Tue Apr 08 2003 Oden Eriksson <oden.eriksson@kvikkjokk.net> 0.9.9-1mdk
- 0.9.9

* Sat Mar 29 2003 Oden Eriksson <oden.eriksson@kvikkjokk.net> 0.9.8-1mdk
- 0.9.8
- html docs is gone, bring in pdf
- misc spec file fixes

* Tue Mar 11 2003 Marcel Pol <mpol@gmx.net> 0.9.7-2mdk
- conflicts: tmdns
- include locales

* Sat Mar 08 2003 Oden Eriksson <oden.eriksson@kvikkjokk.net> 0.9.7-1mdk
- 0.9.7

* Wed Mar 05 2003 Oden Eriksson <oden.eriksson@kvikkjokk.net> 0.9.6-1mdk
- 0.9.6
- rebuilt against latest mysql
- misc spec file fixes

* Thu Jan 16 2003 Oden Eriksson <oden.eriksson@kvikkjokk.net> 0.9.5-2mdk
- build release

* Mon Dec 16 2002 Oden Eriksson <oden.eriksson@kvikkjokk.net> 0.9.5-1mdk
- new version
- new S1
- misc spec file fixes
- new sub package "devel"
- run as mydns:mydns

* Sat Sep 28 2002 Oden Eriksson <oden.eriksson@kvikkjokk.net> 0.9.3-1mdk
- new version
- misc spec file fixes

* Thu Sep 19 2002 Oden Eriksson <oden.eriksson@kvikkjokk.net> 0.9.2-1mdk
- initial cooker contrib
- install web admin stuff in common %%{webadminroot}/ directory
- added a simple init script
