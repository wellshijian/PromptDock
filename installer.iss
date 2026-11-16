#ifndef MyAppVersion
  #define MyAppVersion "1.0.0"
#endif

[Setup]
AppId={{8F9E7A2B-4C1D-4E5F-9A8B-202611160001}
AppName=PromptDock
AppVersion={#MyAppVersion}
AppPublisher=WELLSHIJIAN
AppPublisherURL=https://github.com/wellshijian/PromptDock
AppSupportURL=https://github.com/wellshijian/PromptDock/releases
AppUpdatesURL=https://github.com/wellshijian/PromptDock/releases
DefaultDirName={localappdata}\Programs\PromptDock
DefaultGroupName=PromptDock
PrivilegesRequired=lowest
AllowNoIcons=yes
OutputDir=.
OutputBaseFilename=PromptDock_Setup
SetupIconFile=icon.ico
UninstallDisplayIcon={app}\PromptDock.exe
Compression=lzma2/normal
SolidCompression=yes
WizardStyle=modern
CloseApplications=yes
RestartApplications=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut (创建桌面快捷方式)"; GroupDescription: "Additional tasks:"; Flags: checkedonce

[Files]
Source: "dist\PromptDock.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist

[Icons]
Name: "{group}\PromptDock"; Filename: "{app}\PromptDock.exe"
Name: "{group}\Uninstall PromptDock"; Filename: "{uninstallexe}"
Name: "{autodesktop}\PromptDock"; Filename: "{app}\PromptDock.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\PromptDock.exe"; Description: "Launch PromptDock (立即运行 PromptDock)"; Flags: nowait postinstall skipifsilent
