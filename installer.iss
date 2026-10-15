; Inno Setup 6 Script for OpenSearch by DeepLogic
; Produces OpenSearch-Setup.exe installer

#define MyAppName "OpenSearch"
#define MyAppPublisher "DeepLogic"
#define MyAppVersion "1.0.0"
#define MyAppExeName "OpenSearch.exe"
#define MyAppAssocName MyAppName + " by " + MyAppPublisher

[Setup]
AppId={{9B7E35A1-6899-4A73-A7D6-9E8640C3B702}
AppName={#MyAppName} by {#MyAppPublisher}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppPublisher}\{#MyAppName}
DefaultGroupName={#MyAppPublisher}\{#MyAppName}
AllowNoIcons=yes
OutputDir=dist\installer
OutputBaseFilename=OpenSearch-Setup
SetupIconFile=assets\icons\opensearch.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayIcon={app}\{#MyAppExeName}
UninstallDisplayName={#MyAppName} by {#MyAppPublisher}
CloseApplications=yes
RestartApplications=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "startupicon"; Description: "Start OpenSearch when Windows starts"; GroupDescription: "Windows Integration:"; Flags: unchecked

[Files]
Source: "dist\OpenSearch\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "assets\icons\opensearch.ico"; DestDir: "{app}\assets\icons"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\assets\icons\opensearch.ico"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\assets\icons\opensearch.ico"; Tasks: desktopicon
Name: "{userstartup}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: startupicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}\cache"
Type: filesandordirs; Name: "{app}\logs"
