# Project governance standards — English translations

These are full English translations of the adopted Chinese v0.1.0 project governance standards, effective on 2026-10-30. The Chinese source determines normative meaning. The [translation registry](../../../registry/translations.json) records the source and translation identities, source version and matching clause IDs.

[Chinese domain directory](../../../standards/project-governance/README.md) · [English repository entrance](../../../README.en.md) · [Language and update workflow — Chinese](../../../guides/INTERNATIONALIZATION.md)

## Read in responsibility order

| Document ID | Full English text | Chinese source | Stable clause IDs |
| --- | --- | --- | --- |
| `STD-PG-001` | [Project governance framework and responsibility interfaces](framework.md) | [项目治理领域总则与职责接口](../../../standards/project-governance/001-项目治理领域总则与职责接口--v0.1.0.md) | PGF-01–PGF-06 |
| `STD-PG-002` | [Project initiation, positioning and scope](initiation-scope.md) | [项目立项定位与范围规范](../../../standards/project-governance/002-项目立项定位与范围规范--v0.1.0.md) | PGI-01–PGI-06 |
| `STD-PG-003` | [Requirements, design and acceptance traceability](requirements-traceability.md) | [需求设计与验收追溯规范](../../../standards/project-governance/003-需求设计与验收追溯规范--v0.1.0.md) | PGT-01–PGT-06 |
| `STD-PG-004` | [Repository naming, directories and content placement](repository-content.md) | [仓库命名目录与内容归属规范](../../../standards/project-governance/004-仓库命名目录与内容归属规范--v0.1.0.md) | PGR-01–PGR-06 |
| `STD-PG-005` | [README branding and badges](readme-branding.md) | [README品牌与徽章规范](../../../standards/project-governance/005-README品牌与徽章规范--v0.1.0.md) | PGE-01–PGE-08 |
| `STD-PG-006` | [Documentation authoring and internationalization](documentation-i18n.md) | [文档编制与国际化规范](../../../standards/project-governance/006-文档编制与国际化规范--v0.1.0.md) | PGD-01–PGD-08 |
| `STD-PG-007` | [Git Workspace and Local Operations Standard](git-workspace.md) | [Git工作区与本地操作规范](../../../standards/project-governance/007-Git工作区与本地操作规范--v0.1.0.md) | PGW-01–PGW-10 |
| `STD-PG-008` | [Git Branch Synchronization and Conflict Handling Standard](git-integration.md) | [Git分支同步与冲突处理规范](../../../standards/project-governance/008-Git分支同步与冲突处理规范--v0.1.0.md) | PGB-01–PGB-11 |
| `STD-PG-009` | [Change proposals, review and merge](change-review-merge.md) | [变更提案审查与合并规范](../../../standards/project-governance/009-变更提案审查与合并规范--v0.1.0.md) | PGC-01–PGC-06 |
| `STD-PG-010` | [Work items, milestones and collaborative responsibilities](work-items-responsibility.md) | [工作项里程碑与协作职责规范](../../../standards/project-governance/010-工作项里程碑与协作职责规范--v0.1.0.md) | PGK-01–PGK-06 |
| `STD-PG-011` | [Testing, quality gates and evidence](quality-evidence.md) | [测试质量门禁与证据规范](../../../standards/project-governance/011-测试质量门禁与证据规范--v0.1.0.md) | PGQ-01–PGQ-06 |
| `STD-PG-012` | [Dependencies, configuration and supply chain](dependencies-configuration.md) | [依赖配置与供应链规范](../../../standards/project-governance/012-依赖配置与供应链规范--v0.1.0.md) | PGS-01–PGS-06 |
| `STD-PG-013` | [Security, privacy and operational boundaries](security-privacy.md) | [安全隐私与操作边界规范](../../../standards/project-governance/013-安全隐私与操作边界规范--v0.1.0.md) | PGP-01–PGP-06 |
| `STD-PG-014` | [Rights, licensing and third-party materials](rights-license.md) | [权属许可与第三方材料规范](../../../standards/project-governance/014-权属许可与第三方材料规范--v0.1.0.md) | PGL-01–PGL-08 |
| `STD-PG-015` | [Versions, tags and releases](version-release.md) | [版本标签与发行规范](../../../standards/project-governance/015-版本标签与发行规范--v0.1.0.md) | PGV-01–PGV-06 |
| `STD-PG-016` | [Deployment, configuration migration and rollback](deployment-migration-rollback.md) | [部署配置迁移与回滚规范](../../../standards/project-governance/016-部署配置迁移与回滚规范--v0.1.0.md) | PGU-01–PGU-06 |
| `STD-PG-017` | [Maintenance, response and compatibility commitments](maintenance-compatibility.md) | [维护响应与兼容承诺规范](../../../standards/project-governance/017-维护响应与兼容承诺规范--v0.1.0.md) | PGM-01–PGM-06 |
| `STD-PG-018` | [Deprecation, migration, archival and retirement](deprecation-retirement.md) | [弃用迁移归档与退役规范](../../../standards/project-governance/018-弃用迁移归档与退役规范--v0.1.0.md) | PGA-01–PGA-06 |
| `STD-PG-019` | [Files, caches, build artifacts and evidence lifecycle](materials-evidence-lifecycle.md) | [文件缓存构建物与证据生命周期规范](../../../standards/project-governance/019-文件缓存构建物与证据生命周期规范--v0.1.0.md) | PGX-01–PGX-06 |
| `STD-PG-020` | [Specification adoption, exceptions and upgrades](adoption-exceptions-upgrades.md) | [规范采用例外与升级规范](../../../standards/project-governance/020-规范采用例外与升级规范--v0.1.0.md) | PGN-01–PGN-06 |

## Use and maintenance

Start with the framework and the topic relevant to the project. Record exact source document/clauses, applicability, configuration, project-specific operations and necessary exceptions; keep the general standard in Standards rather than copying it into project repositories. Follow the [project governance guide — Chinese](../../../guides/PROJECT-GOVERNANCE.md) and the [completed synthetic example — Chinese](../../../examples/project-governance/README.md).

When the Chinese bytes change, compare the exact change against the translation, mark an unfinished update as outdated and fall back to the Chinese source. Maintain each translated clause, example and dependency together with its Chinese source.
