# Sorgenti di Planner 0.2.0

Questo indice usa le versioni rilevate nel pacchetto di prova
`PlannerApp-linux.tar.gz` per Linux x86-64, compilato su Ubuntu 22.04.
Prima di collegarlo nelle note della release, confrontare le versioni con i
manifest dell'archivio finale e aggiornare le voci eventualmente cambiate.
SHA-256 dell'archivio di prova:
`ed39244c782313d2ffcfc19ab6b48b2198af606d830ca74d03e2e2ffc3096c5e`.

## Planner

Il [codice di Planner al tag v0.2.0](https://github.com/perni24/planner/tree/v0.2.0)
sara disponibile con la pubblicazione del tag. Include frontend, backend e
[script di build](backend/build_portable.py). La procedura di compilazione e
nella [guida di sviluppo](doc/GUIDA_SVILUPPO.md). L'archivio automatico del tag
contiene il codice di Planner, non i sorgenti di terze parti elencati qui sotto.

## Qt, Qt WebEngine e binding Python (Linux)

| Componente | Versione | Sorgenti |
| --- | --- | --- |
| Qt | `6.11.2` | [Archivio completo](https://download.qt.io/archive/qt/6.11/6.11.2/single/qt-everywhere-src-6.11.2.tar.xz) o [archivi per modulo](https://download.qt.io/archive/qt/6.11/6.11.2/submodules/) |
| Qt WebEngine, incluso Chromium | `6.11.2` | [Archivio del modulo](https://download.qt.io/archive/qt/6.11/6.11.2/submodules/qtwebengine-everywhere-src-6.11.2.tar.xz) |
| PyQt6 | `6.11.0` | [Distribuzione sorgente](https://pypi.org/project/PyQt6/6.11.0/#files) |
| PyQt6-WebEngine | `6.11.0` | [Distribuzione sorgente](https://pypi.org/project/PyQt6-WebEngine/6.11.0/#files) |
| PyQt6-sip | `13.13.0` | [Distribuzione sorgente](https://pypi.org/project/PyQt6-sip/13.13.0/#files) |
| QtPy | `2.4.3` | [Distribuzione sorgente](https://pypi.org/project/QtPy/2.4.3/#files) |
| ICU | `73.2` | [Release dei sorgenti ICU](https://github.com/unicode-org/icu/releases/tag/release-73-2) |

I wheel binari Riverbank [PyQt6-Qt6](https://pypi.org/project/PyQt6-Qt6/6.11.2/)
e [PyQt6-WebEngine-Qt6](https://pypi.org/project/PyQt6-WebEngine-Qt6/6.11.2/)
`6.11.2`, entrambi `manylinux_2_34_x86_64`, forniscono le librerie Qt incluse
nel pacchetto Linux. Planner copia questi binari e rimuove i componenti
inutilizzati; non ricompila Qt e non applica patch ai suoi sorgenti.

Tutte le **81 librerie, plugin e helper** sotto `_internal/PyQt6/Qt6/` hanno
SHA-256 identico ai binari ufficiali di Qt Online Installer per Linux x86-64.
Il confronto include:

- [Qt Base 6.11.2](https://download.qt.io/online/qtsdkrepository/linux_x64/desktop/qt6_6112/qt6_6112/qt.qt6.6112.linux_gcc_64/): `libQt6Core`, `libQt6Gui` e `libQt6Widgets` identici.
- [Qt WebEngine 6.11.2](https://download.qt.io/online/qtsdkrepository/linux_x64/extensions/qtwebengine/6112/x86_64/extensions.qtwebengine.6112.linux_gcc_64/): `libQt6WebEngineCore`, `libQt6WebEngineWidgets` e `QtWebEngineProcess` identici.
- [Qt PDF 6.11.2](https://download.qt.io/online/qtsdkrepository/linux_x64/extensions/qtpdf/6112/x86_64/extensions.qtpdf.6112.linux_gcc_64/) e ICU 73.2 (dall'indice Qt Base): librerie e plugin inclusi identici.

I binari distribuiti non contengono quindi modifiche aggiuntive di Riverbank
rispetto a quelli dell'installer Qt. Il confronto riguarda i binari inclusi,
non le risorse dei wheel o una ricompilazione dai sorgenti.

## Librerie di sistema (Linux)

Le versioni sono quelle di `licenses/system-manifest.json`. Per ogni pacchetto
sorgente, scaricare il descrittore `.dsc` e, **dalla stessa directory**, tutti
i file che esso elenca: sorgente originale ed eventuali patch o file di
pacchettizzazione Ubuntu. Il solo `.dsc` non contiene il codice. I descrittori
riportano gli SHA-256 per verificare i file scaricati.
Su Debian e Ubuntu, [`dget --download-only URL_DEL_DSC`](https://manpages.ubuntu.com/manpages/jammy/man1/dget.1.html)
scarica il descrittore e i file associati senza estrarli.

| Pacchetto sorgente | Versione Ubuntu | Descrittore |
| --- | --- | --- |
| `alsa-lib` | `1.2.6.1-1ubuntu1.2` | [Scarica .dsc](https://archive.ubuntu.com/ubuntu/pool/main/a/alsa-lib/alsa-lib_1.2.6.1-1ubuntu1.2.dsc) |
| `brotli` | `1.0.9-2ubuntu0.1` | [Scarica .dsc](https://archive.ubuntu.com/ubuntu/pool/main/b/brotli/brotli_1.0.9-2ubuntu0.1.dsc) |
| `bzip2` | `1.0.8-5ubuntu0.1` | [Scarica .dsc](https://archive.ubuntu.com/ubuntu/pool/main/b/bzip2/bzip2_1.0.8-5ubuntu0.1.dsc) |
| `dbus` | `1.12.20-2ubuntu4.1` | [Scarica .dsc](https://archive.ubuntu.com/ubuntu/pool/main/d/dbus/dbus_1.12.20-2ubuntu4.1.dsc) |
| `e2fsprogs` | `1.46.5-2ubuntu1.2` | [Scarica .dsc](https://archive.ubuntu.com/ubuntu/pool/main/e/e2fsprogs/e2fsprogs_1.46.5-2ubuntu1.2.dsc) |
| `expat` | `2.4.7-1ubuntu0.9` | [Scarica .dsc](https://archive.ubuntu.com/ubuntu/pool/main/e/expat/expat_2.4.7-1ubuntu0.9.dsc) |
| `fontconfig` | `2.13.1-4.2ubuntu5` | [Scarica .dsc](https://archive.ubuntu.com/ubuntu/pool/main/f/fontconfig/fontconfig_2.13.1-4.2ubuntu5.dsc) |
| `freetype` | `2.11.1+dfsg-1ubuntu0.4` | [Scarica .dsc](https://archive.ubuntu.com/ubuntu/pool/main/f/freetype/freetype_2.11.1+dfsg-1ubuntu0.4.dsc) |
| `glib2.0` | `2.72.4-0ubuntu2.11` | [Scarica .dsc](https://archive.ubuntu.com/ubuntu/pool/main/g/glib2.0/glib2.0_2.72.4-0ubuntu2.11.dsc) |
| `keyutils` | `1.6.1-2ubuntu3` | [Scarica .dsc](https://archive.ubuntu.com/ubuntu/pool/main/k/keyutils/keyutils_1.6.1-2ubuntu3.dsc) |
| `krb5` | `1.19.2-2ubuntu0.10` | [Scarica .dsc](https://archive.ubuntu.com/ubuntu/pool/main/k/krb5/krb5_1.19.2-2ubuntu0.10.dsc) |
| `libbsd` | `0.11.5-1` | [Scarica .dsc](https://archive.ubuntu.com/ubuntu/pool/main/libb/libbsd/libbsd_0.11.5-1.dsc) |
| `libcap2` | `1:2.44-1ubuntu0.22.04.3` | [Scarica .dsc](https://archive.ubuntu.com/ubuntu/pool/main/libc/libcap2/libcap2_2.44-1ubuntu0.22.04.3.dsc) |
| `libffi` | `3.4.2-4` | [Scarica .dsc](https://archive.ubuntu.com/ubuntu/pool/main/libf/libffi/libffi_3.4.2-4.dsc) |
| `libgcrypt20` | `1.9.4-3ubuntu3.3` | [Scarica .dsc](https://archive.ubuntu.com/ubuntu/pool/main/libg/libgcrypt20/libgcrypt20_1.9.4-3ubuntu3.3.dsc) |
| `libgpg-error` | `1.43-3` | [Scarica .dsc](https://archive.ubuntu.com/ubuntu/pool/main/libg/libgpg-error/libgpg-error_1.43-3.dsc) |
| `libmd` | `1.0.4-1build1` | [Scarica .dsc](https://archive.ubuntu.com/ubuntu/pool/main/libm/libmd/libmd_1.0.4-1build1.dsc) |
| `libpng1.6` | `1.6.37-3ubuntu0.7` | [Scarica .dsc](https://archive.ubuntu.com/ubuntu/pool/main/libp/libpng1.6/libpng1.6_1.6.37-3ubuntu0.7.dsc) |
| `libselinux` | `3.3-1build2` | [Scarica .dsc](https://archive.ubuntu.com/ubuntu/pool/main/libs/libselinux/libselinux_3.3-1build2.dsc) |
| `libx11` | `2:1.7.5-1ubuntu0.4` | [Scarica .dsc](https://archive.ubuntu.com/ubuntu/pool/main/libx/libx11/libx11_1.7.5-1ubuntu0.4.dsc) |
| `libxau` | `1:1.0.9-1build5` | [Scarica .dsc](https://archive.ubuntu.com/ubuntu/pool/main/libx/libxau/libxau_1.0.9-1build5.dsc) |
| `libxcb` | `1.14-3ubuntu3` | [Scarica .dsc](https://archive.ubuntu.com/ubuntu/pool/main/libx/libxcb/libxcb_1.14-3ubuntu3.dsc) |
| `libxcomposite` | `1:0.4.5-1build2` | [Scarica .dsc](https://archive.ubuntu.com/ubuntu/pool/main/libx/libxcomposite/libxcomposite_0.4.5-1build2.dsc) |
| `libxdamage` | `1:1.1.5-2build2` | [Scarica .dsc](https://archive.ubuntu.com/ubuntu/pool/main/libx/libxdamage/libxdamage_1.1.5-2build2.dsc) |
| `libxdmcp` | `1:1.1.3-0ubuntu5` | [Scarica .dsc](https://archive.ubuntu.com/ubuntu/pool/main/libx/libxdmcp/libxdmcp_1.1.3-0ubuntu5.dsc) |
| `libxext` | `2:1.3.4-1build1` | [Scarica .dsc](https://archive.ubuntu.com/ubuntu/pool/main/libx/libxext/libxext_1.3.4-1build1.dsc) |
| `libxfixes` | `1:6.0.0-1` | [Scarica .dsc](https://archive.ubuntu.com/ubuntu/pool/main/libx/libxfixes/libxfixes_6.0.0-1.dsc) |
| `libxkbcommon` | `1.4.0-1` | [Scarica .dsc](https://archive.ubuntu.com/ubuntu/pool/main/libx/libxkbcommon/libxkbcommon_1.4.0-1.dsc) |
| `libxkbfile` | `1:1.1.0-1build3` | [Scarica .dsc](https://archive.ubuntu.com/ubuntu/pool/main/libx/libxkbfile/libxkbfile_1.1.0-1build3.dsc) |
| `libxrandr` | `2:1.5.2-1build1` | [Scarica .dsc](https://archive.ubuntu.com/ubuntu/pool/main/libx/libxrandr/libxrandr_1.5.2-1build1.dsc) |
| `libxrender` | `1:0.9.10-1build4` | [Scarica .dsc](https://archive.ubuntu.com/ubuntu/pool/main/libx/libxrender/libxrender_0.9.10-1build4.dsc) |
| `libxtst` | `2:1.2.3-1ubuntu0.22.04.1` | [Scarica .dsc](https://archive.ubuntu.com/ubuntu/pool/main/libx/libxtst/libxtst_1.2.3-1ubuntu0.22.04.1.dsc) |
| `libzstd` | `1.4.8+dfsg-3build1` | [Scarica .dsc](https://archive.ubuntu.com/ubuntu/pool/main/libz/libzstd/libzstd_1.4.8+dfsg-3build1.dsc) |
| `lz4` | `1.9.3-2build2` | [Scarica .dsc](https://archive.ubuntu.com/ubuntu/pool/main/l/lz4/lz4_1.9.3-2build2.dsc) |
| `mesa` | `23.2.1-1ubuntu3.1~22.04.4` | [Scarica .dsc](https://archive.ubuntu.com/ubuntu/pool/main/m/mesa/mesa_23.2.1-1ubuntu3.1~22.04.4.dsc) |
| `ncurses` | `6.3-2ubuntu0.3` | [Scarica .dsc](https://archive.ubuntu.com/ubuntu/pool/main/n/ncurses/ncurses_6.3-2ubuntu0.3.dsc) |
| `nspr` | `2:4.35-0ubuntu0.22.04.1` | [Scarica .dsc](https://archive.ubuntu.com/ubuntu/pool/main/n/nspr/nspr_4.35-0ubuntu0.22.04.1.dsc) |
| `nss` | `2:3.98-0ubuntu0.22.04.5` | [Scarica .dsc](https://archive.ubuntu.com/ubuntu/pool/main/n/nss/nss_3.98-0ubuntu0.22.04.5.dsc) |
| `openssl` | `3.0.2-0ubuntu1.30` | [Scarica .dsc](https://archive.ubuntu.com/ubuntu/pool/main/o/openssl/openssl_3.0.2-0ubuntu1.30.dsc) |
| `pcre2` | `10.39-3ubuntu0.2` | [Scarica .dsc](https://archive.ubuntu.com/ubuntu/pool/main/p/pcre2/pcre2_10.39-3ubuntu0.2.dsc) |
| `pcre3` | `2:8.39-13ubuntu0.22.04.1` | [Scarica .dsc](https://archive.ubuntu.com/ubuntu/pool/main/p/pcre3/pcre3_8.39-13ubuntu0.22.04.1.dsc) |
| `readline` | `8.1.2-1` | [Scarica .dsc](https://archive.ubuntu.com/ubuntu/pool/main/r/readline/readline_8.1.2-1.dsc) |
| `sqlite3` | `3.37.2-2ubuntu0.8` | [Scarica .dsc](https://archive.ubuntu.com/ubuntu/pool/main/s/sqlite3/sqlite3_3.37.2-2ubuntu0.8.dsc) |
| `systemd` | `249.11-0ubuntu3.23` | [Scarica .dsc](https://archive.ubuntu.com/ubuntu/pool/main/s/systemd/systemd_249.11-0ubuntu3.23.dsc) |
| `util-linux` | `2.37.2-4ubuntu3.6` | [Scarica .dsc](https://archive.ubuntu.com/ubuntu/pool/main/u/util-linux/util-linux_2.37.2-4ubuntu3.6.dsc) |
| `xcb-util` | `0.4.0-1build2` | [Scarica .dsc](https://archive.ubuntu.com/ubuntu/pool/main/x/xcb-util/xcb-util_0.4.0-1build2.dsc) |
| `xcb-util-cursor` | `0.1.1-4ubuntu1` | [Scarica .dsc](https://archive.ubuntu.com/ubuntu/pool/universe/x/xcb-util-cursor/xcb-util-cursor_0.1.1-4ubuntu1.dsc) |
| `xcb-util-image` | `0.4.0-2` | [Scarica .dsc](https://archive.ubuntu.com/ubuntu/pool/main/x/xcb-util-image/xcb-util-image_0.4.0-2.dsc) |
| `xcb-util-keysyms` | `0.4.0-1build3` | [Scarica .dsc](https://archive.ubuntu.com/ubuntu/pool/main/x/xcb-util-keysyms/xcb-util-keysyms_0.4.0-1build3.dsc) |
| `xcb-util-renderutil` | `0.3.9-1build3` | [Scarica .dsc](https://archive.ubuntu.com/ubuntu/pool/main/x/xcb-util-renderutil/xcb-util-renderutil_0.3.9-1build3.dsc) |
| `xcb-util-wm` | `0.4.1-1.1build2` | [Scarica .dsc](https://archive.ubuntu.com/ubuntu/pool/main/x/xcb-util-wm/xcb-util-wm_0.4.1-1.1build2.dsc) |
| `xz-utils` | `5.2.5-2ubuntu1.2` | [Scarica .dsc](https://archive.ubuntu.com/ubuntu/pool/main/x/xz-utils/xz-utils_5.2.5-2ubuntu1.2.dsc) |
| `zlib` | `1:1.2.11.dfsg-2ubuntu9.2` | [Scarica .dsc](https://archive.ubuntu.com/ubuntu/pool/main/z/zlib/zlib_1.2.11.dfsg-2ubuntu9.2.dsc) |

Per PCRE2 `10.39-3ubuntu0.2` sono disponibili anche i link diretti al
[sorgente originale](https://archive.ubuntu.com/ubuntu/pool/main/p/pcre2/pcre2_10.39.orig.tar.gz)
e alle [patch Ubuntu](https://archive.ubuntu.com/ubuntu/pool/main/p/pcre2/pcre2_10.39-3ubuntu0.2.diff.gz).

## Runtime e strumenti

- [Python 3.14.10](https://www.python.org/downloads/release/python-31410/#files)
  e la versione riportata nel manifest del pacchetto Linux di prova.
- [PyInstaller 6.22.3](https://pypi.org/project/pyinstaller/6.22.3/#files)
  fornisce il bootloader. La versione di build e fissata in
  [requirements-dev.txt](backend/requirements-dev.txt).
- Le versioni e i riferimenti per gli altri pacchetti Python si trovano in
  `licenses/runtime-manifest.json`; le dipendenze frontend sono registrate in
  [package-lock.json](frontend/package-lock.json).

Per licenze e avvisi consultare [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)
e la directory `licenses/` del pacchetto. Per segnalare un link non piu
accessibile, aprire una [segnalazione](https://github.com/perni24/planner/issues).
