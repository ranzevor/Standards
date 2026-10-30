# Change proposals, review and merge

**Source version:** 0.1.0　**Status:** adopted　**Effective date:** 2026-10-30

**Document ID:** STD-PG-009　**Language:** en　**Authority:** Chinese (zh-Hans) only

This is the full, non-authoritative translation of the [Chinese source](../../../standards/project-governance/009-变更提案审查与合并规范--v0.1.0.md). In a conflict, consult the Chinese source. MUST/MUST NOT bind only when the applicability condition holds and the exact version is selected for adoption.

## Applicability, terms and responsibilities

Applies to changes in source code, specifications, tests, permissions, configuration and deliverables; a PR may be a platform pull request or an equivalently verifiable local change proposal. The baseline is the exact object before modification, the candidate is the complete object proposed for acceptance, and the integration object is the object ultimately entering the target branch; branch names cannot substitute for any of these. Authors deliver differences and self-checks, independent reviewers assess technical content, and mergers verify exact prerequisite states. Depends on [PGT](requirements-traceability.md), [PGB](git-integration.md) and [PGQ](quality-evidence.md).

## PGC-01 Fix the baseline, scope and risk

**Inputs and prerequisites:** Requirements, target branch/content tree, current uncommitted changes and proposed modification scope.

**Procedure:** For Git repositories, read the baseline commit/tree, derive the candidate tree from the actual worktree under review and obtain complete differences through Git diff; distinguish existing uncommitted changes from this change's differences. Offline release packages use verified build manifests to fix object identity. The proposal lists goals, changed and unchanged scope, dependencies, sources, compatibility and rollback. Classify editorial, behavioral, public-interface/persistent-data/security/gate changes by actual impact to determine necessary review and acceptance, rather than classifying risk by diff line count.

**Outputs and acceptance:** The exact baseline and complete differences are obtainable, including additions, deletions, modes and generated outputs; changes beyond scope have explicit reasons and corresponding decisions.

**Failure and recovery:** If the baseline is unknown or others' changes are mixed in, first reread state and provenance and separate differences or coordinate integration; do not overwrite unread work.

**Positive example:** A three-line permission-check change is reviewed as a security-behavior change.

**Direct failure example:** Packaging a critical gate relaxation as “minor formatting corrections” to avoid review.

**Valid adjacent case:** A whitespace-only adjustment with demonstrated unchanged semantics may receive proportionate lightweight review.

**Checking entry point:** Tools check baseline/candidate identities, difference scope and risk states; substantive review checks the truth of risk classification.

## PGC-02 Author self-check and a reviewable candidate

**Inputs and prerequisites:** The complete candidate, change requirements, test expectations, dependencies and sources.

**Procedure:** Authors check implemented behavior, failure recovery, compatibility, sources and content placement item by item; run affected checks and provide commands, actual results, unverified targets and known defects. Supply the current candidate's Git tree and baseline commit, or its offline release-package identity. Store necessary raw results in a separate run directory or evidence store and provide exact entry points. Describe generated outputs and regeneration commands through build rules.

**Outputs and acceptance:** Reviewers can obtain exact inputs, reproduce key behavior and find unfinished items without conversational background; label self-checks author-self-review, not independent conclusions.

**Failure and recovery:** If bodies are missing, inputs truncated or necessary checks unrun, supply the corresponding objects; preserve original outputs of failed checks and produce new results after repair, rather than rewriting failure logs as success.

**Positive example:** A change proposal supplies old and new interfaces, negative-case reproduction, valid adjacent cases and original failure logs.

**Direct failure example:** Providing only file counts, a directory tree and “self-tests passed.”

**Valid adjacent case:** Unchanged dependency research may be reused under an impact record showing that identity and propositions remain consistent; repeated research is not mandatory.

**Checking entry point:** Proposal/evidence bindings are checked automatically; self-check completeness requires manual checking.

## PGC-03 Substantive independent technical review

**Inputs and prerequisites:** The exact candidate and author self-check, actual changes, required expertise and independent-review arrangements.

**Procedure:** Reviewers actually inspect bodies/implementations, necessity, implementability, failure and valid boundaries, source support, interface responsibilities, independent test expectations and content placement. Replay negative cases or supply independent reasoning for important mechanisms rather than merely restating the author's synopsis. Record reviewer identity, method, actual read/execution scope, findings and limitations; independence depends on the real process and is not self-proved by using another name.

**Outputs and acceptance:** Each scope unit has a specific technical judgment and evidence location; conclusions are not-run/partial/fail/pass. A full pass requires all necessary scope reviewed with no open blockers.

