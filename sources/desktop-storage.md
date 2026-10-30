# 本地文档与存储技术来源

以下为固定来源映射，具体实现及滚动文档仍需按当前版本验证；引用日期与具体实现版本分别记录。

| ID | 来源 | 技术范围 | 适用与限制 |
| --- | --- | --- | --- |
| O01 | [Microsoft Known Folders](https://learn.microsoft.com/en-us/windows/win32/shell/known-folders) | 动态 Win32 文档；所见更新日期 2026-07-17；Known Folders 可重定向，包括网络位置 | S01/S11；只用于 Windows 目录假设，未把某个具体调用初始化要求写成全领域义务 |
| O02 | [XDG Base Directory 0.8](https://specifications.freedesktop.org/basedir/0.8/) | 固定 0.8，2021-05-08；数据/配置/状态/缓存/运行目录分离，环境路径须为绝对 | S01；仅采用 XDG 的实现激活，不强制全部 Linux 桌面实现相同 |
| O03 | [GetFileInformationByHandleEx](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-getfileinformationbyhandleex) | 动态 Win32 实现文档；句柄查询及信息类受 OS/驱动差异影响 | S03；只支持“核对句柄对应对象与实际能力”，不声称任一文件 ID 永久稳定或构成授权 |
| O04 | [Linux man-pages fsync(2)](https://man7.org/linux/man-pages/man2/fsync.2.html) | Linux man-pages 项目一手接口说明；文件 fsync 不必然使目录项落盘，目录需另外同步 | S06；Linux 条件化，不泛化全部 POSIX/Windows/网络服务；引擎持久化仍引用既有规范 |
| O05 | [FlushFileBuffers](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-flushfilebuffers) | 动态 Win32 文档，所见更新 2021-10-13；句柄类型、访问权与返回错误有区别 | S06；不把调用返回作为所有硬件断电可靠证明，也不要求应用全卷管理员 flush |
| O06 | [ReplaceFileW](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-replacefilew) | 动态 Win32 API；ERROR_UNABLE_TO_MOVE_REPLACEMENT / _2 对原/替换名有不同后果；IGNORE_ACL_ERRORS 可不保留 ACL | S07/F06；支持“失败不等于没变更”，不在 L4 提供未经目标验证的替换算法 |
| O07 | [Qt QSaveFile](https://doc.qt.io/qt-6/qsavefile.html) | qt-6 滚动文档；页面标识 Qt 6.12.0；引用日期 2026-10-23；临时写与 commit，direct-write fallback 下取消无相同保护 | S08/F07；L5 固定项目实际采用的Qt版本及文件系统条件 |
| O08 | [Apple File Coordinators and Presenters](https://developer.apple.com/library/archive/documentation/FileManagement/Conceptual/FileSystemProgrammingGuide/FileCoordinators/FileCoordinators.html) | 官方 Documentation Archive；解释协调者、呈现者和 NSDocument 的协作，不作为最新 SDK availability 的独立依据 | S10；仅支持机制分工，不承诺控制所有外部进程或全部存储提供者；现代签名/availability 留 L5 核验 |
| O09 | [SQLite WAL](https://www.sqlite.org/wal.html) | 官方动态引擎文档；WAL 为数据库持久状态的一部分，网络文件系统有机制限制 | S11/S12/F13；不重订 WAL、事务和备份算法，不建议手动删除 WAL；运行时版本另行绑定 |
