# Work items, milestones and collaborative responsibilities

**Source version:** 0.1.0　**Status:** adopted　**Effective date:** 2026-10-30

**Document ID:** STD-PG-010　**Language:** en　**Authority:** Chinese (zh-Hans) only

This is the full, non-authoritative translation of the [Chinese source](../../../standards/project-governance/010-工作项里程碑与协作职责规范--v0.1.0.md). In a conflict, consult the Chinese source. MUST/MUST NOT bind only when the applicability condition holds and the exact version is selected for adoption.

## Scope and terms

Applies to requirements, defects, research, documentation, maintenance and security work; a small project without a team may use local versioned records and does not need hosted Issues or paid tools. A work item describes an assessable outcome; a milestone is a set of necessary deliverables, not a percentage promise. An owner is someone who actually accepts the work; unassigned is a valid state but cannot substantiate activity completion. Security details follow [PGP](security-privacy.md); acceptance follows [PGQ](quality-evidence.md).

## PGK-01 Classification, reproduction and acceptance conditions

**Inputs and prerequisites:** Report/requirement sources, exact objects, expected/actual results and impacts.

**Procedure:** Assign a stable ID and type (feature/defect/research/documentation/maintenance/security); defects provide minimal synthetic reproductions, environments and original outputs, while research provides questions, methods and exit conditions. Each item lists scope, acceptance conditions, dependencies and an owner or unassigned; suggestions in reports do not automatically become approved requirements.

**Outputs and acceptance:** Acceptance conditions distinguish delivery, failure, unknown and non-reproduction; sensitive content need not be placed in public Issues.

**Failure and recovery:** If information is insufficient, triage lists specific gaps and safe ways to supply it; do not change “currently unable to reproduce” into “user error.” Duplicates link to the exact original item while preserving evidence from different environments.

**Positive example:** A defect record specifies file encoding, command, expected exit code and actual truncated output.

**Direct failure example:** “Fix all problems” is the only description, leaving no way to judge completion at closure.

**Valid adjacent case:** A small documentation typo needs only before/after text and its location, not a crash dump.

**Checking entry point:** The work-item schema checks type/ID/conditions and dependency fields; substantive review assesses defect authenticity and requirement necessity.

## PGK-02 State transitions and closure reasons

**Inputs and prerequisites:** The current work-item revision and execution/verification results.

**Procedure:** Use open→triaged→in-progress→verification→closed; blocked/deferred retain the previous state and reason, while rejected/duplicate record the decision or original item. closed records a resolution: verified-fix/verified-delivery/not-reproducible/rejected/duplicate. Only the first two denote verified deliverables, and they must reference current acceptance conditions and evidence.

**Outputs and acceptance:** Verification that has not passed cannot yield verified-fix; closed-not-reproducible does not count as a verified fix. Each transition retains old and new states and the revision.

**Failure and recovery:** When a new counterexample overturns closure, append a reopened event and retain the old conclusion; closing an Issue does not revoke unknown in-flight effects.

**Positive example:** After code repair, the item enters verification; only when the reproduction input and regressions pass does it become verified-fix.

**Direct failure example:** Automatically marking a defect fixed after merging its PR while the real environment remains unverified.

**Valid adjacent case:** Research with a negative conclusion that satisfies its predefined contract uses verified-delivery, not verified-fix.

**Checking entry point:** The `transition_work_item` finite model checks states, results and closure reasons, not whether the actual work occurred.

## PGK-03 Necessary dependencies and milestones

**Inputs and prerequisites:** Deliverable sets, required work items, transitive necessary dependencies and the basis for committed dates.

**Procedure:** Each milestone lists its goal, necessary deliverables and exit conditions; separate required-consumption from reference. Completion includes transitive dependencies of necessary items and holds only when all states are verified and no open blockers remain. Distinguish dates as committed/estimate/unset; an estimate does not automatically become a commitment.

**Outputs and acceptance:** The completed set can be recomputed; the necessary graph has no missing nodes or circular approval. A current goal without a date is valid and does not justify fabricating external delivery agreements.

**Failure and recovery:** When a dependency is delayed, update the blocked scope and alternatives; removing a necessary item requires preserving the original set, differences and corresponding scope decision, rather than deleting failed items to raise completion percentages.

