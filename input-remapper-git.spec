# Version File Source
# I've put it here because I need it declared before it's used in some definitions.
Source2:        _version

# DEFINITIONS
# Repo tags are now pulled from the _version file, so it only has to be changed in one place.
# This is why sources were declared above.
%define pkgname %(awk 'NR==1 {print; exit}' < %{SOURCE2} )
%define pkgversion %(awk 'NR==2 {print; exit}' < %{SOURCE2} )
%define pkgrelease %(awk 'NR==3 {print; exit}' < %{SOURCE2} )
%define reponame input-remapper

Name:           %{pkgname}
Version:        %{pkgversion}
Release:        %{pkgrelease}
Summary:        An easy to use tool to change the behaviour of your input devices (from latest git commit)
License:        GPL-3.0-or-later
URL:            https://github.com/sezanzeb/input-remapper
Source0:        %{url}/archive/refs/heads/input-remapper-main.tar.gz
Source1:        README.Fedora
BuildArch:      noarch

BuildRequires:  desktop-file-utils
BuildRequires:  libappstream-glib
BuildRequires:  pyproject-rpm-macros
BuildRequires:  systemd-rpm-macros
BuildRequires:  python3-devel
BuildRequires:  python3-setuptools
BuildRequires:  python3-wheel
BuildRequires:  gettext
BuildRequires:  python3-evdev
BuildRequires:  python3-gobject-base
BuildRequires:  python3-pydantic
BuildRequires:  python3-pydbus

# Called from inputremapper/gui/reader_service.py
BuildRequires:  /usr/bin/pgrep
Requires:       /usr/bin/pgrep

# inputremapper/gui/components/editor.py
BuildRequires:  python3-cairo
Requires:       python3-cairo

# Extra test dependencies (see scripts/ci-install-deps.sh):
BuildRequires:  python3-psutil
Requires:       python3-psutil

# Using pytest as the test runner lets us ignore modules and skip tests
BuildRequires:  python3-pytest

BuildRequires:  gobject-introspection
Requires:       gobject-introspection
# Grep for require_version to find these:
# gi.require_version("Gdk", "3.0")
# gi.require_version("Gtk", "3.0")
BuildRequires:  gtk3
Requires:       gtk3
# gi.require_version("GtkSource", "4")
BuildRequires:  gtksourceview4
Requires:       gtksourceview4

Conflicts:      input-remapper

%generate_buildrequires
%pyproject_buildrequires -r


%description
An easy to use tool to change the mapping of your input device buttons. 
Supports mice, keyboards, gamepads, X11, Wayland, combined buttons and 
programmable macros. Allows mapping non-keyboard events (click, joystick, 
wheel) to keys of keyboard devices.
The program works at the evdev interface level, by filtering and redirecting 
the output of physical devices to that of virtual ones.


%prep
%autosetup -p1 -n %{reponame}-main
cp %{SOURCE1} ./
#Fix rpmlint errors
find inputremapper/injection/macros/ -iname "*.py" -type f -print0 | xargs -0 sed -i -e 's+\s*#\s*!/usr/bin/env python3++'



%build
%pyproject_wheel


%install
%pyproject_install
%pyproject_save_files inputremapper
mv %{buildroot}%{python3_sitelib}/etc %{buildroot}/etc
mv %{buildroot}%{python3_sitelib}/usr/bin %{buildroot}/usr/bin
mv %{buildroot}%{python3_sitelib}/usr/lib/systemd %{buildroot}/usr/lib/systemd
mv %{buildroot}%{python3_sitelib}/usr/lib/udev %{buildroot}/usr/lib/udev
mv %{buildroot}%{python3_sitelib}/usr/share %{buildroot}/usr/share
mkdir -p %{buildroot}/usr/share/dbus-1/system.d/

# clean up duplicate files
rm %{buildroot}%{_datadir}/%{reponame}/inputremapper.Control.conf
rm %{buildroot}%{_datadir}/%{reponame}/io.github.sezanzeb.input_remapper.metainfo.xml
rm %{buildroot}%{_datadir}/%{reponame}/%{reponame}-gtk.desktop
rm %{buildroot}%{_datadir}/%{reponame}/%{reponame}.policy
rm %{buildroot}%{_datadir}/%{reponame}/%{reponame}.svg


%post -n %{name}
%systemd_post %{reponame}.service