**Failure and recovery:** If expertise or inputs are insufficient, mark only the corresponding scope partial/blocked, specifying gaps and continuation conditions; counts of other structural checks cannot be assembled into semantic coverage.

**Positive example:** A reviewer finds that restoring an old snapshot revives terminal tasks and supplies a direct counterexample and a valid recovery case that must not be wrongly rejected.

**Direct failure example:** An author copies their own checking report into an “independent approval” field.

**Valid adjacent case:** The same reviewer reuses an earlier judgment on exactly identical bytes while actually checking new differences and dependency impacts.

**Checking entry point:** Machines check only record identities, scope and states; sentence-by-sentence adequacy, actual independence and expert judgments belong to manual review.

## PGC-04 Defect repair and re-review after candidate changes

**Inputs and prerequisites:** Finding IDs, exact failing objects, counterexamples, impacts and repair criteria.

**Procedure:** Record each finding's severity and blocking conditions; the author's response lists changed files/clauses, the actual repair mechanism, negative/valid-adjacent-case results and unrepaired parts. Recompute impact when the candidate changes; old conclusions remain bound to old digests. Reviewers check closure against all original criteria, rather than closing a three-location finding after fixing only two.

**Outputs and acceptance:** closed has complete criterion rechecks and new object identity; partial repairs remain open/partial, and necessary regressions actually run against the new object.

**Failure and recovery:** If a repair introduces a new defect or a test expectation is wrong, retain the old process, reopen the finding and correct independent criteria; do not disguise a new object as the previously reviewed one.

**Positive example:** An effect-status error across three documents is corrected and rechecked at every location, with all three locations listed.

**Direct failure example:** Updating only the hash and state in a finding table without rereading changed content.

**Valid adjacent case:** If only the results display page changes and technical content is unchanged, closeout checks may follow the demonstrated bounded differences.

**Checking entry point:** `validate_change` checks finding states, candidate bindings and scope sets; independent review judges whether closure satisfies causal criteria.

## PGC-05 Merge prerequisites and concurrency protection

**Inputs and prerequisites:** The proposed integration object, current target HEAD, necessary checks/reviews and actual branch constraints.

**Procedure:** Reread target HEAD and compare it with the expected baseline; map the actual integration object produced by merge, squash or rebase to the verified object and recheck the new object when necessary. Confirm no open blockers, current results for necessary gates and the real existence of required decisions before merging. Platform protection configuration must be read from the actual platform; policy files and badges do not establish that it is configured.

**Outputs and acceptance:** The merge commit/tree agrees with read-back of the target reference; shared branch updates use available expected-HEAD protection rather than force-pushing over unread changes.

**Failure and recovery:** If target HEAD changes, reintegrate and reassess rather than retrying an overwrite. If a merge call times out, first inspect target-reference, commit and PR facts before deciding whether to retry; retain unknown until an authoritative result exists.

**Positive example:** main receives a new commit after PR review, so the merge tree is recomputed and affected gates rerun.

**Direct failure example:** Merging current content solely because the same branch name was green last week.

**Valid adjacent case:** A local documentation project uses actual candidate trees and local integration commits without being forced to create hosted CI.

**Checking entry point:** Finite models check expected HEAD and exact check bindings; actual platform capabilities, permissions and final references require separate verification.

## PGC-06 Merge failure, withdrawal and repair

**Inputs and prerequisites:** Actual merge results, affected consumers, erroneous versions and recovery goals.

**Procedure:** Distinguish unmerged, merged, conflict and unknown; preserve original changes in shared history through new revert/repair commits, following PGB for merge-revert mainline selection. Record code rollback, data recovery, artifact withdrawal and adoption withdrawal separately; one revert cannot encompass all external effects.

**Outputs and acceptance:** Recovery objects, necessary data/configuration and consumers meet predetermined criteria; original failures and the repair chain can be located.

**Failure and recovery:** On revert conflict, save the current state, resolve or abort, and then plan a new forward repair; irreversible data changes follow PGU recovery points or forward migration rather than blindly reverting to an old program.

**Positive example:** A new revert commit is added to a shared branch, the original commit remains in the graph, and interfaces are rechecked after recovery.

**Direct failure example:** Using reset and force-push to delete shared changes and lose others' commits.

**Valid adjacent case:** An unshared temporary branch may have its history organized under project policy after protecting uncommitted content, without claiming to change established remote facts.

**Checking entry point:** Local synthetic Git scenarios actually test revert and conflicts; real data/publication recovery uses target contracts.
