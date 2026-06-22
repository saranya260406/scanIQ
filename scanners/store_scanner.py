import subprocess
import json
import logging
import os
import re

logger = logging.getLogger(__name__)

class StoreScanner:

    SKIP_PUBLISHERS = [
        'CN=Microsoft Corporation',
        'CN=Microsoft Windows',
        'CN=Microsoft',
    ]

    SKIP_NAME_PREFIXES = [
        'Microsoft.Windows.',
        'Microsoft.AccountsControl',
        'Microsoft.AsyncTextService',
        'Microsoft.BioEnrollment',
        'Microsoft.CredDialogHost',
        'Microsoft.AAD.',
        'Microsoft.XboxGame',
        'MicrosoftWindows.',
        'Windows.CBS',
        'windows.immersive',
        'Windows.Print',
        'Microsoft.549981C3F5F10',
        'DolbyLaboratories.',
        'Clipchamp.',
    ]

    # GUID/hash-prefix pattern — OEM internal packages
    OEM_GUID_PATTERN = re.compile(r'^[A-F0-9]{8}\.')

    # Common OEM/manufacturer publisher keywords — laptop brand whoever ஆனாலும் match aagum
    OEM_PUBLISHER_KEYWORDS = [
        'dell', 'hewlett-packard', 'hp inc', 'lenovo', 'asustek',
        'acer', 'msi', 'realtek', 'synaptics', 'dolby laboratories',
        'intel corporation', 'advanced micro devices', 'nvidia corporation',
        'lg electronics', 'samsung electronics', 'toshiba', 'fujitsu',
        'wacom', 'elan microelectronics',
    ]

    # Common pre-installed bundled software (manufacturer-neutral keywords)
    # Idhu OEM utility/background apps — Lenovo Now, Lenovo Vantage Service mathiri
    # Edge, Chrome mathiri "real applications" idhula illa — avanga keep aaganum
    KNOWN_OEM_BUNDLED_APPS = [
        'clipchamp', 'dolbyaccess', 'dolbyaudio', 'dolbydigitalplus',
        'mcafee', 'norton',
        'support assistant', 'supportassistant', 'companion', 'companionapp',
        'audiocontrol', 'cameracontrol', 'webcamcontrol', 'touchpad',
        'precisiontouchpad', 'fingerprintmanager', 'biometric',
        # Lenovo specific bloatware
        'lenovo now', 'lenovonow', 'lenovo vantage', 'lenovovantage',
        'vantage service', 'vantageservice',
    ]

    def scan(self):
        apps = []
        apps.extend(self._scan_appx_packages())
        logger.info(f"Store Scanner: {len(apps)} apps found")
        return apps

    def _scan_appx_packages(self):
        apps = []
        try:
            result = subprocess.run(
                [
                    "powershell",
                    "-NoProfile",
                    "-Command",
                    "Get-AppxPackage -PackageTypeFilter Bundle | Where-Object {$_.SignatureKind -eq 'Store'} | Select-Object Name, Version, Publisher, InstallLocation, PackageFullName | ConvertTo-Json"
                ],
                capture_output=True,
                text=True,
                timeout=60
            )
            if result.returncode == 0 and result.stdout.strip():
                data = json.loads(result.stdout)
                if isinstance(data, dict):
                    data = [data]
                for item in data:
                    name = item.get('Name', '')
                    publisher = item.get('Publisher', '')

                    if self._is_inbuilt(name, publisher):
                        continue

                    install_location = item.get('InstallLocation') or ''
                    size_mb = self._get_folder_size_mb(install_location)
                    apps.append({
                        'name':             name,
                        'version':          item.get('Version', 'Unknown'),
                        'publisher':        publisher,
                        'install_location': install_location,
                        'package_name':     item.get('PackageFullName', ''),
                        'size_mb':          size_mb,
                        'install_date':     'Unknown',
                        'type':             'StoreApp',
                        'source':           'StoreApp'
                    })
            logger.info(f"Store Scanner: {len(apps)} Store apps found")
        except Exception as e:
            logger.error(f"Store scan error: {e}")
        return apps

    def _is_inbuilt(self, name: str, publisher: str) -> bool:
        name_lower = name.lower()
        publisher_lower = publisher.lower()

        # 1. Exact Microsoft publisher check
        for pub in self.SKIP_PUBLISHERS:
            if publisher.startswith(pub):
                return True

        # 2. Specific known Windows core app / OEM app names
        for prefix in self.SKIP_NAME_PREFIXES:
            if name.startswith(prefix):
                return True

        # 3. GUID/hash pattern — generic, vera laptops layum work aagum
        if self.OEM_GUID_PATTERN.match(name):
            return True

        # 4. OEM manufacturer publisher keyword check — brand whoever match aagum
        for keyword in self.OEM_PUBLISHER_KEYWORDS:
            if keyword in publisher_lower:
                return True

        # 5. Known bundled software name keyword check (manufacturer-neutral)
        for keyword in self.KNOWN_OEM_BUNDLED_APPS:
            if keyword in name_lower:
                return True

        return False

    def _get_folder_size_mb(self, path: str) -> float:
        if not path or not os.path.exists(path):
            return 0.0
        try:
            total = 0
            for dirpath, _, filenames in os.walk(path):
                for f in filenames:
                    try:
                        total += os.path.getsize(os.path.join(dirpath, f))
                    except Exception:
                        continue
            return round(total / (1024 * 1024), 2)
        except Exception:
            return 0.0