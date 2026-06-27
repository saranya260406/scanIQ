import sys
import json

# Check settings.json directly
with open('settings.json') as f:
    data = json.load(f)
    print('=' * 60)
    print('settings.json CONTENTS:')
    print('=' * 60)
    print(json.dumps(data, indent=2))

print('\n' + '=' * 60)
print('SettingsLoader RESULT:')
print('=' * 60)

# Now test SettingsLoader
from config.settings_loader import SettingsLoader
sl = SettingsLoader()
print(f'Mode:       {sl.get_mode()}')
print(f'ScanTime:   {sl.get_scan_time()}')
print(f'ExportPath: {sl.get_export_path()}')
print(f'\nFull config:')
print(json.dumps(sl.config, indent=2, default=str))
