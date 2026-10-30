#define MyAppName "PresentazioniMessa"
#define MyAppVersion "2.0"
#define MyAppPublisher "Coro Giovani"
#define MyAppExeName "PresentazioniMessa.exe"
#define MyAppDistDir "dist\PresentazioniMessa"

[Setup]
AppId={{D63B8387-BC6E-4A05-A510-3E873D459EE7}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={localappdata}\Programs\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=installer
OutputBaseFilename=PresentazioniMessa-Setup-{#MyAppVersion}
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayName={#MyAppName}
UninstallDisplayIcon={app}\PresentazioniMessa.ico
SetupIconFile=PresentazioniMessa.ico
SetupLogging=yes
CloseApplications=yes
RestartApplications=no

[Languages]
Name: "italian"; MessagesFile: "compiler:Languages\Italian.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Crea un collegamento sul desktop"; GroupDescription: "Collegamenti aggiuntivi:"; Flags: unchecked

[Files]
; PyInstaller binaries and dependencies. Runtime resources copied by
; build_distribution.bat are excluded here and listed explicitly below.
Source: "{#MyAppDistDir}\*"; DestDir: "{app}"; Excludes: "custom.css,librone.json,start.png,version.txt,PresentazioniMessa.ico,sunday_image.jpg,fonts\*"; Flags: ignoreversion recursesubdirs createallsubdirs

; Files loaded by the application using paths relative to its working directory.
Source: "{#MyAppDistDir}\custom.css"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#MyAppDistDir}\librone.json"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#MyAppDistDir}\start.png"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#MyAppDistDir}\version.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#MyAppDistDir}\PresentazioniMessa.ico"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#MyAppDistDir}\fonts\*"; DestDir: "{app}\fonts"; Flags: ignoreversion recursesubdirs createallsubdirs

; Optional initial cover image. The program can download and replace it later.
Source: "{#MyAppDistDir}\sunday_image.jpg"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; IconFilename: "{app}\PresentazioniMessa.ico"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; IconFilename: "{app}\PresentazioniMessa.ico"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Avvia {#MyAppName}"; WorkingDir: "{app}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Remove transient downloaded files, but leave librone.json available to the
; standard uninstall process so Inno Setup can remove the installed copy.
Type: files; Name: "{app}\librone.tmp.json"
Type: files; Name: "{app}\version.tmp.txt"
Type: files; Name: "{app}\installer.exe"