**Positive example:** A release depends on documentation, an installation package and a recovery drill; if any remains unverified, it is incomplete.

**Direct failure example:** Removing a blocking test from the milestone and then claiming 100%.

**Valid adjacent case:** Unfinished reference reading does not block delivery that relies on no related guarantee, provided it genuinely is not a necessary dependency.

**Checking entry point:** `milestone_ready` checks transitive closure, states and old/new sets; necessity and date commitments require substantive review.

## PGK-04 Division of work and single-writer control

**Inputs and prerequisites:** Shared files/state, each participant's scope and dependency interfaces.

**Procedure:** Assign specific inputs/outputs, file scopes, acceptance and interfaces; shared mutable objects use actual locks, leases, atomic conditions or single-writer integration. Parallel outputs are independent; integration reads complete differences and the current baseline. Saying “sole author” is not a substitute for concurrency control.

**Outputs and acceptance:** Each item's current owner and delivery interface can be located; later writes do not overwrite unread work. One person may perform several roles sequentially in a single-person project.

**Failure and recovery:** On a write conflict, first stop the conflicting update, preserve both differences and coordinate against the baseline; writes with expired leases or old revisions are rejected, rather than reviving old tasks under a new generation.

**Positive example:** Two people maintain documentation and independent tests separately, with central integration of exact differences.

**Direct failure example:** Two processes write the same manifest and the last save overwrites records added by the other.

**Valid adjacent case:** Two read-only analyses can read the same fixed input concurrently without a mutex.

**Checking entry point:** Record-level checks verify scope and revision; Agent-task/parallel semantics consume exact clauses from [L2, Chinese](../../../standards/L2/001-人类与-Agent-团队组织协作规范--v0.1.0.md). Actual lock effects require implementation acceptance.

## PGK-05 Handover, departure and responsibility continuity

**Inputs and prerequisites:** Current work items, necessary materials, access permissions, unknown effects and the recipient.

**Procedure:** Handover records versions/digests, completed facts, unfinished work and blockers, in-flight/unknown operations, reproduction commands and the next condition. Recipients confirm acquisition of necessary inputs and their scope; permission handover is granted/revoked in the real system, not fabricated as actual configuration by task records.

**Outputs and acceptance:** Recipients can locate current objects from recovery entry points; without a recipient, mark unassigned or limited-support rather than inventing a configured team.

**Failure and recovery:** If materials are missing or an operation's outcome is unknown, first verify the original object or authoritative state; handover cannot reset budgets, repeat side-effecting actions or delete failures.

**Positive example:** Maintenance handover includes the latest exact release, open security items and unverified migration results.

**Direct failure example:** Merely writing “continue to completion” without object, input or acceptance information.

**Valid adjacent case:** The same maintainer may continue non-secret project documentation in another tool while still pinning exact inputs.

**Checking entry point:** Handover fields and identities can be checked automatically; actual material acquisition, receipt and permission changes require manual or target-platform verification.

## PGK-06 Communication and public state

**Inputs and prerequisites:** Audiences, maintenance capacity, disclosure boundaries and actual progress.

**Procedure:** Status explanations state completed technical results, specific gaps, current blockers and necessary conditions; external reports distinguish plans, in-flight operations, unknown outcomes and verified completion. Management workload, internal queues or self-promises do not replace project facts; product documentation contains only information its own readers need.

**Outputs and acceptance:** Work items, milestones and user entry points have no contradictory states; events that have not happened are not reported as executed, and work still waiting is not reported as stopped.

**Failure and recovery:** On discovering an erroneous prior report, append an explicit correction referencing the original object and retain the original record; promptly route important risks to the interface responsible for that decision.

**Positive example:** A report states, “The Linux synthetic workflow passed; the Windows target was not executed; installer acceptance is still missing.”

**Direct failure example:** Claiming completed remote delivery when no commit or delivery entry point exists.

**Valid adjacent case:** Routine unchanged periods need no repeated broadcast, but explicit inquiries receive an accurate snapshot.

**Checking entry point:** Record-consistency checks can detect state conflicts; manual review judges whether the narrative is accurate, useful and appropriately placed.
