; Inno Setup script — bundles the Flutter Windows release build into a single
; self-contained installer (SmartShop-Setup-<ver>.exe).
;
; Build:
;   flutter build windows --release   (optionally with --dart-define=API_URL=https://your-domain)
;   "%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe" installer\fastfood_pos.iss
;
; The installer is per-user (no admin / UAC needed), installs to
; %LOCALAPPDATA%\Programs\Smart Shop, adds Start-Menu + optional desktop
; shortcuts, and registers a proper uninstaller.

#define AppName    "Storixx"
#define AppVersion "1.0.0"
#define AppPublisher "ApkaySoftware"
#define AppExe     "smart_shop.exe"
#define BuildDir   "..\build\windows\x64\runner\Release"

[Setup]
AppId={{7F3A9C21-4B8E-4E2A-9C1D-SMARTSHOP0001}}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={localappdata}\Programs\Smart Shop
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
DisableDirPage=auto
UninstallDisplayIcon={app}\{#AppExe}
UninstallDisplayName={#AppName} {#AppVersion}
OutputDir=dist
OutputBaseFilename=SmartShop-Setup-{#AppVersion}
SetupIconFile=..\windows\runner\resources\app_icon.ico
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
ArchitecturesInstallIn64BitMode=x64compatible
ArchitecturesAllowed=x64compatible

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Everything the app needs: smart_shop.exe, all *.dll, and the data\ folder.
Source: "{#BuildDir}\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExe}"
Name: "{group}\{cm:UninstallProgram,{#AppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExe}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExe}"; Description: "{cm:LaunchProgram,{#StringChange(AppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
