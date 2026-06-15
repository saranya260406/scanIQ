import subprocess
import logging

logger = logging.getLogger(__name__)

class StoreScanner:

    def scan(self):
        apps = []
        try:
            result = subprocess.run(
                [
                    "powershell",
                    "-Command",
                    "Get-AppxPackage | Select-Object Name, Publisher, Version, InstallLocation | ConvertTo-Json"
                ],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0 and result.stdout:
                import json
                data = json.loads(result.stdout)
                if isinstance(data, dict):
                    data = [data]
                for item in data:
                    app = {
                        'name': item.get('Name', 'Unknown'),
                        'publisher': item.get('Publisher', 'Unknown'),
                        'version': item.get('Version', 'Unknown'),
                        'install_location': item.get('InstallLocation', 'Unknown'),
                        'type': 'Store'
                    }
                    apps.append(app)
            logger.info(f"Store Scanner: {len(apps)} apps found")
        except Exception as e:
            logger.error(f"Store scan error: {e}")
        return apps