%define base_version 1.2.8
%define mydns_user   mydns
%define mydns_group  mydns
%define mydns_home   %{_localstatedir}/lib/mydns

Summary: A Database based DNS server

Name:    mydns
Version: 1.2.8.31
Release: 1
License: GPLv2+
Group:   System/Servers
URL:     http://mydns-ng.com/
#URL: http://mydns.bboy.net/  this is the original website, but mydns is no more  maintaned by it's original creator
#because this mydns-ng in sourceforge was created
Source0: http://downloads.sourceforge.net/%{name}/%{name}-%{version}.tar.gz
Source1: HOWTO
Source2: mydns.service

BuildRequires: mysql-devel
BuildRequires: mysql-static-devel
BuildRequires: postgresql-devel
BuildRequires: mysql
BuildRequires: postgresql
BuildRequires: texinfo
BuildRequires: gettext-devel
BuildRequires: zlib-devel
BuildRequires: docbook-utils-pdf

Requires(pre):     shadow-utils
Requires(post):    systemd-units
Requires(preun):   systemd-units
Requires(postun):  systemd-units

Patch0: mydns_user.patch
Patch1: mydns-1.2.8.31-lib64.patch
Patch2:	mydns-1.2.8.31-texi.patch

%description
A nameserver that serves records directly from your database.

%package mysql
Summary: MyDNS compiled with MySQL support

Group: System/Servers
Requires: %{name} = %{version}-%{release}
Requires(post): systemd-units
Requires(preun): systemd-units
Requires(postun): systemd-units


%description mysql
MyDNS compiled with MySQL support

%package pgsql
Summary: MyDNS compiled with PostGreSQL support

Group: System/Servers
Requires: %{name} = %{version}-%{release}
Requires(post): systemd-units
Requires(preun): systemd-units
Requires(postun): systemd-units


%description pgsql
MyDNS compiled with PostGreSQL support

%prep
%setup -q
%patch0 -p1
%patch1 -p1
%patch2 -p1

#install doc about alternatives
install -Dp -m 644 %{SOURCE1} ./HOWTO

# Convert to utf-8
for file in AUTHORS; do
    mv $file timestamp
    iconv -f ISO-8859-1 -t UTF-8 -o $file timestamp
    touch -r timestamp $file
done

%build
#mydns current doesn't support loadable modules support, so We need to compile it 2 times and use alternatives, :-(
%configure \
    --without-pgsql \
    --with-mysql \
    --with-mysql-lib=%{_libdir}/mysql \
    --with-mysql-include=%{_includedir}/mysql \
    --with-zlib=%{_libdir} \
    --enable-status \
    --enable-alias

# sed -i.bak 's#libmysqlclient_dirs="#libmysqlclient_dirs="/usr/lib64 #' ./configure

%make
make install DESTDIR=$(pwd)/mysql

%configure \
    --with-pgsql \
    --without-mysql \
    --with-pgsql-lib=%{_libdir} \
    --with-pgsql-include=%{_includedir} \
    --with-zlib=%{_libdir} \
    --enable-status \
    --enable-alias

%make
make install DESTDIR=$(pwd)/pgsql

%install

#create homedir for mydns user
%{__install} -d %{buildroot}%{mydns_home}

#install mysql and pgsql files
for database in mysql pgsql; do
    install -Dp ./$database%{_bindir}/mydnscheck %{buildroot}%{_bindir}/mydnscheck-$database
    install -Dp ./$database%{_bindir}/mydns-conf %{buildroot}%{_bindir}/mydns-conf-$database
    install -Dp ./$database%{_bindir}/mydnsexport %{buildroot}%{_bindir}/mydnsexport-$database
    install -Dp ./$database%{_bindir}/mydnsptrconvert %{buildroot}%{_bindir}/mydnsptrconvert-$database
    install -Dp ./$database%{_bindir}/mydnsimport %{buildroot}%{_bindir}/mydnsimport-$database
    install -Dp ./$database%{_sbindir}/mydns %{buildroot}%{_sbindir}/mydns-$database

    install -d %{buildroot}%{_datadir}/locale
    cp -a ./$database%{_datadir}/locale %{buildroot}%{_datadir}
done

%find_lang %{name}

#main package (all files not linked with mysql or pgsql)
install -Dp -m 644 %{SOURCE2} %{buildroot}%{_unitdir}/mydns.service
install -Dp -m 600 mydns.conf %{buildroot}%{_sysconfdir}/mydns.conf
install -Dp -m 644 contrib/admin.php %{buildroot}%{_datadir}/%{name}/admin.php

install -Dp -m 644 doc/mydns.conf.5 %{buildroot}%{_mandir}/man5/mydns.conf.5
install -Dp -m 644 doc/mydns.8 %{buildroot}%{_mandir}/man8/mydns.8
install -Dp -m 644 doc/mydnscheck.8 %{buildroot}%{_mandir}/man8/mydnscheck.8
install -Dp -m 644 doc/mydnsexport.8 %{buildroot}%{_mandir}/man8/mydnsexport.8
install -Dp -m 644 doc/mydnsimport.8 %{buildroot}%{_mandir}/man8/mydnsimport.8
install -Dp -m 644 doc/mydns-conf.8 %{buildroot}%{_mandir}/man8/mydns-conf.8
install -Dp -m 644 doc/mydns.info %{buildroot}%{_infodir}/mydns.info

