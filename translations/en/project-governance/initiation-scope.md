# Project initiation, positioning and scope

**Source version:** 0.1.0　**Status:** adopted　**Effective date:** 2026-10-30

**Document ID:** STD-PG-002　**Language:** en　**Authority:** Chinese (zh-Hans) only

This is the full, non-authoritative translation of the [Chinese source](../../../standards/project-governance/002-项目立项定位与范围规范--v0.1.0.md). In a conflict, consult the Chinese source. MUST/MUST NOT bind only when the applicability condition holds and the exact version is selected for adoption.

## Scope, terms and inputs

Applies to new projects, major changes of direction and scope changes in existing projects; a small fix may reference the original initiation and record differences without initiating the project again. A project charter records the problem, audience, business outcome, boundaries and entry/exit conditions; it is not a promise of business returns or resources. The decision-maker confirms purpose and scope, the technical lead assesses solutions and constraints, and the executor works within the selected scope; unassigned responsibilities must be recorded truthfully. Normative strength, the single authoritative body and the four state axes follow [PGF](framework.md).

## PGI-01 Define the problem and business outcome

**Inputs and prerequisites:** The problem's source, target users and current handling; without a clear problem, the state is discovery.

**Procedure:** 1) Describe the audience and problem through an observable task; 2) state the current baseline, expected changes after delivery and adjacent problems not being solved; 3) distinguish deliverables from business outcomes; 4) give each success criterion an observation window, measurement method and source, recording an unmeasured baseline as unknown.

**Outputs and acceptance:** The charter's problem, audiences, outcome and success_criteria can be explained through the same scenario; each success criterion can be judged pass/fail/unknown, without treating file counts as user outcomes.

**Failure and recovery:** If measurable data is unavailable, first describe how to obtain it or use observable exploration exit conditions instead; do not fabricate improvement percentages. If audiences conflict, record their goals and priorities separately before deciding scope.

**Positive example:** The outcome of an offline CSV converter is that users can convert files in specified encodings into an agreed column order; cloud synchronization is a non-goal.

**Direct failure example:** “Complete ten pages” is the sole criterion for success in every user task.

**Valid adjacent case:** A feasibility study aims to obtain reproducible experiments and clear feasible/infeasible boundaries, without promising a positive result.

**Checking entry point:** `checks/project_governance.py` checks success-criterion identities, states and measurement fields; the decision-maker substantively reviews the truth of the audience/problem and business value.

## PGI-02 Set boundaries and input resources

**Inputs and prerequisites:** Goals, existing systems/data, participants, environments, time, budget and the actual availability of equipment.

**Procedure:** List in_scope, out_of_scope and constraints; for each resource, record its provider, availability state, permitted use and the impact of its absence. Distinguish technical dependencies from external decisions, and committed limits from estimates and unknowns; outputs, data retention and support scope also form part of the boundaries.

**Outputs and acceptance:** Each major deliverable belongs to a scope category; the same identity cannot be both in scope and excluded. An unknown budget is not automatically unlimited resources; equipment not yet obtained blocks only activities dependent on it.

**Failure and recovery:** If a resource becomes unavailable, update dependencies and the blocked scope, and submit reduction or substitution proposals to the decision-maker; the executor does not silently delete committed features.

**Positive example:** Inputs are limited to local files selected by users themselves, and outputs are written only to the destination directory; no account system is needed.

**Direct failure example:** Automatically adding paid hosting and user-data collection because a cloud SDK is already present.

**Valid adjacent case:** Research with an undecided budget first performs offline experiments whose prerequisites are already met; other activities remain blocked.

**Checking entry point:** Scope-set overlap, resource states and dependency references can be checked automatically; usage rights and resource commitments require the original decisions.

## PGI-03 Start, pause and exit conditions

**Inputs and prerequisites:** Scope, key risks, owners or unassigned states, and stage deliverables.

**Procedure:** Define entry conditions for discovery, active, blocked, accepted and retired; starting requires at least a clear scope, work currently possible and responsibility interfaces. Distinguish successful delivery, an infeasibility conclusion, cancellation and handover in exit conditions; do not record cancellation as successful delivery. Decisions and state events carry the project revision.

**Outputs and acceptance:** The current state has evidence satisfying its entry conditions; blocked points to specific missing conditions and how to resolve them; accepted MUST satisfy all necessary success criteria.

