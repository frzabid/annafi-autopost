' Menjalankan jalan.bat tanpa memunculkan jendela hitam (dipanggil Task Scheduler)
Set sh = CreateObject("WScript.Shell")
dir = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)
sh.Run """" & dir & "\jalan.bat""", 0, False
