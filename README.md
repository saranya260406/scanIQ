# scanIQ

scanIQ is a Windows application for discovering and analyzing installed applications, services, startup entries, browser-related artifacts, and other system traces.

## Features
- Scan installed applications and system traces
- Detect startup items, services, and browser-related artifacts
- Export findings to CSV
- Run as a desktop application or background service

## Requirements
- Python 3.10 or newer
- Windows operating system
- Internet access for optional AI-based classification features

## Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/saranya260406/scanIQ.git
   cd scanIQ
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the application:
   ```bash
   python main.py
   ```

## Optional: Run as a service
If you want to run scanIQ as a background service, use:
```bash
python service.py
```

## Release assets
The source code is available in this repository. Large packaged installers and archives are not stored in the repository to keep GitHub releases lightweight.

If you want the packaged installer, download it from the GitHub Releases page for this project.

## Notes
- Some features may require API keys or local model configuration.
- The project uses configuration files such as config.json and settings.json.
- For best results on Windows, run it with administrator privileges when scanning system-level information.
