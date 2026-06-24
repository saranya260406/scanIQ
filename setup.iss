[Setup]
AppName=scanIQ
AppVersion=1.0
AppPublisher=Saranya
DefaultDirName={autopf}\scanIQ
DefaultGroupName=scanIQ
OutputDir=installer
OutputBaseFilename=scanIQ_Setup
Compression=lzma
SolidCompression=yes
PrivilegesRequired=admin

[Files]
Source: "dist\scanIQ.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: ".env"; DestDir: "{app}"; Flags: ignoreversion
Source: "settings.json"; DestDir: "{app}"; Flags: ignoreversion

[Run]
Filename: "{app}\scanIQ.exe"; Parameters: "install"; Flags: runhidden waituntilterminated
Filename: "{app}\scanIQ.exe"; Parameters: "start"; Flags: runhidden waituntilterminated

[UninstallRun]
Filename: "{app}\scanIQ.exe"; Parameters: "stop"; Flags: runhidden waituntilterminated
Filename: "{app}\scanIQ.exe"; Parameters: "remove"; Flags: runhidden waituntilterminated