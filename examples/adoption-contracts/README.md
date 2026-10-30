# 多领域合成采用合同

本目录用六份合成记录展示文档、条款与检查合同的连接方式。所有记录均设置 `example_only=true`、`operation_authorized=false`、`decision.status=not-decided`，批准者、生效日期和运行结果均为空。

六种场景分别是：无账号离线 CLI 转换器；Web、后端与数据库；桌面和移动原生宿主；AI 工具应用；边缘命令；合成交易账。每例只选择接口演示所需的条款。正式使用时，应根据实际功能和承诺重新分析适用条款、必要依赖及未确定项。

## 字段与核验

- 每份规范锁定ID、版本、路径和SHA-256；局部条款以文档ID限定。
- 适用/不适用/未确定分别给理由；适用项有输入、命令或真实工具、预期终态和证据层级。
- `actual=null`、`status=not-run`、空证据准确表示本示例没有执行真实项目检查。
- 必要消费依赖连接精确两端条款及接口；技术参考不创建批准环。
- 实施身份、环境和选择范围均标合成设计，不从其他项目借用真实材料。

运行 `python checks/project_adoption.py` 检查这些记录；[schema](../../registry/schemas/project-adoption.schema.json)描述合成未决定记录使用的有限 JSON 结构。`validate_record`检查状态及依赖规则；授权、法律义务和业务结果由采用项目记录。[L6正文](../../standards/L6/001-项目采用与实现验收接口规范--v0.1.0.md)给出完整采用接口。
