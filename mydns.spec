%define webadminroot /var/www/html/admin

Summary:	A MySQL-based Internet DNS server
Name:		mydns
Version:	1.1.0
Release:	%mkrel 3
License:	GPL
Group:		System/Servers
URL:		http://mydns.bboy.net/
Source0:	http://mydns.bboy.net/download/%{name}-%{version}.tar.bz2
Source1:	%{name}.init.bz2
Patch0:		mydns-0.11.0-conf.patch.bz2
Requires(post): rpm-helper info-install
Requires(preun): rpm-helper info-install
Requires(pre): rpm-helper
Requires(postun): rpm-helper 
BuildRequires:	MySQL-static-devel
BuildRequires:	zlib-devel
BuildRequires:	docbook-utils-pdf
BuildRequires:	texinfo
BuildRoot:	%{_tmppath}/%{name}-%{version}-buildroot

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
Group:          System/Servers
Requires:	webserver mod_php php-common php-mysql
Requires:	%{name} = %{version}

%description	admin
This package contains a web admin GUI written in php for %{name}

%package	devel
Summary:	Development libraries and headers for %{name}
Group:          Development/C

%description	devel
This package contains the development libraries and headers for
%{name}

%prep

%setup -q
%patch0 -p0

bzcat %{SOURCE1} > %{name}.init

# path fix
find -type f | xargs perl -pi -e "s|/usr/local/bin/php|%{_bindir}/php|g"

%build

%configure2_5x \
    --with-mysql \
    --with-mysql-lib=%{_libdir} \
    --with-mysql-include=%{_includedir}/mysql \
    --with-zlib=%{_libdir} \
    --without-pgsql \
    --enable-status \
    --enable-alias

# use "--without-pgsql" until people complain about it ;)

# use this patch or not?
#pushd contrib
#    patch -p0 < alias.patch
#popd

%make

# build the pdf
pushd doc
    make pdf
popd

%install
[ -n "%{buildroot}" -a "%{buildroot}" != / ] && rm -rf %{buildroot}

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
install -m0755 %{name}.init %{buildroot}%{_initrddir}/%{name}

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
%_install_info %{name}.info

%preun
%_preun_service %{name}
%_remove_install_info %{name}.info

%postun
%_postun_userdel %{name}

%clean
[ -n "%{buildroot}" -a "%{buildroot}" != / ] && rm -rf %{buildroot}

%files -f %{name}.lang
%defattr(-, root, root)
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
%defattr(-, root, root)
%doc contrib/README
%dir %{webadminroot}/%{name}
%config(noreplace) %attr(0644,root,root) %{webadminroot}/%{name}/index.php
%attr(0644,root,root) %{webadminroot}/%{name}/stats.php

%files devel
%defattr(-, root, root)
%{_libdir}/*.a
%{_includedir}/*.h

