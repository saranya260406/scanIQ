import subprocess
import logging

logger = logging.getLogger(__name__)

class ProcessScanner:

    def scan(self):
        processes = []
        try:
            result = subprocess.run(
                [
                    "powershell",
                    "-Command",
                    "Get-Process | Select-Object Name, Id, CPU, WorkingSet, Path | ConvertTo-Json"
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
                    size_mb = round(item.get('WorkingSet', 0) / (1024 * 1024), 2)
                    processes.append({
                        'name': item.get('Name', 'Unknown'),
                        'pid': item.get('Id', 'Unknown'),
                        'cpu': item.get('CPU', 0),
                        'memory_mb': size_mb,
                        'path': item.get('Path') or 'Unknown',
                        'type': 'Process'
                    })
            logger.info(f"Process Scanner: {len(processes)} processes found")
        except Exception as e:
            logger.error(f"Process scan error: {e}")
        return processes