# transbot-qq
QQ群消息匿名转发bot 作为QQ群匿名功能的替代品使用
已实现功能：
1、将私聊收到的文本、图片信息加上匿名昵称后转发群聊
2、用户手动更换自己的匿名昵称、系统每天自动重新分配匿名昵称
3、管理员禁言操作及解除禁言操作

前置说明：
robot消息接收基于go cq-http框架开发，需要程序于5701端口上监听
robot消息发送采用windows桌面端QQ 模拟win32剪贴板操作进行
bot所有日志记录于mysql数据库中

文件夹格式
./picture/1.jpg......
./assigned_nicknames.txt  （记录用户与当前匿名昵称的对应关系 自动生成）
./user_ids.txt （所有用户信息 需手动添加）
./nicknames.txt（所有可用匿名昵称信息 需手动添加）
./authorizedadmin.txt （管理员用户信息 需手动添加）
./main.py

命令一览：
