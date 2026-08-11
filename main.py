from __future__ import annotations

import json
import shutil
import subprocess
import sys
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Callable

from PySide6.QtCore import QObject, QThread, Signal, Qt
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

CORE_GMS: dict[str, str] = {
    "com.google.android.gms": "Google Play services",
    "com.google.android.gms.policy_sidecar_aps": "Google Play services policy sidecar aps",
    "com.google.android.gsf": "Google Services Framework",
    "com.android.vending": "Google Play Store",
    "com.google.android.backuptransport": "Google Backup Transport",
    "com.google.android.syncadapters.contacts": "Google Contacts Sync",
    "com.google.android.syncadapters.calendar": "Google Calendar Sync",
    "com.google.android.onetimeinitializer": "Google One Time Initializer",
    "com.google.android.partnersetup": "Google Partner Setup",
    "com.google.android.setupwizard": "Google Setup Wizard",
    "com.google.android.setupwizard.default": "Google Setup Wizard (default)",
    "com.google.android.setupwizard.tablet": "Google Setup Wizard (tablet)",
    "com.google.android.configupdater": "Google Config Updater",
    "com.google.android.ext.services": "Google Ext Services",
    "com.google.android.ext.shared": "Google Ext Shared",
    "com.google.android.carriersetup": "Google Carrier Setup",
    "com.google.android.apps.restore": "Google Restore",
    "com.google.android.apps.pixelmigrate": "Google Pixel Migrate",
    "com.google.android.webview": "Android System WebView (Google)",
    "com.google.android.webview.stub": "Android System WebView Stub",
    "com.google.android.ims": "Carrier Services / IMS",
    "com.google.android.storagemanager": "Google Storage Manager",
    "com.google.android.printservice.recommendation": "Google Print Service Recommendation",
    "com.google.android.apps.pixel.psi": "Device Intelligence",
    "com.google.android.verifier": "Android Developer Verifier",
    "com.google.android.apps.work.clouddpc": "Android Device Policy",
    "com.google.android.apps.pixel.tabby": "Pixel Audio Services",
}