%preun -n %{name}
%systemd_preun %{reponame}.service


%postun -n %{name}
%systemd_postun_with_restart %{reponame}.service


%check
desktop-file-validate %{buildroot}/%{_datadir}/applications/%{reponame}-gtk.desktop
appstream-util validate-relax --nonet %{buildroot}%{_metainfodir}/*.metainfo.xml


# The tests have multiple incompatibilites with our build system/process, so
# unfortunately, they will be disabled for now (20250223, v2.1.1).
# See the discussion at:
# https://lists.fedorahosted.org/archives/list/devel@lists.fedoraproject.org/thread/PDTJOFHANNQZSWM4P5OLL4A5CBKSTWVC/

# See .github/workflows/test.yml
# Note that setting TMPDIR="${PWD}/test_tmp" tends to form paths that are too
# long for UNIX domain sockets, causing test failures, so we just use the
# default temporary directory.
export DATA_DIR='%{buildroot}%{_datadir}/%{reponame}'

# Make sure everything is at least importable:
# exclude the module from the test suite (v2.1.1) 
%pyproject_check_import -e inputremapper.bin.*

# Run the unit tests.

# Upstream would run them like this...
#   PYTHONPATH='%%{buildroot}%%{python3_sitelib}' PYTHONDONTWRITEBYTECODE=1 \
#       %%{python3} tests/test.py --start-dir unit || :
# ... but using pytest allows us to ignore modules and skip tests easily.

# E   gi.repository.GLib.GError: g-io-error-quark: Could not connect: No such
#     file or directory (1)
#ignore="${ignore-} --ignore=tests/unit/test_daemon.py"
# These tests only work when executed under a user whose home directory
# (based on the passwd entry, not on $HOME) begins with /tmp. Obviously, we
# can’t satisfy that, and we need to skip the affected tests.
#ignore="${ignore-} --ignore=tests/unit/test_migrations.py"

# New (v2.1.1) test failure, requires access to a display:
# ignore="${ignore-} --ignore=tests/integration/test_gui.py"

# TODO: What is wrong?
# E       AssertionError: Lists differ: [<Inp[37 chars]x7f3a2f82e6f0>,
#         <InputEvent for (3, 1, 16384) [131 chars]b10>] != [<Inp[37
#         chars]x7f3a3254b770>, <InputEvent for (3, 1, 16384) [235 chars]8f0>]
# E
# E       Second list contains 2 additional elements.
# E       First extra element 4:
# E       <InputEvent for (3, 0, 0) ABS_X at 0x7f3a2f82e360>
# E
# E       Diff is 1044 characters long. Set self.maxDiff to None to see it.
#k="${k-}${k+ and }not (TestRelToAbs and test_rel_to_abs)"

# This seems to fail only in Koji, not in mock…
# >       self.assertAlmostEqual(len(mouse_history), rel_rate * sleep * 2, delta=5)
# E       AssertionError: 51 != 60.0 within 5 delta (9.0 difference)
#k="${k-}${k+ and }not (TestAbsToRel and test_abs_to_rel)"

# These tests are based on timing/sleeps, and seem to experience flaky and/or
# arch-dependent failures in koji. The failures generally appear to be
# noisy/spurious.
#
#k="${k-}${k+ and }not (TestIdk and test_axis_switch)"
# >       self.assertAlmostEqual(len(mouse_history), rel_rate * sleep, delta=3)
# E       AssertionError: 26 != 30.0 within 3 delta (4.0 difference)
# >       self.assertLess(time.time() - start, sleep_time * 1.3)
# E       AssertionError: 0.5397047996520996 not less than 0.52
#k="${k-}${k+ and }not (TestMacros and test_2)"
# >       self.assertLess(time.time() - start, total_time * 1.2)
# E       AssertionError: 0.44843482971191406 not less than 0.432
#k="${k-}${k+ and }not (TestMacros and test_3)"
# >       self.assertLess(time.time() - start, total_time * 1.2)
# E       AssertionError: 0.511094331741333 not less than 0.48
#k="${k-}${k+ and }not (TestMacros and test_5)"
#         # this seems to have a tendency of injecting less wheel events,
#         # especially if the sleep is short
# >       self.assertGreater(actual_wheel_event_count, expected_wheel_event_count * 0.8)
# E       AssertionError: 2 not greater than 2.4000000000000004
#k="${k-}${k+ and }not (TestMacros and test_mouse)"

# %%pytest tests/unit ${ignore-} -k "${k-}" -v


%files -f %{pyproject_files}
%doc README.md README.Fedora
%license LICENSE
%{_datadir}/dbus-1/system.d/inputremapper.Control.conf
%{_sysconfdir}/xdg/autostart/%{reponame}-autoload.desktop
%{_bindir}/%{reponame}*
%{_unitdir}/%{reponame}.service
%{_udevrulesdir}/99-%{reponame}.rules
%{_datadir}/%{reponame}
%{_datadir}/icons/hicolor/scalable/apps/%{reponame}.svg

# deal with non-standard location of localization files
%exclude %dir %{_datadir}/%{reponame}/lang
%lang(fr) %{_datadir}/%{reponame}/lang/fr
%lang(fr) %{_datadir}/%{reponame}/lang/fr_FR
%lang(it) %{_datadir}/%{reponame}/lang/it
%lang(it) %{_datadir}/%{reponame}/lang/it_IT
%lang(pt) %{_datadir}/%{reponame}/lang/pt
%lang(pt) %{_datadir}/%{reponame}/lang/pt_BR
%lang(ru) %{_datadir}/%{reponame}/lang/ru
%lang(ru) %{_datadir}/%{reponame}/lang/ru_RU
%lang(sk) %{_datadir}/%{reponame}/lang/sk
%lang(sk) %{_datadir}/%{reponame}/lang/sk_SK
%lang(uk) %{_datadir}/%{reponame}/lang/uk
%lang(uk) %{_datadir}/%{reponame}/lang/uk_UA
%lang(zh) %{_datadir}/%{reponame}/lang/zh
%lang(zh) %{_datadir}/%{reponame}/lang/zh_CN

%{_datadir}/applications/%{reponame}-gtk.desktop
%{_datadir}/polkit-1/actions/%{reponame}.policy
%{_metainfodir}/*.metainfo.xml


%changelog
* Fri Oct 31 2025 Rankyn Bass <rankyn@proton.me> - input-remapper-git
- Modify to build from latest git

## START: Generated by rpmautospec
* Thu Jul 24 2025 Fedora Release Engineering <releng@fedoraproject.org> - 2.1.1-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_43_Mass_Rebuild

* Sun Jun 22 2025 Python Maint <python-maint@redhat.com> - 2.1.1-3
- Rebuilt for Python 3.14

* Thu Mar 06 2025 Alexander Ploumistos <alexpl@fedoraproject.org> - 2.1.1-2
- Add runtime dependency on psutil

* Mon Feb 24 2025 Alexander Ploumistos <alexpl@fedoraproject.org> - 2.1.1-1
- Update to v2.1.1
- Disable tests
- Remove explicit glib2 dependencies
- Clean up spec files
- Remove shebang lines from non-executable files

* Tue Sep 19 2023 Alexander Ploumistos <alexpl@fedoraproject.org> - 2.0.1-1
- Update to v2.0.1

* Mon May 29 2023 Alexander Ploumistos <alexpl@fedoraproject.org> - 2.0.0-5
- Work around non-standard location of localization files

* Tue May 23 2023 Alexander Ploumistos <alexpl@fedoraproject.org> - 2.0.0-4
- Import into Fedora proper (fedora#2180418)

* Tue May 23 2023 Alexander Ploumistos <alexpl@fedoraproject.org> - 2.0.0-3
- Remove duplicate files
- Add README.Fedora
- Drop direct systemctl calls

* Sun May 21 2023 Alexander Ploumistos <alexpl@fedoraproject.org> - 2.0.0-2
- Rename package to input-remapper
- Switch to autorelease and autochangelog
- Use find_lang macro
- Remove explicit python runtime dependencies

* Mon Mar 20 2023 Alexander Ploumistos <alexpl@fedoraproject.org> - 2.0.0-1
- Update to 2.0.0

* Thu Nov 17 2022 Alexander Ploumistos <alexpl@fedoraproject.org> - 1.5.0-2
- Rework files stanza

* Wed Nov 16 2022 Alexander Ploumistos <alexpl@fedoraproject.org> - 1.5.0-1
- Version 1.5.0
- Spec file based on Paweł Marciniak's <sunwire+repo@gmail.com> work
- Fix license

## END: Generated by rpmautospec
