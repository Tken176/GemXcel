[Setup]
AppName=GemXcel
AppVersion=1.0
AppPublisher=GemXcel Team
AppPublisherURL=https://gemxcel.pages.dev/

DefaultDirName={autopf}\GemXcel
DefaultGroupName=GemXcel

OutputDir=.
OutputBaseFilename=GemXcel_Setup

Compression=lzma
SolidCompression=yes
WizardStyle=modern

DisableDirPage=no
DisableProgramGroupPage=no
AllowNoIcons=yes

[UninstallDelete]
Type: filesandordirs; Name: "{userappdata}\GemxelProject"

[Files]
; 👉 QUAN TRỌNG NHẤT
Source: "dist\GemXcel.exe"; DestDir: "{app}"; Flags: ignoreversion


[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Additional icons:"; Flags: unchecked


[Icons]
Name: "{group}\GemXcel"; Filename: "{app}\GemXcel.exe"
Name: "{autodesktop}\GemXcel"; Filename: "{app}\GemXcel.exe"; Tasks: desktopicon


[Run]
Filename: "{app}\GemXcel.exe"; Description: "Launch GemXcel"; Flags: nowait postinstall skipifsilent