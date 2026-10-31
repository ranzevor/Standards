# 仓库门禁与安装边界示例

这些合成案例面向检查器和安装流程设计，使用 Python 3.12 标准库及本仓路径校验函数。入口为仓库根：

```sh
python -X utf8 -B -m unittest tests.test_repository_engineering -v
```

实现见 [contracts.py](contracts.py)，测试见[场景源码](../../tests/test_repository_engineering.py)。预期结果由场景中的独立合同决定；命令实际结果以本次执行输出为准。

| 机制 | 直接反例 | 合法邻例/恢复 |
| --- | --- | --- |
| 独立包成员 | 删除空 `py.typed` 并重算自述清单；混入其他字节或额外成员 | 原包、成员重排、按当前候选版本生成的新元数据 |
| 来源字段关系 | 源码文件集合与 `source_manifest_sha256` 矛盾 | 对同一源码重算准确身份 |
| 依赖组语义 | 漏项、重复项、未支持语法或额外来源 | 三组明确互不依赖的 `-r` 条目重排和注释变化 |
| 单次读取 | 路径在首次读取后已被替换成非法配置 | 语义和返回摘要仍对应首次合法字节；下次读取拒绝非法值 |
| 字节与语义 | 将不同排版冒充同一字节身份 | 两种合法 JSON 排版语义相同、摘要不同 |
| 物理根 | Windows junction / POSIX 目录链接导向有相同字符串前缀的根外目录 | 普通根内 Unicode、空格文件名 |
| 安装演进 | 目标有未知文件；输入字节与可信身份不符 | 新装、增删/改名升级、恢复旧版、卸载均使用同一身份规则 |

Windows 运行 junction 场景，POSIX 运行符号链接场景；另一平台场景按条件跳过。Windows 创建 junction 失败会使该场景失败，不按缺少符号链接权限跳过。

`include_targets` 只演示表中独立 include 的有限语法，不能替代 pip 解析器。`inventory` 描述普通文件映射，不捕获目录、空目录、权限或完整文件系统身份。`resolve_member` 只判断受控目录在解析时的物理归属，不锁定并发写入。`switch_owned_files` 返回新的文件映射，不执行磁盘安装、锁、备份事务或数据迁移。

真实包和安装器接入方法见[门禁设计](../../guides/QUALITY-GATE-DESIGN.md)及[安装恢复](../../guides/ARTIFACT-INSTALLATION-LIFECYCLE.md)。项目原始执行输出保存在独立运行目录或 CI 制品中。
