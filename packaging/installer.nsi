Unicode True
ManifestDPIAware True

!include "MUI2.nsh"

!ifndef PORTABLE_DIR
  !error "PORTABLE_DIR must point to the generated portable distribution."
!endif
!ifndef OUTPUT_DIR
  !error "OUTPUT_DIR must point to the installer output directory."
!endif

!define APP_NAME "NEO Rating"
!define APP_VERSION "0.1.0"
!define APP_PUBLISHER "NEO Rating"
!define APP_EXE "NEORating.exe"
!define APP_REG_KEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\NEORating"

Name "${APP_NAME}"
OutFile "${OUTPUT_DIR}\NEORating-${APP_VERSION}-Setup.exe"
InstallDir "$LOCALAPPDATA\Programs\NEORating"
InstallDirRegKey HKCU "Software\NEORating" "InstallLocation"
RequestExecutionLevel user
SetCompressor /SOLID lzma
SetCompressorDictSize 64
CRCCheck force
ShowInstDetails show
ShowUninstDetails show

VIProductVersion "0.1.0.0"
VIAddVersionKey /LANG=1033 "ProductName" "${APP_NAME}"
VIAddVersionKey /LANG=1033 "ProductVersion" "${APP_VERSION}"
VIAddVersionKey /LANG=1033 "CompanyName" "${APP_PUBLISHER}"
VIAddVersionKey /LANG=1033 "LegalCopyright" "Copyright (C) 2026 NEO Rating"
VIAddVersionKey /LANG=1033 "FileDescription" "${APP_NAME} Setup"
VIAddVersionKey /LANG=1033 "FileVersion" "${APP_VERSION}"

!define MUI_ABORTWARNING
!define MUI_FINISHPAGE_RUN "$INSTDIR\${APP_EXE}"
!define MUI_FINISHPAGE_RUN_TEXT "Run NEO Rating"

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_UNPAGE_FINISH

!insertmacro MUI_LANGUAGE "English"

Section "NEO Rating" SEC_MAIN
  SectionIn RO
  SetOutPath "$INSTDIR"
  File /r "${PORTABLE_DIR}\*.*"

  WriteUninstaller "$INSTDIR\Uninstall.exe"
  WriteRegStr HKCU "Software\NEORating" "InstallLocation" "$INSTDIR"
  WriteRegStr HKCU "${APP_REG_KEY}" "DisplayName" "${APP_NAME}"
  WriteRegStr HKCU "${APP_REG_KEY}" "DisplayVersion" "${APP_VERSION}"
  WriteRegStr HKCU "${APP_REG_KEY}" "Publisher" "${APP_PUBLISHER}"
  WriteRegStr HKCU "${APP_REG_KEY}" "InstallLocation" "$INSTDIR"
  WriteRegStr HKCU "${APP_REG_KEY}" "DisplayIcon" "$INSTDIR\${APP_EXE}"
  WriteRegStr HKCU "${APP_REG_KEY}" "UninstallString" '"$INSTDIR\Uninstall.exe"'
  WriteRegStr HKCU "${APP_REG_KEY}" "QuietUninstallString" '"$INSTDIR\Uninstall.exe" /S'
  WriteRegDWORD HKCU "${APP_REG_KEY}" "NoModify" 1
  WriteRegDWORD HKCU "${APP_REG_KEY}" "NoRepair" 1

  CreateDirectory "$SMPROGRAMS\NEO Rating"
  CreateShortcut "$SMPROGRAMS\NEO Rating\NEO Rating.lnk" "$INSTDIR\${APP_EXE}"
  CreateShortcut "$SMPROGRAMS\NEO Rating\Uninstall NEO Rating.lnk" "$INSTDIR\Uninstall.exe"
SectionEnd

Section "Desktop shortcut" SEC_DESKTOP
  CreateShortcut "$DESKTOP\NEO Rating.lnk" "$INSTDIR\${APP_EXE}"
SectionEnd

Section "Uninstall"
  Delete "$DESKTOP\NEO Rating.lnk"
  Delete "$SMPROGRAMS\NEO Rating\NEO Rating.lnk"
  Delete "$SMPROGRAMS\NEO Rating\Uninstall NEO Rating.lnk"
  RMDir "$SMPROGRAMS\NEO Rating"

  DeleteRegKey HKCU "${APP_REG_KEY}"
  DeleteRegKey HKCU "Software\NEORating"

  RMDir /r "$INSTDIR"
SectionEnd
