Unicode true
Name "Image Jakdu"
OutFile "..\..\dist\ImageJakdu-0.1.0-windows-installer.exe"
InstallDir "$LOCALAPPDATA\ImageJakdu"
RequestExecutionLevel user
!define SOURCE_EXE "..\..\dist\ImageJakdu.exe"

Page directory
Page instfiles

Section "Install"
  SetOutPath "$INSTDIR"
  File "${SOURCE_EXE}"
  CreateDirectory "$SMPROGRAMS\Image Jakdu"
  CreateShortCut "$SMPROGRAMS\Image Jakdu\Image Jakdu.lnk" "$INSTDIR\ImageJakdu.exe"
  CreateShortCut "$DESKTOP\Image Jakdu.lnk" "$INSTDIR\ImageJakdu.exe"
  WriteUninstaller "$INSTDIR\Uninstall.exe"
SectionEnd

Section "Uninstall"
  Delete "$DESKTOP\Image Jakdu.lnk"
  Delete "$SMPROGRAMS\Image Jakdu\Image Jakdu.lnk"
  RMDir "$SMPROGRAMS\Image Jakdu"
  Delete "$INSTDIR\ImageJakdu.exe"
  Delete "$INSTDIR\Uninstall.exe"
  RMDir "$INSTDIR"
SectionEnd
