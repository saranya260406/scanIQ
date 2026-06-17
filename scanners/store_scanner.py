import subprocess
import json
import logging
import os

logger = logging.getLogger(__name__)

class StoreScanner:

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
                    "Get-AppxPackage | Select-Object Name, Version, Publisher, InstallLocation, PackageFullName | ConvertTo-Json"
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
                    install_location = item.get('InstallLocation') or ''
                    size_mb = self._get_folder_size_mb(install_location)
                    apps.append({
                        'name':             item.get('Name', 'Unknown'),
                        'version':          item.get('Version', 'Unknown'),
                        'publisher':        item.get('Publisher', 'Unknown'),
                        'install_location': install_location,
                        'package_name':     item.get('PackageFullName', ''),
                        'size_mb':          size_mb,
                        'install_date':     'Unknown',
                        'type':             'StoreApp'
                    })
            logger.info(f"Store Scanner: {len(apps)} Store apps found")
        except Exception as e:
            logger.error(f"Store scan error: {e}")
        return apps

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