Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
WshShell.CurrentDirectory = fso.GetParentFolderName(WScript.ScriptFullName)

' Try pythonw.exe first (no console window, but GUI shows)
On Error Resume Next
WshShell.Run "pythonw run.py", 1, False
If Err.Number <> 0 Then
    Err.Clear
    ' Try pythonw3
    WshShell.Run "pythonw3 run.py", 1, False
    If Err.Number <> 0 Then
        Err.Clear
        ' Try python (will show console briefly, but GUI will appear)
        WshShell.Run "python run.py", 1, False
        If Err.Number <> 0 Then
            Err.Clear
            ' Try python3
            WshShell.Run "python3 run.py", 1, False
        End If
    End If
End If
On Error Goto 0

Set WshShell = Nothing
Set fso = Nothing

