Name:          flatpost
Version:       1.0.0
Release:       1%{?dist}
License:       BSD 2-Clause
Summary:       Desktop environment agnostic Flathub software center.

URL:            https://github.com/gloriouseggroll/flatpost
Source0:        %{URL}/archive/refs/tags/%{version}.tar.gz

BuildArch:      noarch
BuildRequires:  python3-devel
BuildRequires:  make

Provides:	nobara-updater

# App Deps
Requires: python
Requires: python3
Requires: python3-gobject
Requires: python3-requests
Requires: python3-pillow
Requires: python3-svgwrite
Requires: python3-fonttools
Requires: python3-numpy

Requires: flatpak
Requires: glib2
Requires: gtk3
Requires: gtk4
Requires: xdg-utils

Provides: flatpost

%description
Desktop environment agnostic Flathub software center. Allows for browsing,
installation, removal, updating, and permission management of flatpak packages and repositories.

%prep
%autosetup -p1 -n flatpost-%{version}

%build
make all DESTDIR=%{buildroot}

%post
#!/bin/bash

# Check if we already have the association
if [ ! -f /usr/bin/xdg-mime ]; then
    # If xdg-mime is not available, skip this step
    exit 0
fi

# Set the default application for .rpm files
xdg-mime default /usr/share/applications/com.flatpost.flatpostapp.desktop application/vnd.flatpak.ref
xdg-mime default /usr/share/applications/com.flatpost.flatpostapp.desktop application/vnd.flatpak.repo
update-mime-database /usr/share/mime

%files
%{python3_sitelib}/flatpost/
%{_bindir}/flatpost
%{_datadir}/applications/com.flatpost.flatpostapp.desktop
%{_datadir}/flatpost/collections_data.json
%{_datadir}/icons/hicolor/1024x1024/apps/com.flatpost.flatpostapp.png
%{_datadir}/icons/hicolor/64x64/apps/com.flatpost.flatpostapp.png
%license %{_datadir}/licenses/flatpost/LICENSE

%clean
rm -rf %{buildroot}

%changelog
* Fri Jun 28 2024 Your Name <you@example.com> - 1.0-1
- Initial package
