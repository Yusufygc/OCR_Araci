; OCR Aracı kurulum betiği (Inno Setup 6). Derleme: python build_installer.py
#ifndef AppVersion
  #define AppVersion "0.0.0"
#endif
#define AppName "OCR Aracı"
#define AppExe "OCRAraci.exe"

[Setup]
; AppId SABİT: değişirse sonraki sürüm üstüne yazmaz, ikinci kurulum olur
AppId={{D303C71B-3E64-4B0C-8342-118BE7BA81E2}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
DefaultDirName={autopf}\{#AppName}
DisableProgramGroupPage=yes
; UAC sormaz: güncelleme sessiz çalışır, derleme sonrası deneme mümkün olur
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
; Güncellemede çalışan uygulama kapatılır (dosya kilidi olmasın); yeniden açmayı [Run] yapar
CloseApplications=yes
RestartApplications=no
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir=..\dist\installer
OutputBaseFilename=OCRAraci-Setup-{#AppVersion}
UninstallDisplayIcon={app}\{#AppExe}
SetupIconFile=app_icon.ico
Compression=lzma2
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "turkish"; MessagesFile: "compiler:Languages\Turkish.isl"

[Files]
Source: "..\dist\OCRAraci\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#AppName}"; Filename: "{app}\{#AppExe}"

[Run]
Filename: "{app}\{#AppExe}"; Description: "{#AppName} uygulamasını başlat"; Flags: nowait postinstall skipifsilent
Filename: "{app}\{#AppExe}"; Flags: nowait; Check: RelaunchAfterUpdate

[Code]
function HasParam(const Name: String): Boolean;
var
  I: Integer;
begin
  Result := False;
  for I := 1 to ParamCount do
    if CompareText(ParamStr(I), Name) = 0 then
    begin
      Result := True;
      Exit;
    end;
end;

{ Uygulama içi güncelleme /SILENT ile çalışır: yeniden aç. Derleme sonrası deneme /VERYSILENT: açma. }
function RelaunchAfterUpdate: Boolean;
begin
  Result := WizardSilent and not HasParam('/VERYSILENT');
end;
