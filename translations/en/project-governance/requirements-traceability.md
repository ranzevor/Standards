# Requirements, design and acceptance traceability

**Source version:** 0.1.0　**Status:** adopted　**Effective date:** 2026-10-30

**Document ID:** STD-PG-003　**Language:** en　**Authority:** Chinese (zh-Hans) only

This is the full, non-authoritative translation of the [Chinese source](../../../standards/project-governance/003-需求设计与验收追溯规范--v0.1.0.md). In a conflict, consult the Chinese source. MUST/MUST NOT bind only when the applicability condition holds and the exact version is selected for adoption.

## Applicability, terms and responsibilities

Applies to traceable changes involving functional and non-functional requirements, research deliverables and defect fixes; it does not mandate a particular requirements-management platform. A requirement is an independently assessable obligation; a design decision explains the solution and trade-offs; an acceptance contract specifies inputs, observation points and expectations. Requirement owners define expectations, designers allocate responsibilities, executors bind implementations, and acceptance assessors judge results. Depends on [PGI](initiation-scope.md) and [PGF](framework.md); technical implementations reference exact L3/L4/L5 clauses.

## PGT-01 Requirement decomposition and stable identity

**Inputs and prerequisites:** Charter revision, success criteria, user tasks and applicable constraints.

**Procedure:** Assign stable IDs to requirements and state the actor, trigger, observable action/result, priority and source. Split composite goals with different failure mechanisms or acceptance responsibilities into linkable subrequirements; retain parent–child relationships without counting synonymous restatements as additional coverage.

**Outputs and acceptance:** Every necessary success criterion has a supporting requirement; duplicate IDs, requirements without sources and missing parent nodes are rejected. Requirements can be assessed separately, rather than relying on “everything works” as the sole criterion.

**Failure and recovery:** Ambiguous requirements enter clarification with specific unresolved inputs; implementers cannot fill in the requirement's expectations from actual implementation output.

**Positive example:** “Reliable conversion” is split into three requirements: the original file is unchanged, the output format is correct, and failure leaves no partial output.

**Direct failure example:** Marking “support all formats” accepted without a defined format set or error-handling rules.

**Valid adjacent case:** A simple typo fix needs only one requirement and an observation of the text before and after; three levels of decomposition are not mandatory.

**Checking entry point:** `checks/project_governance.py` checks IDs, parent–child relationships and source closure; semantic atomicity requires reading.

## PGT-02 Architectural decisions and interface constraints

**Inputs and prerequisites:** Requirements, existing architecture, data flows and deployment/invocation boundaries.

**Procedure:** Record an ADR for choices affecting data, compatibility, security or operating cost: context, options, decision, reasons, costs, conditions for replacement and affected requirements. Interfaces list providers/consumers, inputs/outputs, errors, timeouts, unknown outcomes and authoritative state; data constraints specify formats, units, identifiers, retention and migration responsibilities.

**Outputs and acceptance:** Each cross-component guarantee has one responsible owner; when an ADR is superseded, retain the old decision and its relationship to the new one rather than merely changing the conclusion date.

**Failure and recovery:** If a consumer depends on a guarantee that is not provided, block that interface and supplement the provider's contract or change the consumer; the fact that both interfaces are called HTTP does not justify ignoring differences in idempotency and errors.

**Positive example:** When choosing atomic output-file replacement, the ADR states the same-filesystem prerequisite and the permitted old/new file states after a crash.

**Direct failure example:** Two components each assume the other handles retry deduplication, resulting in duplicate charges.

**Valid adjacent case:** A single-function offline library can describe errors and value types in a design record without introducing a microservice ADR system.

**Checking entry point:** Check ADR/interface/requirement references and provider existence; concurrency and durability guarantees require substantive review and actual testing in the corresponding technical domain.

## PGT-03 From requirements to files, tests and delivery

**Inputs and prerequisites:** Stable requirements, candidate source objects, target paths and acceptance contracts.

**Procedure:** For each applicable requirement, record responsible files/symbols, test IDs, expected observations, execution entry points and deliverables; automated checks may use file digests or source-code coordinates, while non-code deliverables may use sections, figures/tables or data objects. Also record which requirements tests and deliverables prove; not every tool-support file needs a newly invented business requirement.

**Outputs and acceptance:** Necessary requirements have no gaps lacking implementation or acceptance; file paths resolve; deleted or renamed files trigger reference updates. A coverage matrix distinguishes the existence of a mapping from an executed pass.

