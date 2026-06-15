import subprocess
import json
import logging

logger = logging.getLogger(__name__)

class ServiceScanner:

    def scan(self):
        services = []
        try:
            result = subprocess.run(
                [
                    "powershell",
                    "-Command",
                    "Get-Service | Select-Object Name, DisplayName, Status, StartType | ConvertTo-Json"
                ],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0 and result.stdout:
                data = json.loads(result.stdout)
                if isinstance(data, dict):
                    data = [data]
                for item in data:
                    services.append({
                        'name': item.get('Name', 'Unknown'),
                        'display_name': item.get('DisplayName', 'Unknown'),
                        'status': item.get('Status', 'Unknown'),
                        'start_type': item.get('StartType', 'Unknown'),
                        'type': 'Service'
                    })
            logger.info(f"Service Scanner: {len(services)} services found")
        except Exception as e:
            logger.error(f"Service scan error: {e}")
        return services