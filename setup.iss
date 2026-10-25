; Inno Setup script for Driving School Manager
#define MyAppName "Gestion Auto Ecole"
#define MyAppVersion "1.0"
#define MyAppPublisher "Mohsinnet"
#define MyAppExeName "DrivingSchoolManager.exe"

[Setup]
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\Gestion auto Ecole
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
OutputDir=E:\موقعي\app exe\installer
OutputBaseFilename=DrivingSchoolManager_Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
SetupIconFile=E:\موقعي\app exe\icon.ico
UninstallDisplayIcon={app}\{#MyAppExeName}

[Languages]
Name: "french"; MessagesFile: "compiler:Languages\French.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "E:\موقعي\app exe\DrivingSchoolManager.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "E:\موقعي\app exe\icon.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\icon.ico"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\icon.ico"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
