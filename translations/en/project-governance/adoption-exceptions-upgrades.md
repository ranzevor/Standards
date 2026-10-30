# Specification adoption, exceptions and upgrades

**Source version:** 0.1.0　**Status:** adopted　**Effective date:** 2026-10-30

**Document ID:** STD-PG-020　**Language:** en　**Authority:** Chinese (zh-Hans) only

This is the full, non-authoritative translation of the [Chinese source](../../../standards/project-governance/020-规范采用例外与升级规范--v0.1.0.md). In a conflict, consult the Chinese source. MUST/MUST NOT bind only when the applicability condition holds and the exact version is selected for adoption.

## Applicability, identity and responsibilities

Applies to project specification selection, draft trials, formal adoption, exceptions, upgrades and withdrawal. Technical reference, project adoption and formal adoption by the Standards system are recorded separately; document publication does not automatically cause project adoption. Decision-makers confirm applicable scope and risks, technical leads map dependencies, and acceptance assessors fix implementation objects and contracts. The single general specification body resides in Standards; projects retain only exact references, applicability, configuration, project operations and necessary exceptions. This specification extends the project-governance content of [L6 ADP-01–08, Chinese](../../../standards/L6/001-项目采用与实现验收接口规范--v0.1.0.md), without establishing a second set of contradictory states.

## PGN-01 Pin specifications and adoption types

**Inputs and prerequisites:** Project requirements, the single Standards registry, document IDs/versions/paths/SHA256 and clause sets.

**Procedure:** Select technical-reference/trial/adopted and fix full identities and clauses document by document; if the decision is not-decided, do not fill in approvers or approval times. Draft trials explicitly state scope and risks without changing document state; formal adoption requires a real decision by an authorized actor on the exact object and scope.

**Outputs and acceptance:** Selected bodies resolve with matching digests, rather than merely stating “all latest specifications.” Projects do not copy full general specifications locally to create another effective entry point.

**Failure and recovery:** Version/digest mismatch remains unresolved while exact sources or migrations are investigated; moving a path does not automatically approve a content upgrade.

**Positive example:** A synthetic project references STD-PG-007@0.1.0 and PGW clauses with technical-reference status.

**Direct failure example:** Inheriting an old approval for another digest object using a same-named 0.1.0 document.

**Valid adjacent case:** A project trials a draft with explicit scoped risks; the document remains draft and the system state is unchanged.

**Checking entry point:** `checks/project_adoption.py` and governance adoption checks verify exact references; actual decision authority and process require factual evidence.

## PGN-02 Clause-by-clause applicability and dependencies

**Inputs and prerequisites:** Actual project functions/data/environments/commitments and necessary provider-consumer relationships.

**Procedure:** Select applicable/not-applicable/undetermined for each clause, stating specific triggers or absent facts. Necessary dependencies of applicable clauses select exact provider clauses, versions/digests, guarantees and acceptance responsibilities; reference-only links do not automatically become necessary execution edges.

**Outputs and acceptance:** Applicable closure resolves without missing necessary dependencies or circular approval; not-applicable is not a synonym for untested.

**Failure and recovery:** If functionality is uncertain, retain undetermined and list inputs needed for the judgment; once an actual trigger is found, update applicability and acceptance instead of hiding defects behind “not applicable.”

**Positive example:** A specification project without deployment does not apply PGU runtime deployment, while content, versions, evidence and maintenance descriptions remain applicable.

**Direct failure example:** An application has account login but marks permission controls not applicable because no test account exists.

**Valid adjacent case:** A monolith without a message queue is not forced to add an Outbox; it selects only actual transaction-boundary obligations.

**Checking entry point:** Adoption dependency closure is checked automatically; substantive technical review assesses actual functionality and necessity.

## PGN-03 Project configuration, operations and acceptance interfaces

**Inputs and prerequisites:** Selected clauses, project files/tools/versions/configuration and supported targets.

**Procedure:** Implement specification parameters, actors and actions in project records: specific directories, commands, environments, threshold sources, acceptance conditions and responsibilities. Project parameters cannot arbitrarily lower protocol constants or minimum security requirements set by technical specifications; project-specific runbooks describe their own operations rather than copying specification bodies.

**Outputs and acceptance:** Clauses and project actions/tests/deliverables are bidirectionally traceable; “a specification reference exists” does not mean implementation or acceptance has occurred.

**Failure and recovery:** Missing environments/operations are marked not-run/blocked with necessary inputs listed; passing this repository's finite models cannot imply a real project passed.

