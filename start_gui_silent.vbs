' Zed Editor GUI 启动器 - 完全静默版本
' 此VBScript文件可以完全隐藏地启动GUI程序，不显示任何控制台窗口

Option Explicit

Dim objShell, objFSO, strCurrentDir, strCommand
Dim arrCommands, i, commandSuccess

' 创建Shell和FileSystem对象
Set objShell = CreateObject("WScript.Shell")
Set objFSO = CreateObject("Scripting.FileSystemObject")

' 获取脚本所在目录
strCurrentDir = objFSO.GetParentFolderName(WScript.ScriptFullName)

' 设置工作目录
objShell.CurrentDirectory = strCurrentDir

' 定义要尝试的启动命令（按优先级排序）
arrCommands = Array( _
    "pythonw.exe gui_launcher.pyw", _
    "pythonw.exe main.pyw", _
    "pythonw.exe main.py --gui", _
    "python.exe main.py --gui" _
)

' 初始化成功标志
commandSuccess = False

' 尝试每个命令，直到找到一个能工作的
For i = 0 To UBound(arrCommands)
    On Error Resume Next

    ' 使用Run方法启动程序
    ' 参数说明：
    ' - 第1个参数：要执行的命令
    ' - 第2个参数：窗口显示方式（0 = 隐藏窗口）
    ' - 第3个参数：是否等待程序结束（False = 不等待）
    objShell.Run arrCommands(i), 0, False

    ' 检查是否有错误
    If Err.Number = 0 Then
        commandSuccess = True
        Exit For
    End If

    ' 清除错误并尝试下一个命令
    Err.Clear
Next

' 清理对象
Set objShell = Nothing
Set objFSO = Nothing

' 如果所有命令都失败，可以选择显示错误消息
' 但为了保持完全静默，我们不显示任何消息
' If Not commandSuccess Then
'     MsgBox "无法启动Zed Editor更新程序。请确保Python已正确安装。", vbCritical, "启动错误"
' End If

' 脚本结束
WScript.Quit
