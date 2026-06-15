import os
import subprocess
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class MetadataExtractor:

    def extract(self, app_list):
        enriched = []
        for app in app_list:
            try:
                location = app.get('install_location', '')
                if location and location != 'Unknown':
                    metadata = self._extract_file_metadata(location)
                    app.update(metadata)
                enriched.append(app)
            except Exception as e:
                logger.error(f"Metadata extract error {app.get('name')}: {e}")
                enriched.append(app)
        logger.info(f"Metadata Extractor: {len(enriched)} apps enriched")
        return enriched

    def _extract_file_metadata(self, location):
        metadata = {}
        try:
            exe_path = self._find_exe(location)
            if exe_path and os.path.exists(exe_path):
                # PowerShell use பண்ணி version info எடுக்கும்
                result = subprocess.run(
                    [
                        "powershell",
                        "-Command",
                        f"(Get-Item '{exe_path}').VersionInfo | Select-Object FileVersion, CompanyName, ProductName | ConvertTo-Json"
                    ],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode == 0 and result.stdout:
                    import json
                    info = json.loads(result.stdout)
                    metadata['file_version'] = info.get('FileVersion') or 'Unknown'
                    metadata['company'] = info.get('CompanyName') or 'Unknown'
                    metadata['product_name'] = info.get('ProductName') or 'Unknown'

                # File dates எடுக்கும்
                created = os.path.getctime(exe_path)
                modified = os.path.getmtime(exe_path)
                metadata['file_created'] = datetime.fromtimestamp(created).strftime('%d-%m-%Y')
                metadata['file_modified'] = datetime.fromtimestamp(modified).strftime('%d-%m-%Y')
                metadata['exe_path'] = exe_path
        except Exception as e:
            logger.debug(f"File metadata error: {e}")
        return metadata

    def _find_exe(self, location):
        if not location or not os.path.exists(location):
            return None
        try:
            for item in os.listdir(location):
                if item.lower().endswith('.exe'):
                    return os.path.join(location, item)
        except Exception:
            pass
        return None