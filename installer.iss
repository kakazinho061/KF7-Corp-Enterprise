#define MyAppName "KF7 Corp Enterprise"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "KF7 Corp"
#define MyAppExeName "KF7 Corp Enterprise.exe"

[Setup]
AppId={{KF7-CORP-ENTERPRISE-2026}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}

DefaultDirName={localappdata}\Programs\KF7 Corp Enterprise
DefaultGroupName=KF7 Corp Enterprise

OutputDir=installer
OutputBaseFilename=KF7-Corp-Enterprise-Setup

Compression=lzma
SolidCompression=yes
WizardStyle=modern

PrivilegesRequired=lowest
Uninstallable=yes

[Files]
Source: "dist\KF7 Corp Enterprise.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autodesktop}\KF7 Corp Enterprise"; Filename: "{app}\KF7 Corp Enterprise.exe"; IconFilename: "{app}\KF7 Corp Enterprise.exe"
Name: "{autoprograms}\KF7 Corp Enterprise"; Filename: "{app}\KF7 Corp Enterprise.exe"; IconFilename: "{app}\KF7 Corp Enterprise.exe"

[Run]
Filename: "{app}\KF7 Corp Enterprise.exe"; \
    Description: "Abrir KF7 Corp Enterprise"; \
    Flags: nowait postinstall skipifsilent