GOOGLE_APPS: dict[str, str] = {
    "com.google.android.feedback": "Google Feedback",
    "com.google.android.tts": "Speech Services by Google",
    "com.google.android.projection.gearhead.stub": "Android Auto Stub",
    "com.google.android.projection.gearhead": "Android Auto",
    "com.google.android.googlequicksearchbox": "Google app / Search",
    "com.google.android.apps.turbo": "Device Health Services",
    "com.google.android.markup": "Markup",
    "com.google.android.soundpicker": "Google Sounds / Sound Picker",
    "com.google.android.apps.wellbeing": "Digital Wellbeing",
    "com.google.android.calendar": "Google Calendar",
    "com.google.android.gm.exchange": "Gmail Exchange Services",
    "com.google.android.gm": "Gmail",
    "com.google.android.apps.bard": "Gemini",
    "com.google.android.apps.nexuslauncher": "Pixel Launcher",
    "com.google.android.apps.wallpaper": "Google Wallpapers",
    "com.google.android.as": "Android System Intelligence / Device Personalization",
    "com.google.android.deskclock": "Google Clock",
    "com.google.android.apps.maps": "Google Maps",
    "com.google.android.apps.messaging": "Google Messages",
    "com.google.android.apps.photos": "Google Photos",
    "com.google.android.youtube": "YouTube",
    "com.google.android.calculator": "Google Calculator",
    "com.google.android.tag": "Google Tag",
    "com.google.android.apps.books": "Google Play Books",
    "com.android.chrome": "Google Chrome",
    "com.google.android.apps.docs": "Google Drive",
    "com.google.android.keep": "Google Keep",
    "com.google.android.videos": "Google TV / Play Movies",
    "com.google.android.apps.magazines": "Google News / Play Newsstand",
    "com.google.android.play.games": "Google Play Games",
    "com.google.android.marvin.talkback": "Android Accessibility Suite / TalkBack",
    "com.google.android.apps.youtube.music": "YouTube Music",
    "com.google.android.apps.recorder": "Google Recorder",
    "com.google.android.googlecamera": "Google Camera",
    "com.google.android.apps.tachyon": "Google Meet / Duo",
    "com.google.android.apps.walletnfcrel": "Google Wallet",
    "com.google.android.inputmethod.latin": "Gboard",
    "com.google.android.apps.translate": "Google Translate",
    "com.google.vr.vrcore": "Google VR Services",
    "com.google.android.contacts": "Google Contacts",
    "com.google.android.dialer": "Google Phone / Dialer",
    "com.google.android.apps.enterprise.dmagent": "Google Enterprise Device Management Agent",
    "com.google.android.apps.docs.editors.docs": "Google Docs",
    "com.google.earth": "Google Earth",
    "com.google.android.apps.fitness": "Google Fit",
    "com.google.android.talk": "Google Hangouts",
    "com.google.android.apps.inputmethod.hindi": "Google Indic Keyboard (Hindi)",
    "com.google.android.inputmethod.japanese": "Google Japanese Input",
    "com.google.android.inputmethod.korean": "Google Korean Input",
    "com.google.android.inputmethod.pinyin": "Google Pinyin Input",
    "com.google.android.apps.tycho": "Google Fi / Tycho",
    "com.google.android.apps.docs.editors.sheets": "Google Sheets",
    "com.google.android.apps.docs.editors.slides": "Google Slides",
    "com.google.android.street": "Google Street View",
    "com.google.android.apps.inputmethod.zhuyin": "Google Zhuyin Input",
    "com.google.android.apps.gcs": "Google Connectivity Services",
    "com.google.android.apps.multidevice.client": "Google Multi-Device Client",
    "com.google.android.apps.searchlite": "Google Go",
    "com.google.android.apps.photosgo": "Gallery",
    "com.google.android.apps.nbu.files": "Files by Google",
    "com.google.android.apps.accessibility.voiceaccess": "Voice Access",
    "com.google.android.apps.accessibility.magnifier": "Magnifier",
    "com.google.android.apps.mapslite": "Google Maps Go",
    "com.google.android.gm.lite": "Gmail Go",

}

ALL_GOOGLE = {**CORE_GMS, **GOOGLE_APPS}


@dataclass(frozen=True)
class Device:
    serial: str
    description: str

    def __str__(self) -> str:
        return self.description


def run_adb(serial: str | None, args: list[str], timeout: int = 30) -> subprocess.CompletedProcess[str]:
    adb = shutil.which("adb")
    if not adb:
        raise RuntimeError("ADB was not found in PATH. Install Android platform-tools first.")

    cmd = [adb]
    if serial:
        cmd += ["-s", serial]
    cmd += args

    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=timeout,
        creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
    )


def list_devices() -> list[Device]:
    result = run_adb(None, ["devices", "-l"])
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "adb devices failed")

    devices: list[Device] = []
    for line in result.stdout.splitlines()[1:]:
        line = line.strip()
        if not line:
            continue
        parts = line.split()
        if len(parts) < 2 or parts[1] != "device":
            continue

        serial = parts[0]
        attrs = {}
        for part in parts[2:]:
            if ":" in part:
                k, v = part.split(":", 1)
                attrs[k] = v

        model = attrs.get("model", "Android device").replace("_", " ")
        product = attrs.get("product")
        suffix = f" - {product}" if product and product != model else ""
        devices.append(Device(serial, f"{model}{suffix} [{serial}]"))
    return devices


def get_device_packages(serial: str) -> set[str]:
    # -u includes packages uninstalled for the current user but still present in
    # the system image, which is important because Revert can reinstall them.
    result = run_adb(serial, ["shell", "pm", "list", "packages", "-u"])
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "Could not list packages")

    packages: set[str] = set()
    for line in result.stdout.splitlines():
        line = line.strip()
        if line.startswith("package:"):
            packages.add(line[len("package:"):].strip())
    return packages


