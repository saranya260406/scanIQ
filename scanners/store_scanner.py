import subprocess
import json
import logging
import os

logger = logging.getLogger(__name__)

class StoreScanner:

    SKIP_PUBLISHERS = [
        "CN=Microsoft Corporation",
        "CN=Microsoft Windows",
        "CN=Microsoft"
    ]

    SKIP_NAME_PREFIXES = [
        "Microsoft.AccountsControl",
        "Microsoft.AsyncTextService",
        "Microsoft.BioEnrollment",
        "Microsoft.CredDialogHost",
        "Microsoft.AAD.",
        "Microsoft.XboxGame",
        "MicrosoftWindows.",
        "Windows.CBS",
        "windows.immersive",
        "Windows.Print"
    ]

    def scan(self):
        apps = self._scan_appx_packages()
        logger.info(f"Store Scanner: {len(apps)} apps found")
        return apps

    def _scan_appx_packages(self):
        apps = []

        try:
            cmd = (
                "Get-AppxPackage | "
                "Select-Object Name,Version,Publisher,"
                "InstallLocation,PackageFullName | "
                "ConvertTo-Json -Depth 3"
            )

            result = subprocess.run(
                [
                    "powershell",
                    "-NoProfile",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-Command",
                    cmd
                ],
                capture_output=True,
                text=True,
                timeout=120
            )

            if result.returncode != 0:
                logger.error(result.stderr)
                return apps

            if not result.stdout.strip():
                return apps

            data = json.loads(result.stdout)

            if isinstance(data, dict):
                data = [data]

            for item in data:

                name = item.get("Name", "")
                publisher = item.get("Publisher", "")
                install_location = item.get("InstallLocation", "")


                if self._is_inbuilt(name, publisher):
                    continue

                apps.append({
                    "name": name,
                    "version": item.get("Version", ""),
                    "publisher": publisher,
                    "install_location": install_location,
                    "package_name": item.get("PackageFullName", ""),
                    "size_mb": self._get_folder_size_mb(
                        install_location
                    ),
                    "install_date": "",
                    "type": "StoreApp",
                    "source": "StoreApp"
                })

            logger.info(
                f"Store Scanner: {len(apps)} Store apps found"
            )

        except Exception as e:
            logger.exception(
                f"Store Scanner Error: {e}"
            )

        return apps

    def _is_inbuilt(self, name, publisher):

        for pub in self.SKIP_PUBLISHERS:
            if publisher.startswith(pub):
                return True

        for prefix in self.SKIP_NAME_PREFIXES:
            if name.startswith(prefix):
                return True

        return False

    def _get_folder_size_mb(self, path):

        if not path:
            return 0.0

        if not os.path.exists(path):
            return 0.0

        total = 0

        try:
            for root, dirs, files in os.walk(path):
                for file in files:
                    try:
                        total += os.path.getsize(
                            os.path.join(root, file)
                        )
                    except:
                        pass

            return round(
                total / (1024 * 1024),
                2
            )

        except:
            return 0.0