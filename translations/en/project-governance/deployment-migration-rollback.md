# Deployment, configuration migration and rollback

**Source version:** 0.1.0　**Status:** adopted　**Effective date:** 2026-10-30

**Document ID:** STD-PG-016　**Language:** en　**Authority:** Chinese (zh-Hans) only

This is the full, non-authoritative translation of the [Chinese source](../../../standards/project-governance/016-部署配置迁移与回滚规范--v0.1.0.md). In a conflict, consult the Chinese source. MUST/MUST NOT bind only when the applicability condition holds and the exact version is selected for adoption.

## Applicability, non-goals and roles

Applies when a project places code/configuration into a runtime environment, changes persistent data or commits to an operational service; documentation-only projects with no deployment object may explicitly record non-applicability without inventing a production environment. Deployment places an exact artifact in a target environment; migration changes data/configuration semantics; rollback restores a set of mutually compatible states and may not undo external effects. Deployment owners manage operations, data owners manage migration/recovery, and acceptance assessors check business and technical criteria. Infrastructure and database mechanisms reference their respective L4 bodies; this specification manages project sequencing, compatibility windows and responsibilities.

## PGU-01 Environment and artifact prerequisites

**Inputs and prerequisites:** Release manifests, target resources/accounts/regions, effective configuration, current versions and permitted side effects.

**Procedure:** Read back exact targets and current states and confirm actual separation of test, rehearsal and production environments; pin artifact digests and configuration/data versions, listing necessary permissions/windows and affected consumers. Do not write when target identity is missing; environment-variable or directory names are not proof of isolation.

**Outputs and acceptance:** Planned targets, artifacts and configuration agree with reality, and predeployment states can be located; projects without deployment retain reasons for non-applicability.

**Failure and recovery:** If targets or digests differ, stop that step and verify provenance; MUST NOT fall back to an arbitrary “most recently successful” object. If initiated operations have unknown responses, inspect actual deployment state before deciding recovery.

**Positive example:** Rehearsal uses a separate database and synthetic data, with resource IDs different from production and confirmed by read-back.

**Direct failure example:** Configuration named staging points to a production database unnoticed.

**Valid adjacent case:** An offline library tests only installation/import without creating a fictitious service deployment.

**Checking entry point:** Finite checks of plan identities and states; actual environment isolation undergoes acceptance on the cloud/runtime target.

## PGU-02 Migration classification and compatibility windows

**Inputs and prerequisites:** Old/new code, configuration/data formats, read/write consumers and migration scripts.

**Procedure:** List a compatibility matrix: old code reading/writing new data, new code reading/writing old data, and old/new configuration combinations; distinguish reversible steps, steps requiring recovery points and irreversible steps. Set observation and exit conditions for expand→backfill→switch→contract; do not remove compatibility fields before old consumers exit.

**Outputs and acceptance:** Permitted version combinations within every window are explicit; migrations have idempotency, resumability, unknown-outcome criteria and authoritative progress. Include configuration-unit and default-value changes.

**Failure and recovery:** Do not enter contraction while backfill is incomplete or old readers remain; concurrent progress uses target versions/watermarks to prevent old-state overwrites. Specific database transaction/locking semantics follow the selected database contract.

**Positive example:** A new column starts optional, backfill checks missing counts, readers switch, and constraints are added only after confirming old writers have exited.

**Direct failure example:** Deleting an old field before releasing consumers that still depend on it.

**Valid adjacent case:** A purely static documentation update without persistent-data migration may assess only link and cache compatibility.

**Checking entry point:** `deployment_safe` checks declared matrices and stage conditions; actual database behavior is verified with exact target tools.

## PGU-03 Backup and recovery-point verification

**Inputs and prerequisites:** Critical state, recoverable points, backup scope/identity, keys and environments needed for recovery.

**Procedure:** Before irreversible steps, obtain recovery points meeting project commitments such as RPO/RTO; verify readability, integrity and the actual recovery process, not merely backup-file existence. Record included/excluded data, configuration, permissions and external effects, explicitly identifying revocations/corrections that must be replayed after recovery.

**Outputs and acceptance:** The selected recovery point can restore necessary state under the contract, with recovery time/loss windows compared against commitments; untested recovery capability is not marked verified.

