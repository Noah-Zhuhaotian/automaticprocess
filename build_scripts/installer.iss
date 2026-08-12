; Inno Setup script - wraps the PyInstaller onedir build (dist/AutomaticProcess/)
; into a single Setup.exe installer: Start Menu shortcut, optional desktop
; shortcut, proper "Apps & features" uninstall entry.
;
; Build order (from the repo root):
;   1. pyinstaller build_scripts/automaticprocess.spec   (produces dist/AutomaticProcess/)
;   2. "%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe" build_scripts/installer.iss
; Output: build_scripts/output/AutomaticProcess-Setup.exe
;
; AppId is a fixed GUID (not the app name) so re-running the installer for a
; future version upgrades in place instead of creating a second entry -
; never change it once real installs exist.

#define MyAppName "Automatic Process Assistant"
#define MyAppVersion "1.0.0"
#define MyAppExeName "AutomaticProcess.exe"
#define MyDistDir "..\dist\AutomaticProcess"

[Setup]
AppId={{9BD5349E-A6C3-4593-BA5B-CE126D48BA77}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
DefaultDirName={autopf}\AutomaticProcess
DefaultGroupName=Automatic Process Assistant
DisableProgramGroupPage=yes
OutputDir=output
OutputBaseFilename=AutomaticProcess-Setup
SetupIconFile=..\resources\app_icon.ico
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\{#MyAppExeName}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Additional shortcuts:"

[Files]
Source: "{#MyDistDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall skipifsilent