**Failure and recovery:** If a test points to an old object, a symbol is absent or a deliverable is missing, mark unresolved, repair the object and recheck; do not merely update the digest to pretend it has been tested.

**Positive example:** REQ-03 maps to writer.commit, failure-injection test T-03 and the output-format description.

**Direct failure example:** Every requirement points to the same “all tests passed” string, with no way to locate specific observations.

**Valid adjacent case:** One parameterized test legitimately covers several requirements sharing a mechanism, with each one's inputs and criteria listed row by row.

**Checking entry point:** Paths, test IDs and delivery closure are checked automatically; independent review assesses whether tests actually prove the selected requirements.

## PGT-04 Independent expectations and result layers

**Inputs and prerequisites:** Requirement contracts, initial states, inputs, environments and predefined result criteria.

**Procedure:** Establish expectations from requirements or protocols first, then execute and save actual results. Separate structural checks, finite models, isolated execution and real targets; important mechanisms include positive cases, direct failures, valid adjacent cases and relevant combined boundaries. Fix comparison rules, units and tolerance sources for judging deviations.

**Outputs and acceptance:** Each result is bound to a requirement, candidate and environment; not-run/unknown/skip do not become pass. A negative research result may satisfy a predefined research-delivery contract without meeting a performance goal.

**Failure and recovery:** If a test itself is wrong, retain its original output, record the independent basis for correcting the expectation, and rerun; expected cannot be generated automatically from the current actual.

**Positive example:** The original-file digest is identical before and after failure and the output directory contains no partial artifact: these are independently observable states.

**Direct failure example:** Wrapping any return value with expected=actual and claiming requirement conformance.

**Valid adjacent case:** Inputs in two equivalent encodings produce the same normalized output; different results for every input are not required.

**Checking entry point:** [PGQ](quality-evidence.md) owns execution and evidence contracts; automated evaluators handle only explicitly defined finite result types.

## PGT-05 Change impact and dependency closure

**Inputs and prerequisites:** Differences between old and new requirements/interfaces/files and the current dependency graph.

**Procedure:** Follow consumer edges from changed nodes to list affected requirements, configurations, tests, documentation, translations and deliverables. Separate necessary dependencies from references; the necessary graph MUST NOT have missing nodes or use a cycle as grounds for approval. For each item of old evidence, decide reuse, supplemental verification, invalidation or non-applicability, explaining why its object, environment and proven proposition remain the same or have changed.

**Outputs and acceptance:** The impact set can be reproduced from the graph and differences; if any necessary dependency node is incomplete, do not claim the entire necessary closure complete.

**Failure and recovery:** On finding a missing edge, restore the relationship and expand the affected rechecks; do not hide a blocker by downgrading a “necessary” label. Parallel updates use revision comparisons; recompute closure after a conflict.

**Positive example:** When a field's unit changes from seconds to milliseconds, assess configuration, SDKs, examples and threshold tests together.

**Direct failure example:** Running only unit tests for changed files while ignoring protocol consumers dependent on them.

**Valid adjacent case:** If only comments change and executable code, configuration, environment and the proven proposition remain unchanged, the original execution evidence may be reused with recorded reasons.

**Checking entry point:** Transitive dependency graphs and stale bindings can be checked automatically; technical review verifies whether implicit consumers were missed in the impact assessment.

## PGT-06 Closure, exceptions and handover

**Inputs and prerequisites:** All necessary requirements, current acceptance results, residual risks and exception decisions.

**Procedure:** Distinguish requirement states as proposed/accepted/implemented/verified/rejected/deferred; verified MUST have passing results for the currently applicable contract. Exceptions identify exact requirements and alternative safeguards and are handled under [PGN](adoption-exceptions-upgrades.md), rather than simply deleting unmet requirements. Handover includes the current matrix, unfinished items and reproduction entry points.

**Outputs and acceptance:** Closure reasons agree with actual results; all necessary requirements are verified or have explicitly permitted exceptions. Deliverable existence does not make all requirements verified.

**Failure and recovery:** If new findings overturn a pass, add a reopened event and retain the old result; return to design, implementation or verification according to impact.

**Positive example:** A requirement is implemented but not yet verified on Windows; its state is implemented, not verified across all platforms.

**Direct failure example:** Deleting a failing test and marking its requirement complete.

**Valid adjacent case:** An explicitly rejected feature retains rejected and its rationale; implementation and tests need not be fabricated for it.

**Checking entry point:** Requirement states, exception references and necessary-completion closure are checked automatically; the authenticity of actual implementation and handover is reviewed separately.