%clean

%pre
getent group %{mydns_group} >/dev/null || groupadd -r %{mydns_group}
getent passwd %{mydns_user} >/dev/null || \
useradd -r -g %{mydns_group} -d %{mydns_home}  -s /sbin/nologin \
-c "MyDNS - database based DNS server account" %{mydns_user}
exit 0

%post
if [ $1 -eq 1 ] ; then 
    # Initial installation 
    /bin/systemctl daemon-reload >/dev/null 2>&1 || :
fi

%preun
if [ $1 -eq 0 ]; then
    # Package removal, not upgrade
    /bin/systemctl --no-reload disable mydns.service > /dev/null 2>&1 || :
    /bin/systemctl stop mydns.service > /dev/null 2>&1 || :
fi

%postun mysql
/bin/systemctl daemon-reload >/dev/null 2>&1 || :
if [ $1 -ge 1 ] ; then
    # Package upgrade, not uninstall
    /bin/systemctl try-restart mydns.service >/dev/null 2>&1 || :
fi

%postun pgsql
/bin/systemctl daemon-reload >/dev/null 2>&1 || :
if [ $1 -ge 1 ] ; then
    # Package upgrade, not uninstall
    /bin/systemctl try-restart mydns.service >/dev/null 2>&1 || :
fi

%post pgsql
%{_sbindir}/alternatives --install %{_sbindir}/mydns MyDNS %{_sbindir}/mydns-pgsql 1 \
    --slave %{_bindir}/mydnscheck mydnscheck %{_bindir}/mydnscheck-pgsql \
    --slave %{_bindir}/mydnsexport mydnsexport %{_bindir}/mydnsexport-pgsql \
    --slave %{_bindir}/mydnsimport mydnsimport %{_bindir}/mydnsimport-pgsql \
    --slave %{_bindir}/mydnsptrconvert mydnsptrconvert %{_bindir}/mydnsptrconvert-pgsql
if [ $1 -eq 1 ] ; then 
    # Initial installation 
    /bin/systemctl daemon-reload >/dev/null 2>&1 || :
fi


%post mysql
%{_sbindir}/alternatives --install %{_sbindir}/mydns MyDNS %{_sbindir}/mydns-mysql 2 \
    --slave %{_bindir}/mydnscheck mydnscheck %{_bindir}/mydnscheck-mysql \
    --slave %{_bindir}/mydnsexport mydnsexport %{_bindir}/mydnsexport-mysql \
    --slave %{_bindir}/mydnsimport mydnsimport %{_bindir}/mydnsimport-mysql \
    --slave %{_bindir}/mydnsptrconvert mydnsptrconvert %{_bindir}/mydnsptrconvert-mysql
if [ $1 -eq 1 ] ; then 
    # Initial installation 
    /bin/systemctl daemon-reload >/dev/null 2>&1 || :
fi

%preun pgsql
# When not removal, exit immediately
[ $1 = 0 ] || exit 0
( LANG=C ; \
	if ( %{_sbindir}/alternatives --display MyDNS | \
		grep point | grep -q %{_sbindir}/mydns-pgsql ) ; \
		then /bin/systemctl --no-reload disable mydns.service > /dev/null 2>&1 && \
		    /bin/systemctl stop mydns.service > /dev/null 2>&1 || : \
	fi ; \
)
%{_sbindir}/alternatives -remove MyDNS %{_sbindir}/mydns-pgsql
exit 0


%preun mysql
# When not removal, exit immediately
[ $1 = 0 ] || exit 0
( LANG=C ; \
	if ( %{_sbindir}/alternatives --display MyDNS | \
		grep point | grep -q %{_sbindir}/mydns-mysql ) ; \
		then /bin/systemctl --no-reload disable mydns.service > /dev/null 2>&1 && \
		    /bin/systemctl stop mydns.service > /dev/null 2>&1 || : \
	fi ; \
)
%{_sbindir}/alternatives -remove MyDNS %{_sbindir}/mydns-mysql
exit 0

%files -f %{name}.lang
%{_mandir}/man?/*
%{_infodir}/mydns.info*
%doc AUTHORS ChangeLog COPYING NEWS README TODO HOWTO
%attr(0600,root,root) %config(noreplace) %{_sysconfdir}/mydns.conf
%{_unitdir}/mydns.service
%dir %{_datadir}/%{name}
%{_datadir}/%{name}/admin.php
%attr(-,%{mydns_user},%{mydns_group}) %dir %{mydns_home}

%files mysql
%doc QUICKSTART.mysql
%{_bindir}/mydnscheck-mysql
%{_bindir}/mydns-conf-mysql
%{_bindir}/mydnsexport-mysql
%{_bindir}/mydnsptrconvert-mysql
%{_bindir}/mydnsimport-mysql
%{_sbindir}/mydns-mysql

%files pgsql
%doc QUICKSTART.postgres
%{_bindir}/mydnscheck-pgsql
%{_bindir}/mydns-conf-pgsql
%{_bindir}/mydnsexport-pgsql
%{_bindir}/mydnsptrconvert-pgsql
%{_bindir}/mydnsimport-pgsql
%{_sbindir}/mydns-pgsql