**Positive example:** A project implements the PGQ contract through its own Linux command and synthetic inputs while the Windows target remains not-run.

**Direct failure example:** Treating example ports and timeout values in a specification as fixed thresholds for every project.

**Valid adjacent case:** Different projects implement the same clause with different tools, provided they satisfy the same guarantee and specific acceptance.

**Checking entry point:** L6 record schemas/governance models check interfaces; project contracts execute against actual targets.

## PGN-04 Exceptions, compensation and expiry

**Inputs and prerequisites:** Exact unmet clauses already effectively adopted by the project, triggering facts, risks, alternative safeguards, responsibilities and permitted decision scope.

**Procedure:** Deviations when merely trialing drafts are recorded as trial selections and risks, not misrepresented as formal exceptions to effective obligations. Exceptions list reasons, applicable components/environments, compensating controls, start/end/review triggers, steps to restore conformance and decisions. MUST NOT use exceptions to alter third-party constraints, others' rights or non-waivable requirements without authority; missing decisions remain proposed rather than acting as approved gate bypasses.

**Outputs and acceptance:** Exceptions identify one item or an explicit set, not “everything as needed”; compensation is verifiable, and an expired or review-triggered exception MUST NOT automatically remain effective without a renewed decision.

**Failure and recovery:** Reassess failed compensation, expiry or scope expansion; restore original requirements or obtain a new explicit decision, retaining old exceptions and actual nonconformance facts.

**Positive example:** Retain old-format reading for a limited period, add validation and read-only restrictions, and state explicit migration exit conditions.

**Direct failure example:** “Temporarily do not follow the security specification” without specific clauses, compensation or scope.

**Valid adjacent case:** A requirement whose trigger is absent is recorded not applicable, without inventing exception approval for it.

**Checking entry point:** `exception_valid` checks identity, state, time/triggers and compensation results; risk acceptability and waivability require expert judgment.

## PGN-05 Upgrade impacts and explicit decisions

**Inputs and prerequisites:** Pinned old objects, proposed new objects, clause/dependency/acceptance differences and the project's current implementation.

**Procedure:** Compare retained, added, modified and removed elements, necessary dependencies and exception impacts; create project migration and re-verification plans. After approval, update adoption records using expected revisions, locating original selections and upgrade decisions through Git versions or the project's existing decision system; new upstream versions do not silently upgrade downstream consumers.

**Outputs and acceptance:** New records point only to objects actually decided upon; old evidence is reused or invalidated item by item according to object/environment/proposition, and new requirements receive actual supplemental verification.

**Failure and recovery:** On concurrent revision mismatch, reread current selections and compare again; failed upgrades restore old selections or repair forward under compatibility contracts. Reverting a version number is not equivalent to reverting data/external effects.

**Positive example:** A new specification changes configuration units; the project migrates values, documentation, tests and exceptions together.

**Direct failure example:** A scheduled script replaces all adoption hashes with latest without recording decisions.

**Valid adjacent case:** If only path layout changes and exact content is unchanged, verify path changes through Git diff and correct references; retain necessary consumer migration instructions while specification obligations remain unchanged.

**Checking entry point:** The `upgrade_adoption` finite model checks old/new identities, revisions and decisions; actual impact adequacy requires substantive review.

## PGN-06 Withdrawal, invalid references and recovery

**Inputs and prerequisites:** Withdrawal/rejection decisions, invalid references, existing consumers and replacement/retention conditions.

**Procedure:** Record rejection of new adoption, withdrawal of existing selections, repeal of specifications and cessation of implementation separately. Preserve acquisition entry points for old objects and decisions through Git objects, exact release versions and the project's existing decision system. For invalid references, first look for available sources of the same identity; if none exists, limit corresponding conformance claims rather than filling gaps with same-named objects. Consumer migration and retention follow PGA.

**Outputs and acceptance:** Current scope and unresolved items are clear, and old approvals/failures are not rewritten; withdrawing specification references does not automatically undo external effects that already occurred.

**Failure and recovery:** Restoring adoption requires rechecking objects, scope, dependencies and decisions without reviving expired exceptions; historical evidence proves historical facts only.

**Positive example:** A project rejects a new revision and continues pinning an old selection with an exact obtainable source, recording risks.

**Direct failure example:** Deleting adoption records and claiming the project never operated under that specification.

**Valid adjacent case:** Removing a draft technical reference that never became formal adoption requires only an accurate record of the reference change.

**Checking entry point:** State and reference/history-chain consistency checks; actual decisions and consumer effects are verified separately.
