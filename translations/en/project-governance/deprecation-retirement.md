# Deprecation, migration, archival and retirement

**Source version:** 0.1.0　**Status:** adopted　**Effective date:** 2026-10-30

**Document ID:** STD-PG-018　**Language:** en　**Authority:** Chinese (zh-Hans) only

This is the full, non-authoritative translation of the [Chinese source](../../../standards/project-governance/018-弃用迁移归档与退役规范--v0.1.0.md). In a conflict, consult the Chinese source. MUST/MUST NOT bind only when the applicability condition holds and the exact version is selected for adoption.

## Scope and terms

Applies to replacement of interfaces/versions/specifications/coordinates, end of support, archival and service retirement; “no new features” does not automatically mean retirement. deprecated indicates alternatives and migration, archived restricts maintenance activity, retired ends the stated service/capability, and deleted removes specific objects; decide and verify the four separately. Decision-makers confirm scope, maintainers identify consumers, and data/platform owners handle retention and access. Depends on [PGM](maintenance-compatibility.md), [PGX](materials-evidence-lifecycle.md) and [PGN](adoption-exceptions-upgrades.md).

## PGA-01 Consumers and replacement relationships

**Inputs and prerequisites:** Objects proposed for replacement, existing versions/packages/links/services and support commitments.

**Procedure:** Inspect in-repository and known external consumers, installation/import/invocation coordinates, data formats and maintenance contacts; list replacements' exact identities and covered/excluded scope. Explicitly state risks and discovery methods for consumers that cannot be enumerated, rather than treating “unregistered” as “absent.”

**Outputs and acceptance:** Every known necessary consumer has handling and responsibility; replacements are not inferred from same names, and differences in relied-on guarantees are retained.

**Failure and recovery:** Newly discovered consumers update the migration set and window and trigger reassessment of stop conditions; without a replacement, provide continued-use risks, export or termination paths rather than fabricating equivalent alternatives.

**Positive example:** A package-coordinate change separately checks code imports, CI references and user installation commands.

**Direct failure example:** Declaring zero external consumers solely because an in-repository full-text search finds no matches.

**Valid adjacent case:** A private, undistributed prototype with verifiable usage scope may state no external consumers without inventing a list.

**Checking entry point:** Verify registered consumption graphs, paths and replacement objects; completeness and unknown-consumer risks require manual checking.

## PGA-02 Migration guidance and compatibility windows

**Inputs and prerequisites:** Exact old/new objects, obligation/interface/data differences and consumer usage scenarios.

**Procedure:** List retained, added, modified and removed elements; provide old/new coordinates, ordered steps, expected results, known incompatibilities and recovery. Windows specify start/end conditions and their decision basis; without a committed date, do not invent a deadline. Do not remove compatibility interfaces before necessary consumers exit.

**Outputs and acceptance:** Users can locate specific new objects from old ones and judge migration success against inputs; migration guides do more than say “upgrade to the latest version.”

**Failure and recovery:** Failed conversion preserves original data and errors, followed by reversible recovery or forward repair; lossy new formats explicitly state irreversibility and require recovery-point verification first.

**Positive example:** A configuration key rename explains unit changes, old-value conversion and rejection conditions.

**Direct failure example:** Concluding configuration can be copied directly because both versions have a same-named field.

**Valid adjacent case:** A navigation-only path migration may verify coordinates/anchors and preservation of exact content without inventing data conversion.

**Checking entry point:** Verify old/new mappings, references and declared compatibility matrices; actual conversion runs on the corresponding target.

## PGA-03 Data export, retention and access revocation

**Inputs and prerequisites:** Data/configuration/secret inventories, user rights and necessary retention/deletion conditions.

**Procedure:** Before service termination, provide applicable export methods, formats and integrity checks; classify and retain source, formal deliverables and necessary evidence while reclaiming rebuildable temporary materials. Revoke unnecessary access/tokens/resources on actual platforms, keeping secrets out of exports. Retention and deletion MUST both consider actual obligations rather than defaulting to permanent retention of all sensitive data.

**Outputs and acceptance:** Exports are readable and complete, residual access and data locations are verified, and backup-retention/expiry strategies are clear.