**Failure and recovery:** When a key prerequisite changes, first preserve executed results, record the impact, and then have the appropriate decision-maker adjust the stage. Do not write “not executed” before verifying an unknown external outcome.

**Positive example:** Unavailable hardware blocks only on-board measurements; documentation and simulation still have explicit work items.

**Direct failure example:** All necessary acceptance checks are not-run, but the project is accepted because its progress bar is full.

**Valid adjacent case:** Evidence of infeasibility satisfies a research project's predefined exit conditions.

**Checking entry point:** The state model rejects a transition to accepted without necessary deliverables; whether cancellation is appropriate and who may decide are matters of manual factual judgment.

## PGI-04 Scope-change differences and decisions

**Inputs and prerequisites:** The current revision, original scope, proposed_delta and requirement sources; a typo that does not change the goal is not scope expansion.

**Procedure:** List additions, removals and modifications individually, with reasons, affected requirements/interfaces/resources/success criteria and compatibility risks. Record decisions as pending/approved/rejected with the exact revision; after approval, update scope using an expected-revision comparison while retaining the old sets and decision, not merely the latest text.

**Outputs and acceptance:** Every scope change traces back to old and new sets and a decision; the new revision is continuous with previous records, and stale concurrent updates are rejected.

**Failure and recovery:** If revisions differ, reread the current scope, merge the differences and obtain a new decision; if an approval result is lost, verify the original decision identity rather than creating a duplicate change. Rejected expansion MUST NOT be executed by renaming it a technical optimization.

**Positive example:** Before adding cloud synchronization, list account, cost, data and support impacts and obtain the corresponding scope decision.

**Direct failure example:** Deleting a failing feature, overwriting the old scope and declaring the original goal 100% complete.

**Valid adjacent case:** Correcting spelling in documentation without changing user tasks or success criteria can follow the editing process.

**Checking entry point:** The `apply_scope_change` finite model checks preservation of old sets, decision state and revision; approval authenticity and the necessity of the change require substantive review.

## PGI-05 Risks, dependencies and exploratory work

**Inputs and prerequisites:** Unknown technical/business conditions, potential impacts, and provider/consumer relationships in dependencies.

**Procedure:** For each risk, list its trigger, impact, monitoring method, mitigation method, residual risk and handling responsibility. Turn unknowns into verification work with exit criteria; list deliverables and acceptable states for necessary dependencies. Link exploration results to the original risk; without data on effectiveness, MUST NOT claim the risk has been reduced.

**Outputs and acceptance:** Key risks have executable verification or handling measures; blocked work can be traced to missing dependencies. Check necessary dependency closure according to [PGT](requirements-traceability.md).

**Failure and recovery:** If an experiment refutes a hypothesis, update feasibility and scope choices rather than rewriting the hypothesis after the fact to fit the result; if a dependency is permanently canceled, assess substitution or exit.

**Positive example:** First measure the upper memory bound using de-identified synthetic files, then decide the largest supported input.

**Direct failure example:** Changing “feasibility remains to be proved” to “no risk” without performing verification.

**Valid adjacent case:** Selecting a mature library still leaves this project's distinctive format-compatibility checks, without requiring repetition of all upstream research.

**Checking entry point:** Check risk IDs, dependency cycles and verification references; expert review assesses impact severity and mitigation effectiveness.

## PGI-06 Charter handover and adoption interfaces

**Inputs and prerequisites:** The decided charter, unresolved items, success criteria and subsequent owners.

**Procedure:** Turn success criteria into stable PGT requirements, deliver work items to PGK and supply PGN with the basis for governance-clause applicability. Handover lists the receiving scope, current revision, outstanding risks, resource-access handover and confirmation state; without a recipient, mark unassigned rather than inventing a team.

**Outputs and acceptance:** Downstream references identify the exact charter revision and allow reconstruction of the original problem and boundaries; receipt confirmation is not implementation acceptance.

**Failure and recovery:** If the recipient cannot obtain inputs, supply the necessary objects or keep the work blocked; a departing owner does not “clear responsibility” by deleting history.

**Positive example:** A synthetic project charter maps SC-01 to REQ-01 and an offline conversion test.

**Direct failure example:** Treating ExampleOwner in a template as a real maintainer who has already confirmed.

**Valid adjacent case:** In a single-person project, the same person handles initiation and development; the facts of independent review are addressed separately.

**Checking entry point:** For templates and completed examples, see the [project governance examples, Chinese](../../../examples/project-governance/README.md); tools check ID references and states, not the authenticity of actual handover.
