Unicode true
Name "Image Jakdu"
OutFile "..\..\dist\ImageJakdu-0.1.2-windows-installer.exe"
InstallDir "$PROGRAMFILES64\ImageJakdu"
RequestExecutionLevel admin
!define SOURCE_EXE "..\..\dist\ImageJakdu.exe"
!define VC_REDIST_SOURCE "vc_redist.x64.exe"

Page directory
Page instfiles

Section "Install"
  DetailPrint "Installing Microsoft Visual C++ Runtime..."
  InitPluginsDir
  File /oname=$PLUGINSDIR\vc_redist.x64.exe "${VC_REDIST_SOURCE}"
  ExecWait '"$PLUGINSDIR\vc_redist.x64.exe" /install /quiet /norestart'

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
