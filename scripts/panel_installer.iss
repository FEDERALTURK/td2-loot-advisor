#ifndef AppVersion
  #define AppVersion "1.0.0"
#endif
#define AppName "TD2 Loot Advisor Panel"
#define AppExe "TD2LootAdvisorPanel.exe"

[Setup]
AppId={{A2A6D190-C68E-4C83-B4D9-0ECAB3F7F8BE}
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
OutputBaseFilename=TD2LootAdvisorPanel_Setup_{#AppVersion}
SetupIconFile=..\icon\td2.ico
UninstallDisplayIcon={app}\{#AppExe}
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible
CloseApplications=force

[Languages]
Name: "turkish"; MessagesFile: "compiler:Languages\Turkish.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
Source: "..\dist\TD2LootAdvisorPanel\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExe}"

[Run]
Filename: "{app}\{#AppExe}"; Description: "{cm:LaunchProgram,{#AppName}}"; Flags: nowait postinstall skipifsilent