**Failure and recovery:** Failed export verification or undecided retention blocks the corresponding irreversible deletion; unknown revocation results require checking platform state rather than inferring success from a local task ending.

**Positive example:** After exporting synthetic user data, compare record counts and key fields before allowing deletion of the test service.

**Direct failure example:** Deleting the only database before verifying exports.

**Valid adjacent case:** A documentation project without persistent user data creates no export interface but retains necessary formal content and evidence.

**Checking entry point:** Retention/deletion prerequisite models; actual export/platform revocation undergo target acceptance.

## PGA-04 Archival and immutable history

**Inputs and prerequisites:** Proposed archival scope, current entry points, exact source/releases/evidence and maintenance states.

**Procedure:** Fix final identities and replacement descriptions; make current entry points accurately show maintenance/support states. Archival does not change existing licenses, retract users' existing copies or automatically delete repositories or data. Historical failures, decisions and original objects remain locatable and are not changed into current passes.

**Outputs and acceptance:** Historical readers can locate exact versions and necessary recovery materials; current and historical entry points do not simultaneously claim to be the sole effective version.

**Failure and recovery:** If critical entry points or security descriptions need correction after archival, decide changes under actual platform permissions/policies while retaining original identities; do not unarchive without reason or rewrite shared history.

**Positive example:** An archival notice links exact replacement versions and scope not migrated.

**Direct failure example:** Describing an archive operation as having deleted user data and revoked every key.

**Valid adjacent case:** A local project not relying on a platform's archive function can preserve history through immutable manifests and maintenance states.

**Checking entry point:** Record/content identities can be checked; actual archival/access effects require target-state read-back.

## PGA-05 Deletion conditions and failure recovery

**Inputs and prerequisites:** Deletion objects, reference closure, export/recovery verification, retention obligations and required decisions.

**Procedure:** Before deletion, recheck active references, necessary consumers, retention holds and recovery capability; list reversible/irreversible steps, expected reclamation/residue and error handling. Delete only the explicit set, never treating similar directory names as sufficient grounds. Read back residual objects and user entry points after the operation.

**Outputs and acceptance:** Objects still referenced, sole evidence, unverified exports or objects with unexpired retention MUST NOT be reclaimed as ordinary caches; executed deletion and unknown outcomes are recorded separately.

**Failure and recovery:** For partial deletion or unknown responses, inspect target facts rather than blindly expanding the set; recovery rebuilds from verified objects and identities, explicitly identifying irrecoverable losses.

**Positive example:** Reclaim unreferenced, rebuildable temporary dependencies while preserving lockfiles and original failure logs.

**Direct failure example:** Deleting sole failure originals or unverified backups to make space usage appear lower.

**Valid adjacent case:** Same-content caches with definite rebuild entry points and no holds/active references may be cleaned under the established reclamation policy.

**Checking entry point:** `retirement_ready` and PGX reference/reclamation models; actual deletion permissions and effects require separate verification.

## PGA-06 Retirement completion and later requests

**Inputs and prerequisites:** All necessary retirement tasks, data/permission/resource states and retention responsibilities.

**Procedure:** Check consumers, migration, export, revocation, resources and history preservation item by item; retain open/unknown rather than forcing every item complete. A retirement-completion statement identifies final objects, residual risks, necessary retention and actual later-contact boundaries; restart requires renewed confirmation of scope and resources rather than automatic restoration of old commitments.

**Outputs and acceptance:** Only satisfaction of all necessary conditions permits retired-complete; remaining retention tasks separately register responsibilities and expiry triggers.

**Failure and recovery:** If residual access or missed migration is found after retirement, reopen related tasks and control risks rather than rewriting the original completion record.

**Positive example:** A service has stopped while audit retention continues for its required period; states are registered separately.

**Direct failure example:** Inferring that all artifacts, backups and keys have disappeared because the repository web page returns 404.

**Valid adjacent case:** If the user decides only to stop maintenance without deletion, retained source is an intended result, not a retirement failure.

**Checking entry point:** Necessary-task closure and final-state consistency are checked automatically; actual residual resources and retention conditions require substantive review.
