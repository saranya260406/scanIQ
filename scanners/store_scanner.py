import subprocess
import json
import logging
import os

logger = logging.getLogger(__name__)

class StoreScanner:

    # Windows inbuilt Store apps skip
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
                    "Get-AppxPackage -PackageTypeFilter Bundle | Select-Object Name, Version, Publisher, InstallLocation, PackageFullName | ConvertTo-Json"
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

                    # Inbuilt apps skip
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
        # Publisher check
        for pub in self.SKIP_PUBLISHERS:
            if publisher.startswith(pub):
                return True
        # Name prefix check
        for prefix in self.SKIP_NAME_PREFIXES:
            if name.startswith(prefix):
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