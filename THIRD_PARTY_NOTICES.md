# Third-Party Notices

## Solar Bold Duotone Icons

Planner uses the following icons from the Solar Bold Duotone Icons collection:

- `arrow-left.svg`
- `arrow-right.svg`
- `calendar.svg`
- `home.svg`
- `settings.svg`

Author: Solar Icons  
Source: [Solar Bold Duotone Icons on SVG Repo](https://www.svgrepo.com/collection/solar-bold-duotone-icons/)  
License: [CC Attribution License](https://www.svgrepo.com/page/licensing/#CC%20Attribution)

Modifications: files were renamed and rendered at different sizes and colors using CSS masks. The original SVG geometry was not modified.

## Linux Desktop Components

The following components are used by the Linux desktop build. They are not
included in the Windows build, which uses the system WebView2 Runtime.
Configured Python package versions are listed below. The exact versions and
copies of the upstream license files shipped in each Linux build are recorded
in `licenses/manifest.json`, next to the executable. These files are copied
without modifying their contents.

### QtPy

- Author: The Spyder Development Team and contributors
- Configured version: 2.4.3
- License: MIT
- Project and source: [QtPy](https://github.com/spyder-ide/qtpy)
- Release: [QtPy on PyPI](https://pypi.org/project/QtPy/2.4.3/)

### PyQt6 and PyQt6-WebEngine

Author: Riverbank Computing Limited.

Configured versions: PyQt6 6.11.0 and PyQt6-WebEngine 6.11.0.

License of the public PyPI bindings used by this project: GNU GPL version 3
(`GPL-3.0-only`), not LGPL.

Projects: [PyQt6](https://www.riverbankcomputing.com/software/pyqt/)
and [PyQt-WebEngine](https://www.riverbankcomputing.com/software/pyqtwebengine/).

Releases and source distributions: [PyQt6](https://pypi.org/project/PyQt6/6.11.0/)
and [PyQt6-WebEngine](https://pypi.org/project/PyQt6-WebEngine/6.11.0/)

The Linux build also includes the PyQt6-sip runtime. Its upstream license files
and exact version are preserved under `licenses/PyQt6-sip/` and in the manifest.
See [PyQt6-sip](https://pypi.org/project/PyQt6-sip/).

### Qt 6 and Qt WebEngine Libraries

Authors: The Qt Company Ltd. and contributors; third-party components retain
their respective copyright notices.

The Qt shared libraries are supplied by the `PyQt6-Qt6` and
`PyQt6-WebEngine-Qt6` wheels. Their upstream wheel license files contain the
GNU Lesser General Public License version 3. This is separate from the GPLv3
license of the Python bindings above and does not replace the licenses of
third-party code included in Qt or Chromium.

Packages: [PyQt6-Qt6](https://pypi.org/project/PyQt6-Qt6/)
and [PyQt6-WebEngine-Qt6](https://pypi.org/project/PyQt6-WebEngine-Qt6/).

Licensing: [Qt licensing](https://doc.qt.io/qt-6/licensing.html)
and [Qt WebEngine licensing](https://doc.qt.io/qt-6.11/qtwebengine-licensing.html).

Upstream source releases: [Qt source archives](https://download.qt.io/official_releases/qt/)

### Chromium and Other Qt Third-Party Components

Qt WebEngine incorporates Chromium and other third-party software under
multiple licenses. These components are not all covered by a single BSD, GPL
or LGPL notice. Their individual copyright notices and license terms must be
preserved for the actual version distributed.

References: [Qt WebEngine third-party licensing](https://doc.qt.io/qt-6.11/qtwebengine-licensing.html)
and [Qt third-party libraries](https://doc.qt.io/qt-6/qtthirdparty.html).

The wheel license copies and manifest are an inventory of available materials,
not a complete Chromium notice bundle or a corresponding-source distribution.
Before publishing the Linux package, the release maintainer must complete the
version-specific Qt/Chromium notice and corresponding-source review described
in `doc/TODO.md`. The Linux artifact remains excluded from public release assets
until that review and the native tests are complete. Links in this file do not
replace license texts, required notices or corresponding-source obligations.
