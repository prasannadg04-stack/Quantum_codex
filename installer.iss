; Inno Setup script - turns dist\HeadCursor into a normal "Setup" installer for NGO computers.
; Free tool: https://jrsoftware.org/isinfo.php  (open this file, press Compile)

[Setup]
AppName=HeadCursor
AppVersion=1.0
AppPublisher=Quantum Codex
DefaultDirName={autopf}\HeadCursor
DefaultGroupName=HeadCursor
OutputBaseFilename=HeadCursor-Setup
Compression=lzma
SolidCompression=yes

[Files]
Source: "dist\HeadCursor\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs

[Icons]
Name: "{group}\HeadCursor"; Filename: "{app}\HeadCursor.exe"
Name: "{autodesktop}\HeadCursor"; Filename: "{app}\HeadCursor.exe"

[Run]
Filename: "{app}\HeadCursor.exe"; Description: "Start HeadCursor now"; Flags: nowait postinstall skipifsilent
