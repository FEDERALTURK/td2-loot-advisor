#define AppName "TD2 Rapor Paneli"
#define AppVersion "1.5.0"
#define AppExe "TD2RaporPaneli.exe"

[Setup]
AppId={{C3CF0A3A-AB8B-44BE-8C3B-4D6BCB0E47C4}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
AppPublisher=FEDERALTURK
AppPublisherURL=https://github.com/FEDERALTURK/td2-loot-advisor
DefaultDirName={localappdata}\Programs\{#AppName}
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=..\installer
OutputBaseFilename=TD2RaporPaneli_Setup_{#AppVersion}
SetupIconFile=..\icon\td2.ico
UninstallDisplayIcon={app}\{#AppExe}
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
CloseApplications=force

[Languages]
Name: "turkish"; MessagesFile: "compiler:Languages\Turkish.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
Source: "..\project_review\github\td2-loot-advisor-reports-main\dist\panel\{#AppExe}"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExe}"

[Run]
Filename: "{app}\{#AppExe}"; Description: "{cm:LaunchProgram,{#AppName}}"; Flags: nowait postinstall skipifsilent