**Failure and recovery:** Corrupt backups, unavailable keys or failed recovery verification block irreversible steps dependent on that recovery point; recheck after repair rather than closing the issue by renaming a backup file.

**Positive example:** After restoration into an isolated database, verify totals, key invariants and application reads before allowing production migration.

**Direct failure example:** A backup log says “complete,” but no recovery verification exists, yet rollback is declared safe.

**Valid adjacent case:** A rebuildable static service without persistent state may use an exact old artifact as its recovery object without mandatory database backup.

**Checking entry point:** Recovery-point states and necessary scope are checked automatically; actual recovery, RPO/RTO and key availability are tested on the target.

## PGU-04 Rollout steps, observation and stop conditions

**Inputs and prerequisites:** Compatibility windows, verified recovery points, deployment order, business metrics and explicit threshold sources.

**Procedure:** Record starting conditions, actions, expected states and maximum waits step by step; check health and business criteria before traffic switching/enablement. Thresholds derive from actual project commitments or measurements, not a vendor default generalized to all projects. Concurrent deployments use actual leases/version comparisons to prevent overwrites.

**Outputs and acceptance:** Every step has observable success, failure and unknown terminal states; reaching a stop threshold enters the predetermined response rather than expanding impact further.

**Failure and recovery:** After timeout, inspect actual versions, migration states and traffic rather than assuming non-execution; repeats follow their idempotency contracts, and old-generation actions cannot continue writing.

**Positive example:** After switching a small traffic percentage, compare predefined error rates and core operations, not merely process liveness.

**Direct failure example:** Rerunning a script that may duplicate charges while migration state is unknown.

**Valid adjacent case:** A small local application update uses synthetic acceptance before/after installation without requiring a cloud canary-traffic platform.

**Checking entry point:** Stage/timeout/authoritative-state models; actual rollout mechanisms undergo cloud, desktop, mobile or other domain acceptance.

## PGU-05 Choose rollback or forward repair

**Inputs and prerequisites:** Actual failures, current code/configuration/data/external effects and compatibility matrices.

**Procedure:** First determine whether the old program can safely read/write current data; if permitted, restore exact old artifacts and configuration and recheck. If incompatible or already irreversible, select a verified recovery point or forward repair, stating data loss/external effects and required decisions. Reverting files does not undo messages, payments, notifications or disclosure.

**Outputs and acceptance:** After recovery, key invariants, user operations and permissions all satisfy contracts, and current references identify the actual recovery objects.

**Failure and recovery:** Failed rollback enters an explicit emergency path while retaining current state and raw logs; do not compound damage by successively trying several unknown old versions.

**Positive example:** Old versions cannot write the new data format, so direct binary downgrade is prohibited and a forward-compatible patch is selected.

**Direct failure example:** Restoring only an old container and declaring that the new Schema and already emitted external events have all been rolled back.

**Valid adjacent case:** A configuration-only change with a verified old configuration and backward-compatible data may not need database restoration.

**Checking entry point:** The `rollback_allowed` finite model checks matrices, irreversibility and recovery points; actual recovery results are tested item by item.

## PGU-06 Post-rollout acceptance and record handover

**Inputs and prerequisites:** Actual target states, business observations, final artifact/configuration/data identities and residual risks.

**Procedure:** Check necessary user tasks, interfaces, data integrity and monitoring before/after deployment; register final running objects, migration progress, unfinished cleanup/compatibility windows, recovery entry points and responsibilities. Assign subsequent contraction, observation and support to maintenance work items.

**Outputs and acceptance:** Plans and actual states can be compared; deployment is marked complete only when necessary acceptance for selected targets is satisfied. Unexecuted platforms or real transactions remain not-run.

**Failure and recovery:** Reassess rollback/forward repair for delayed findings using current authoritative state rather than old predeployment assumptions; record corrections and consumer notices.

**Positive example:** Continue observing for the agreed window after rollout and execute a separate contraction task once old writers exit.

**Direct failure example:** Closing every migration and maintenance item merely because the deployment command exits 0.

**Valid adjacent case:** Non-applicability of the deployment topic to a documentation project does not prevent acceptance of local content, links and adoption interfaces.

**Checking entry point:** Completion closure and handover records are checked automatically; actual business/data states are judged against target contracts.