def get_device_api_level(serial: str) -> int:
    result = run_adb(serial, ["shell", "getprop", "ro.build.version.sdk"])
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "Could not determine Android API level")
    value = result.stdout.strip()
    try:
        return int(value)
    except ValueError as exc:
        raise RuntimeError(f"Could not determine Android API level. Device returned: {value or 'nothing'}") from exc


def get_device_identity(serial: str) -> dict[str, str]:
    result = run_adb(serial, ["shell", "getprop"])
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "Could not identify device")

    properties: dict[str, str] = {}
    for line in result.stdout.splitlines():
        if line.startswith("[") and "]: [" in line and line.endswith("]"):
            key, value = line[1:].split("]: [", 1)
            properties[key] = value[:-1]

    keys = (
        "ro.product.manufacturer",
        "ro.product.model",
        "ro.product.device",
        "ro.build.version.release",
        "ro.build.version.sdk",
        "ro.build.version.incremental",
        "ro.build.fingerprint",
    )
    identity = {key: properties.get(key, "") for key in keys}
    if not identity["ro.product.model"] or not identity["ro.build.fingerprint"]:
        raise RuntimeError("Could not identify the device model and software build")
    return identity


def defaults_directory() -> Path:
    directory = Path(__file__).resolve().parent / "defaults"
    directory.mkdir(exist_ok=True)
    return directory


def matching_bloat_config(identity: dict[str, str]) -> dict | None:
    for config_path in sorted(defaults_directory().glob("*.json")):
        try:
            config = json.loads(config_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if config.get("device") == identity and isinstance(config.get("packages"), list):
            return config
    return None


def save_bloat_config(identity: dict[str, str], packages: list[str]) -> Path:
    identity_text = json.dumps(identity, sort_keys=True).encode("utf-8")
    filename = f"{sha256(identity_text).hexdigest()[:16]}.json"
    path = defaults_directory() / filename
    config = {
        "device": identity,
        "packages": sorted(packages),
    }
    path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    return path


class OperationWorker(QObject):
    progress = Signal(str)
    finished = Signal(int, int)
    failed = Signal(str)

    def __init__(self, serial: str, packages: list[str], mode: str, revert: bool = False):
        super().__init__()
        self.serial = serial
        self.packages = packages
        self.mode = mode  # "disable" or "uninstall"
        self.revert = revert

    def _exec(self, args: list[str]) -> tuple[bool, str]:
        result = run_adb(self.serial, args)
        output = (result.stdout + "\n" + result.stderr).strip()
        return result.returncode == 0, output

    def run(self) -> None:
        try:
            succeeded = 0
            failed = 0

            for index, package in enumerate(self.packages, start=1):
                friendly = ALL_GOOGLE.get(package, package)
                prefix = f"[{index}/{len(self.packages)}] {friendly} ({package})"

                if self.revert:
                    # A disabled package is already installed for the user, so
                    # enable it first. If it was uninstalled for user 0, fall
                    # back to restoring the existing system package.
                    ok_enable, out_enable = self._exec(
                        ["shell", "pm", "enable", "--user", "0", package]
                    )
                    ok_install, out_install = (False, "")
                    if not ok_enable:
                        ok_install, out_install = self._exec(
                            ["shell", "cmd", "package", "install-existing", "--user", "0", package]
                        )
                    ok = ok_install or ok_enable
                    detail = " | ".join(x for x in (out_enable, out_install) if x)
                    action = "RESTORE"
                elif self.mode == "uninstall":
                    ok, detail = self._exec(
                        ["shell", "pm", "uninstall", "--user", "0", package]
                    )
                    action = "UNINSTALL"
                else:
                    ok, detail = self._exec(
                        ["shell", "pm", "disable-user", "--user", "0", package]
                    )
                    action = "DISABLE"

                if ok:
                    succeeded += 1
                    self.progress.emit(f"{action}: OK - {prefix}")
                else:
                    failed += 1
                    self.progress.emit(f"{action}: FAILED - {prefix} :: {detail or 'unknown error'}")

            self.finished.emit(succeeded, failed)
        except Exception as exc:
            self.failed.emit(str(exc))


class InstallWorker(QObject):
    progress = Signal(str)
    finished = Signal(bool, str)

    def __init__(self, serial: str, apk_path: str, api_level: int):
        super().__init__()
        self.serial = serial
        self.apk_path = apk_path
        self.api_level = api_level

    def run(self) -> None:
        try:
            result = run_adb(
                self.serial,
                [
                    "install",
                    *(["--bypass-low-target-sdk-block"] if self.api_level >= 34 else []),
                    self.apk_path,
                ],
                timeout=120,
            )
            output = (result.stdout + "\n" + result.stderr).strip()
            self.finished.emit(result.returncode == 0, output or "ADB install completed.")
        except Exception as exc:
            self.finished.emit(False, str(exc))


class LogDialog(QDialog):
    def __init__(self, title: str, parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(760, 420)

        layout = QVBoxLayout(self)
        self.label = QLabel("Starting...")
        self.label.setWordWrap(True)
        self.label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.label.setAlignment(Qt.AlignTop | Qt.AlignLeft)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.label)
        layout.addWidget(scroll)

        self.buttons = QDialogButtonBox(QDialogButtonBox.Close)
        self.buttons.button(QDialogButtonBox.Close).setEnabled(False)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)

        self.lines: list[str] = []

    def append(self, line: str) -> None:
        self.lines.append(line)
        self.label.setText("\n".join(self.lines))

    def complete(self, succeeded: int, failed: int) -> None:
        self.append(f"\nFinished: {succeeded} succeeded, {failed} failed.")
        self.buttons.button(QDialogButtonBox.Close).setEnabled(True)

    def error(self, message: str) -> None:
        self.append(f"\nERROR: {message}")
        self.buttons.button(QDialogButtonBox.Close).setEnabled(True)


class DeGooglerWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.debug_gather = "--debug-gather" in sys.argv
        self.setWindowTitle("ADB DeGoogler — GATHER MODE" if self.debug_gather else "ADB DeGoogler")
        self.resize(920, 760)

        self.device_map: dict[str, Device] = {}
        self.package_checkboxes: dict[str, QCheckBox] = {}
        self.current_detected: set[str] = set()
        self.worker_thread: QThread | None = None
        self.worker: OperationWorker | None = None
        self.install_thread: QThread | None = None
        self.install_worker: InstallWorker | None = None
        self.current_bloat_config: dict | None = None

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(12)

        device_row = QHBoxLayout()
        device_row.addWidget(QLabel("Device:"))
        self.device_combo = QComboBox()
        self.device_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.device_combo.currentIndexChanged.connect(self.on_device_changed)
        device_row.addWidget(self.device_combo, 1)

        refresh_btn = QPushButton("Refresh Devices")
        refresh_btn.clicked.connect(self.refresh_devices)
        device_row.addWidget(refresh_btn)
        root.addLayout(device_row)

        self.pages = QTabWidget()
        self.pages.setTabPosition(QTabWidget.North)
        root.addWidget(self.pages, 1)

        removal_page = QWidget()
        removal_root = QVBoxLayout(removal_page)

        removal_title = QLabel("GATHER MODE" if self.debug_gather else "Remove Google apps")
        removal_title.setStyleSheet("font-size: 24px; font-weight: 700;")
        removal_root.addWidget(removal_title)
        removal_description = QLabel(
            "Select any device specific bloatware and then press start"
            if self.debug_gather
            else "Scan an authorized Android device and disable or uninstall selected Google, OEM, and system packages."
        )
        removal_description.setWordWrap(True)
        removal_root.addWidget(removal_description)
        removal_warning = QLabel(
            "Warning: removing system applications can break "
            "setup/restore flows, and other system behavior. Fully Uninstall uses Android's per-user uninstall; restoring "
            "may not be possible without reflashing the ROM."
        )
        removal_warning.setWordWrap(True)
        removal_warning.setStyleSheet("padding: 10px; border: 1px solid palette(mid); border-radius: 6px;")
        removal_root.addWidget(removal_warning)

        preset_row = QHBoxLayout()
        for text, callback in (
            ("Uncheck All", self.preset_uncheck_all),
            ("Remove Apps Only", self.preset_apps_only),
            ("Remove All GMS", self.preset_all_gms),
            ("Select All Listed", self.preset_all_listed),
        ):
            btn = QPushButton(text)
            btn.clicked.connect(callback)
            preset_row.addWidget(btn)
        self.oem_bloat_btn = QPushButton("OEM Bloat")
        self.oem_bloat_btn.clicked.connect(self.preset_oem_bloat)
        self.oem_bloat_btn.setVisible(False)
        preset_row.addWidget(self.oem_bloat_btn)
        preset_row.addStretch(1)
        removal_root.addLayout(preset_row)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll_frame = QFrame()
        self.scroll_layout = QVBoxLayout(self.scroll_frame)
        self.scroll_layout.setAlignment(Qt.AlignTop)
        self.scroll.setWidget(self.scroll_frame)
        removal_root.addWidget(self.scroll, 1)

        self.empty_label = QLabel("Select a connected ADB device to scan its packages.")
        self.empty_label.setAlignment(Qt.AlignCenter)
        self.empty_label.setWordWrap(True)
        self.scroll_layout.addWidget(self.empty_label)

        self.full_uninstall = QCheckBox("Fully Uninstall")
        self.full_uninstall.setToolTip(
            "Unchecked: adb shell pm disable-user --user 0 PACKAGE\n"
            "Checked: adb shell pm uninstall --user 0 PACKAGE"
        )
        removal_root.addWidget(self.full_uninstall)

        button_row = QHBoxLayout()
        self.start_btn = QPushButton("Start")
        self.start_btn.setMinimumHeight(42)
        self.start_btn.clicked.connect(self.start_operation)
        button_row.addWidget(self.start_btn)

        self.revert_btn = QPushButton("Revert")
        self.revert_btn.setMinimumHeight(42)
        self.revert_btn.clicked.connect(self.revert_operation)
        button_row.addWidget(self.revert_btn)
        removal_root.addLayout(button_row)
        self.pages.addTab(removal_page, "Remove Google apps")

        install_page = QWidget()
        install_root = QVBoxLayout(install_page)
        install_title = QLabel("Install F-Droid")
        install_title.setStyleSheet("font-size: 24px; font-weight: 700;")
        install_root.addWidget(install_title)
        install_description = QLabel(
            "Install the legacy F-Droid APK bundled with this app on the selected Android device."
        )
        install_description.setWordWrap(True)
        install_root.addWidget(install_description)

        install_warning = QLabel(
            "Important: this is a very old version of F-Droid. It is still functional, but it must be updated "
            "before you use it. Open F-Droid after installation and run its update process."
        )
        install_warning.setWordWrap(True)
        install_warning.setStyleSheet("padding: 12px; border: 1px solid palette(mid); border-radius: 6px;")
        install_root.addWidget(install_warning)

        self.install_path_label = QLabel()
        self.install_path_label.setWordWrap(True)
        install_root.addWidget(self.install_path_label)
        self.install_btn = QPushButton("Install F-Droid APK")
        self.install_btn.setMinimumHeight(42)
        self.install_btn.clicked.connect(self.install_fdroid)
        install_root.addWidget(self.install_btn)
        self.install_status = QLabel("Ready.")
        self.install_status.setWordWrap(True)
        install_root.addWidget(self.install_status)
        install_root.addStretch(1)
        self.pages.addTab(install_page, "Install F-Droid")
        self.install_path_label.setText(f"APK: {self.fdroid_apk_path()}")

        self.status = QLabel("Ready.")
        root.addWidget(self.status)

        self.refresh_devices()

    def fdroid_apk_path(self) -> str:
        return str(Path(__file__).resolve().parent / "alternatives" / "appstore" / "org.fdroid.fdroid.apk")

    def install_fdroid(self) -> None:
        serial = self.current_serial()
        if not serial:
            QMessageBox.warning(self, "No device", "Choose an authorized ADB device first.")
            return
        apk_path = self.fdroid_apk_path()
        if not Path(apk_path).is_file():
            QMessageBox.critical(self, "APK not found", f"Could not find the bundled APK:\n{apk_path}")
            return
        try:
            api_level = get_device_api_level(serial)
        except Exception as exc:
            QMessageBox.critical(self, "Could not determine API level", str(exc))
            return
        flag_note = " with the API 34+ compatibility flag" if api_level >= 34 else ""
        self.install_btn.setEnabled(False)
        self.install_status.setText(f"Android API level {api_level} detected. Installing legacy F-Droid{flag_note}...")
        thread = QThread(self)
        worker = InstallWorker(serial, apk_path, api_level)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)

        def done(ok: bool, output: str) -> None:
            self.install_status.setText(("Install succeeded. " if ok else "Install failed. ") + output)
            if ok:
                QMessageBox.information(self, "F-Droid installed", "F-Droid was installed. Open it and run an update before using it.")
            self.install_btn.setEnabled(True)
            thread.quit()

        worker.finished.connect(done)
        thread.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        self.install_thread = thread
        self.install_worker = worker
        thread.finished.connect(lambda: setattr(self, "install_thread", None))
        thread.finished.connect(lambda: setattr(self, "install_worker", None))
        thread.start()

    def clear_package_list(self) -> None:
        while self.scroll_layout.count():
            item = self.scroll_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        self.package_checkboxes.clear()

    def refresh_devices(self) -> None:
        self.device_combo.blockSignals(True)
        self.device_combo.clear()
        self.device_map.clear()
        try:
            devices = list_devices()
        except Exception as exc:
            self.status.setText(str(exc))
            self.device_combo.blockSignals(False)
            self.clear_package_list()
            self.scroll_layout.addWidget(QLabel(str(exc)))
            return

        if not devices:
            self.device_combo.addItem("No authorized ADB devices found", None)
            self.status.setText("No authorized ADB devices found.")
        else:
            for device in devices:
                self.device_map[device.serial] = device
                self.device_combo.addItem(device.description, device.serial)
            self.status.setText(f"Found {len(devices)} device(s).")

        self.device_combo.blockSignals(False)
        self.on_device_changed(self.device_combo.currentIndex())

    def current_serial(self) -> str | None:
        data = self.device_combo.currentData()
        return str(data) if data else None

    def on_device_changed(self, _index: int) -> None:
        serial = self.current_serial()
        self.clear_package_list()
        self.current_detected.clear()
        self.current_bloat_config = None
        self.oem_bloat_btn.setVisible(False)

        if not serial:
            self.scroll_layout.addWidget(QLabel("Select a connected ADB device to scan its packages."))
            return

        try:
            self.current_bloat_config = matching_bloat_config(get_device_identity(serial))
        except Exception:
            # Package scanning remains useful even if an older device exposes
            # incomplete build properties.
            self.current_bloat_config = None
        self.oem_bloat_btn.setVisible(self.current_bloat_config is not None)

        try:
            packages = get_device_packages(serial)
        except Exception as exc:
            self.scroll_layout.addWidget(QLabel(f"Package scan failed: {exc}"))
            self.status.setText(f"Package scan failed: {exc}")
            return

        detected_google = sorted(
            set(ALL_GOOGLE) & packages,
            key=lambda p: (p not in CORE_GMS, ALL_GOOGLE[p].lower()),
        )
        # Include system packages as well as ordinary installed apps. This is
        # intentional: OEM bloat is often preloaded as a system package.
        detected_other = sorted(packages - set(ALL_GOOGLE), key=str.lower)
        detected = detected_google + detected_other
        self.current_detected = set(detected)

        if not detected:
            self.scroll_layout.addWidget(QLabel("No packages were found on this device."))
            self.status.setText("No packages detected.")
            return

        core_heading = QLabel("Core GMS / framework")
        core_heading.setStyleSheet("font-weight: 700; margin-top: 4px;")
        self.scroll_layout.addWidget(core_heading)

        for package in detected:
            if package not in CORE_GMS:
                continue
            self.add_package_checkbox(package)

        apps_heading = QLabel("Google apps")
        apps_heading.setStyleSheet("font-weight: 700; margin-top: 12px;")
        self.scroll_layout.addWidget(apps_heading)

        for package in detected_google:
            if package in CORE_GMS:
                continue
            self.add_package_checkbox(package)

        oem_heading = QLabel("OEM / non-Google packages")
        oem_heading.setStyleSheet("font-weight: 700; margin-top: 12px;")
        oem_heading.setToolTip(
            "Includes both user-installed apps and preloaded system packages. "
            "Only select packages you have identified as safe to disable or uninstall."
        )
        self.scroll_layout.addWidget(oem_heading)
        for package in detected_other:
            self.add_package_checkbox(package, friendly=package)

        core_count = len([p for p in detected_google if p in CORE_GMS])
        google_app_count = len(detected_google) - core_count
        self.status.setText(
            f"Detected {len(detected)} packages: {google_app_count} Google apps, "
            f"{core_count} core GMS, {len(detected_other)} OEM/non-Google."
        )

    def add_package_checkbox(self, package: str, friendly: str | None = None) -> None:
        cb = QCheckBox(f"{friendly or ALL_GOOGLE[package]}   [{package}]")
        cb.setProperty("package", package)
        self.package_checkboxes[package] = cb
        self.scroll_layout.addWidget(cb)

    def preset_uncheck_all(self) -> None:
        for cb in self.package_checkboxes.values():
            cb.setChecked(False)

    def preset_apps_only(self) -> None:
        for package, cb in self.package_checkboxes.items():
            cb.setChecked(package in GOOGLE_APPS)

    def preset_all_gms(self) -> None:
        for package, cb in self.package_checkboxes.items():
            cb.setChecked(package in ALL_GOOGLE)

    def preset_all_listed(self) -> None:
        """Explicit opt-in for every displayed package, including OEM/system ones."""
        for cb in self.package_checkboxes.values():
            cb.setChecked(True)

    def preset_oem_bloat(self) -> None:
        """Add saved device-specific bloat selections to the current selection."""
        if not self.current_bloat_config:
            return
        for package in self.current_bloat_config["packages"]:
            checkbox = self.package_checkboxes.get(package)
            if checkbox:
                checkbox.setChecked(True)

    def selected_packages(self) -> list[str]:
        return [package for package, cb in self.package_checkboxes.items() if cb.isChecked()]

    def confirm_operation(self, packages: list[str], revert: bool) -> bool:
        core_selected = [p for p in packages if p in CORE_GMS]
        non_google_selected = [p for p in packages if p not in ALL_GOOGLE]

        if revert:
            text = (
                f"Restore/re-enable {len(packages)} selected package(s) for user 0?\n\n"
                "Revert will try 'cmd package install-existing' and then 'pm enable'."
            )
            icon = QMessageBox.Question
        else:
            action = "UNINSTALL for user 0" if self.full_uninstall.isChecked() else "DISABLE for user 0"
            text = f"{action} on {len(packages)} selected package(s)?"
            if core_selected:
                text += (
                    f"\n\n{len(core_selected)} selected package(s) are classified as core GMS/framework. "
                    "This can break core Android/Google functionality and may make apps unstable or unusable."
                )
            if non_google_selected:
                text += (
                    f"\n\n{len(non_google_selected)} selected package(s) are OEM/non-Google packages. "
                    "Disabling or uninstalling the wrong system package can break device features or boot/setup."
                )
            if self.full_uninstall.isChecked():
                text += (
                    "\n\nFully Uninstall is more disruptive. The packages normally remain in the system image, "
                    "but a factory reset is the most reliable way to return to the original state."
                )
            icon = QMessageBox.Warning

        box = QMessageBox(icon, "Confirm operation", text, QMessageBox.Yes | QMessageBox.No, self)
        box.setDefaultButton(QMessageBox.No)
        return box.exec() == QMessageBox.Yes

    def start_operation(self) -> None:
        serial = self.current_serial()
        packages = self.selected_packages()
        if not serial:
            QMessageBox.warning(self, "No device", "Choose an authorized ADB device first.")
            return
        if not packages:
            QMessageBox.information(self, "Nothing selected", "Check at least one package first.")
            return

        if self.debug_gather:
            try:
                identity = get_device_identity(serial)
                config_path = save_bloat_config(identity, packages)
            except Exception as exc:
                QMessageBox.critical(self, "Could not save gather data", str(exc))
                return
            self.status.setText(f"Saved {len(packages)} package selection(s) to {config_path}")
            QMessageBox.information(
                self,
                "Gather data saved",
                f"Saved device-specific bloat selections for {identity['ro.product.model']}.\n\n{config_path}",
            )
            self.current_bloat_config = matching_bloat_config(identity)
            self.oem_bloat_btn.setVisible(True)
            return

        if not self.confirm_operation(packages, revert=False):
            return

        mode = "uninstall" if self.full_uninstall.isChecked() else "disable"
        self.run_operation(serial, packages, mode=mode, revert=False)

    def revert_operation(self) -> None:
        serial = self.current_serial()
        packages = self.selected_packages()
        if not serial:
            QMessageBox.warning(self, "No device", "Choose an authorized ADB device first.")
            return
        if not packages:
            QMessageBox.information(self, "Nothing selected", "Check the packages you want to restore first.")
            return
        if not self.confirm_operation(packages, revert=True):
            return

        self.run_operation(serial, packages, mode="disable", revert=True)

    def run_operation(self, serial: str, packages: list[str], mode: str, revert: bool) -> None:
        dialog = LogDialog("Revert packages" if revert else "Apply de-Googling changes", self)
        dialog.setModal(True)

        thread = QThread(self)
        worker = OperationWorker(serial, packages, mode=mode, revert=revert)
        worker.moveToThread(thread)

        thread.started.connect(worker.run)
        worker.progress.connect(dialog.append)
        worker.finished.connect(dialog.complete)
        worker.finished.connect(thread.quit)
        worker.failed.connect(dialog.error)
        worker.failed.connect(thread.quit)
        thread.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)

        # Keep Python references alive for the duration of the modal dialog.
        self.worker_thread = thread
        self.worker = worker

        self.start_btn.setEnabled(False)
        self.revert_btn.setEnabled(False)

        def cleanup() -> None:
            self.start_btn.setEnabled(True)
            self.revert_btn.setEnabled(True)
            self.worker_thread = None
            self.worker = None
            # Re-scan after every completed operation so the list reflects the device.
            self.on_device_changed(self.device_combo.currentIndex())

        thread.finished.connect(cleanup)
        thread.start()
        dialog.exec()


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("ADB DeGoogler")
    window = DeGooglerWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
