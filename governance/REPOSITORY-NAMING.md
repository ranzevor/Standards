# 仓库命名政策

本项目仓库标识为 **Standards**。原创仓库采用 **PascalCase**，正式品牌拼写保留，MCP/API/SDK/CLI 等通用缩写统一大写。仓库命名、迁移实施和平台权限调整分别管理。

## 选定规则与grammar

默认正例：`Standards`、`ImageWorkbench`、`AtlasSDK`、`MCPServer`。品牌项目沿用经确认的正式拼写，不把技术标识调整称为品牌重命名。

```text
OriginalActive = PascalCase - ReservedVersionDateStateOrInternalID
PascalCase = [A-Z][A-Za-z0-9]*
Acronyms = MCP | API | SDK | CLI
Archive = HistoricalBase "-archive-" YYYY "-" MM "-" DD
```

本项目使用 `Standards`。正式品牌拼写按独立确认的品牌来源记录保留；自动检查须传入准确品牌标识与依据，不能只自报brand规避禁用项。具有真实依据的品牌不因包含New/Final等词而被改名。品牌例外以虚构品牌`RiverSketch`为例；经确认的`iPhone`同样保留正式拼写；仓库标识与品牌展示、包名、域名和安装命令分开。

| 命名风格 | 特点 | 适用规则 |
| --- | --- | --- |
| kebab-case | URL 词界清楚，单词使用小写 | 用于明确采用该风格的技术标识 |
| camelCase | 首词小写，后续单词首字母大写 | 正式品牌按其确认拼写保留 |
| PascalCase | 与项目/品牌展示接近，需一致处理缩写 | 已选定原创仓默认 |

活跃名不得混版本（`V2`）、日期（`20261023`）、内部编号（`A101`）、临时状态（`Temp/New/Final/Backup/Archive/Old/Copy`）。程序检查已知模式，不代表商标、平台可用性或人为语义全部已验。`AtlasSDK`合法，`AtlasSdk`不符合通用缩写规则。

底层比较函数可显式指定风格用于对照测试；正式选定规则入口`validate_selected_name`固定PascalCase，不能选择另一style规避规则。

## 有意义的后缀

`AtlasSDK`、`AtlasCLI`、`AtlasMCP`、`AtlasLib`仅在确有独立消费边界时使用，登记role与原因；产品本身不因“使用SDK/CLI”就增加后缀。monorepo默认仍用产品/用途名，只有需要与生态中其他仓区分工作区时才使用`Monorepo`。`-repo/-project/-test/-dev`等不得充当无意义装饰；真实用途必须说明并通过人工复核，自动检查不判定理由质量。

## 平台与来源例外

| 类型 | 精确规则 | 范围 |
| --- | --- | --- |
| 组织元数据 | `.github`、`.github-private` | 平台特殊入口，不是通用slug放宽 |
| 账号主页 | 与实际账号名相同 | 不借主页例外命名任意仓 |
| 用户/组织Pages | `<account>.github.io` | 项目Pages不要求这个仓名 |
| 保留上游身份的fork | 与登记上游名称精确一致 | 记录来源/理由，不自动扩成独立品牌 |
| 既有归档保留 | 与登记的历史名精确一致且附来源依据 | 不追溯套用PascalCase，不实际改名 |
| 新拟归档名 | `<base>-archive-YYYY-MM-DD` | 日期有效，状态确为归档；不要求为了归档一定改名 |

来源：[组织简介](https://docs.github.com/en/organizations/collaborating-with-groups-in-organizations/customizing-your-organizations-profile)、[账号简介](https://docs.github.com/en/account-and-profile/how-tos/profile-customization/managing-your-profile-readme)、[Pages类型](https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages)。2026-10-23核对平台规定的特殊名；例外不会赋予公开或部署权限。

## 正反例与可执行检查

选定规则中`Standards`、`ImageWorkbench`为正例；`standards`、`image_workbench`、`AppV2`、`AppNew`、`AppA101`为反例。带有明确角色与用途的`AtlasSDK`为条件正例，空理由或错误角色为反例。检查见[repository_naming.py](../checks/repository_naming.py)与[测试](../tests/test_repository_naming.py)；程序只判断grammar、已知保留模式与例外参数，不能证明名称无商标冲突或已获平台分配。

## 冲突与迁移验收

1. 核对目标命名空间与既有仓、包、品牌及上游关系；名称冲突不通过加`new/final/2`掩盖。选择清楚业务区分词，或保留现名并说明技术原因。
2. 列出旧新坐标：仓链接、文档、徽章、包名/导入路径、Actions `uses`、CI触发条件、Webhook、OIDC信任条件、部署源、Pages路径、子模块及外部消费者。仓名变更不自动授权包坐标或品牌变更。
3. [GitHub改名说明](https://docs.github.com/en/repositories/creating-and-managing-repositories/renaming-a-repository)说明普通仓流量可重定向，但Pages项目路径和被引用Action不能依赖同等重定向；复用旧名会影响旧重定向。逐项记录实际验证，不以页面能打开替代集成验收。
4. 操作前固定授权范围、准确对象、备份与回退方案；操作后在获准环境验证链接、包解析、CI、部署引用和旧消费者，并保留失败。迁移是否实施及保护设置是否生效，以目标平台的实际操作记录和验证结果为准。
