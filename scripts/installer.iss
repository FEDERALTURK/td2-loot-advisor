; TD2 Loot Advisor — Windows kurulum dosyası (Inno Setup 6)
; build_installer.bat tarafından çağrılır:  ISCC /DAppVersion=5.0 scripts\installer.iss
; Yönetici izni istemez: kullanıcının kendi klasörüne kurulur (ayarlar ve sandık kaydedilebilsin diye).

#ifndef AppVersion
  #define AppVersion "5.0"
#endif
#define AppName "TD2 Loot Advisor"
#define AppExe "TD2LootAdvisor.exe"

[Setup]
AppId={{51FBF829-F27E-49A0-B33A-667634AB2A8C}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
AppPublisher=FEDERALTURK
AppPublisherURL=https://github.com/FEDERALTURK/td2-loot-advisor
AppSupportURL=https://github.com/FEDERALTURK/td2-loot-advisor/issues
DefaultDirName={localappdata}\Programs\{#AppName}
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=..\installer
OutputBaseFilename=TD2LootAdvisor_Setup_{#AppVersion}
SetupIconFile=..\build\td2.ico
UninstallDisplayIcon={app}\{#AppExe}
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible
CloseApplications=yes

[Languages]
Name: "turkish"; MessagesFile: "compiler:Languages\Turkish.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "german"; MessagesFile: "compiler:Languages\German.isl"
Name: "french"; MessagesFile: "compiler:Languages\French.isl"
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"
Name: "italian"; MessagesFile: "compiler:Languages\Italian.isl"
Name: "portuguese"; MessagesFile: "compiler:Languages\Portuguese.isl"
Name: "polish"; MessagesFile: "compiler:Languages\Polish.isl"
Name: "dutch"; MessagesFile: "compiler:Languages\Dutch.isl"
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
; Program (PyInstaller klasörü). Kullanıcı verisi (builds.json, stash.json, logs…) kurulumda yoktur;
; ilk açılışta oluşur ve güncellemede korunur.
Source: "..\dist\TD2LootAdvisor\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExe}"
Name: "{group}\{cm:UninstallProgram,{#AppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExe}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExe}"; Description: "{cm:LaunchProgram,{#AppName}}"; Flags: nowait postinstall skipifsilent
; Uygulama içi güncelleme sessiz kurulum yapar (/RELAUNCH=1): bitince program kendiliğinden yeniden açılır
Filename: "{app}\{#AppExe}"; Flags: nowait; Check: ShouldRelaunch

[Code]
function ShouldRelaunch: Boolean;
begin
  Result := WizardSilent and (ExpandConstant('{param:RELAUNCH|0}') = '1');
end;
