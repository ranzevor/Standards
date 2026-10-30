# Files, caches, build artifacts and evidence lifecycle

**Source version:** 0.1.0　**Status:** adopted　**Effective date:** 2026-10-30

**Document ID:** STD-PG-019　**Language:** en　**Authority:** Chinese (zh-Hans) only

This is the full, non-authoritative translation of the [Chinese source](../../../standards/project-governance/019-文件缓存构建物与证据生命周期规范--v0.1.0.md). In a conflict, consult the Chinese source. MUST/MUST NOT bind only when the applicability condition holds and the exact version is selected for adoption.

## Applicability and terms

Applies to source, formal documentation/deliverables, data, dependencies, caches, build artifacts and execution evidence. Rebuildable means necessary inputs, tools and acquisition methods are actually available and results satisfy explicit equivalence criteria, not merely “theoretically repeatable.” Irreplaceable evidence consists of original inputs, failures, decisions or external observations whose historical facts cannot be recreated by rerunning. Custodians manage identity/retention, current users declare active references, and reclaimers verify usage and conditions. Depends on [PGR](repository-content.md), [PGQ](quality-evidence.md) and [PGA](deprecation-retirement.md).

## PGX-01 Classification and retention conditions

**Inputs and prerequisites:** File sets, purposes, authoritative sources, references, rebuild methods and retention restrictions.

**Procedure:** Set retention rules by directory and material type for source/formal-document/formal-delivery/irreplaceable-evidence/reproducible-build/dependency/cache/temporary. Record individual objects and active references where retention, reclamation or an exception actually requires them. Necessary source, formal deliverables and irreplaceable evidence have retention responsibilities and acquisition entry points; rebuildable items specify tools, pins, sources and equivalence criteria. Register sensitive-content retention conditions together with permitted access; retention does not expand sharing.

**Outputs and acceptance:** Every reclamation candidate has a fact-based classification; sole source or historical failures do not become disposable because the directory is named cache.

**Failure and recovery:** If classification, rights or references are unknown, retain undetermined without automatic deletion; first locate sources, consumers and retention bases.

**Positive example:** An npm download cache can be reacquired; lockfiles and original failure logs are not caches.

**Direct failure example:** Moving the only original design document into a temporary directory and then cleaning it as garbage.

**Valid adjacent case:** Generated output of rebuildable API documentation may be reclaimed while hand-written source and the pinned generator remain retained.

**Checking entry point:** `reclaim_plan` checks reclamation candidates' categories, rebuild entry points, retention conditions and active references; actual rebuildability and irreplaceability require substantive review.

## PGX-02 One current candidate and a minimal evidence index

**Inputs and prerequisites:** Current source, immutable historical inputs, verification results and review identity needs.

**Procedure:** Maintain one mutable current candidate. Git repositories fix it with the actual worktree's tree, while commits and diffs preserve version relationships and file differences; release packages use integrity manifests generated during builds. Store minimal necessary raw results and evidence indexes in a separate run directory or evidence store, bound to the corresponding source identity. Where historical objects already have immutable exact inputs, reference them and verify identity; new copies require specific isolation/recovery necessity, size and retention conditions.

**Outputs and acceptance:** Readers obtain current content from one entry point; the evidence index suffices to locate raw facts without multiple mutually drifting “final versions.”

**Failure and recovery:** On discovering duplicate snapshots, first inspect references, identity and necessity and form a recoverable deduplication plan; do not directly delete original failures or inputs still used in review.

**Positive example:** Review fixes the actual candidate tree and prohibits simultaneous writes, then checks before/after identities; raw results reference that tree, and Git supplies source history.

**Direct failure example:** Copying all source and node_modules after every test merely to display quantity.

**Valid adjacent case:** Where parallel mutable-test isolation is genuinely needed, a minimal necessary temporary worktree may be created and later reclaimed according to reference/retention conditions.

**Checking entry point:** Candidate entry points, references and usage inventories can be checked; actual execution and recovery needs determine copy necessity.

## PGX-03 Usage, active references and space budgets

**Inputs and prerequisites:** Actual filesystem free space, proposed write bytes/peak usage, active process/review references and the shared minimum reserve.

**Procedure:** Before writing/building, measure actual free space and target usage and assess the minimum reserve against worst-case increments and necessary temporary peaks; MUST NOT assume savings from compression, COW or hard links. Before reclamation, check direct and transitive references; dynamic references use revisions, leases or corresponding coordination, rather than deleting currently used objects based solely on an older scan.

**Outputs and acceptance:** Operations stay within the explicit free-space floor; logical directory size, actual allocated space and shared remaining space are not conflated. Insufficient reserve blocks only dependent writes, not grounds for deleting evidence to hide the gap.

**Failure and recovery:** On insufficient space, report exact bytes, projected increments and the minimum shortfall, prioritizing verified rebuildable idle items for reclamation; recheck unknown references or concurrent changes.

**Positive example:** Before a build, count source outputs, temporary directories and log peaks together, then assess available reserve.

**Direct failure example:** Using the previous round's df reading to guarantee that a large copy this time cannot exhaust shared disk.

**Valid adjacent case:** Read-only checking of a few small files need not reserve space for a full-repository copy, but new logs still count.

**Checking entry point:** `capacity_allowed` and reference-closure finite models; local tools observe the actual filesystem and active references.

## PGX-04 Reclaim rebuildable items

**Inputs and prerequisites:** Exact path sets, classifications, proof of no active references, rebuild entry points, absence of retention holds and expected reclaimed space.

**Procedure:** List a plan first and recheck path boundaries and reference revisions; reclaim only policy-eligible temporary/cache/dependency/build artifacts. Retain necessary lockfiles, source, formal deliveries and irreplaceable failures; measure actual reclaimed space afterward. Tools default to dry-run; real deletion uses the project's permitted reclamation execution interface.

**Outputs and acceptance:** Reclaimed objects are all rebuildable and unreferenced, without misclassifying “original materials” by file suffix alone. Cleanup results accurately list successes, failures and unprocessed items.

**Failure and recovery:** On permission errors or usage changes, retain unprocessed states and recheck scope without expanding wildcards. For mistaken reclamation, rebuild from verified sources and check identity; historical failure facts cannot be recreated.

**Positive example:** Completed synthetic local Git temporary repositories are reclaimed after original commands and state evidence have been saved.

**Direct failure example:** Deleting the sole fixed input still being read by a reviewer to lower disk usage.

**Valid adjacent case:** An unused download cache can be reacquired from actual pins and sources; policy-compliant copies need not be retained forever.

**Checking entry point:** `reclaim_plan` only produces candidates and rejection reasons; validation does not automatically delete real files.

## PGX-05 Deduplication, reference rewriting and rebuild verification

**Inputs and prerequisites:** Suspected duplicate objects, full-byte identities, current references and retention semantics.

**Procedure:** Confirm identical content through byte/digest comparison, then confirm that permissions, temporal semantics, retention and purposes can be merged; select an authoritative object, rewrite references and verify. Immutable historical events retain separate event identities even when output bytes match; content-addressed storage may share bytes without merging events.

**Outputs and acceptance:** All necessary references resolve after deduplication and rights/historical semantics remain intact; matching digests do not prove that different events can be merged directly.

**Failure and recovery:** If references were missed or retention conditions differ, do not delete, or restore original references; if rebuilt results differ, retain the original valid object and repair the generation method.

**Positive example:** Multiple pinned references share the same rebuildable dependency blob, while reference records remain separate.

**Direct failure example:** Deleting one execution event and its time/object record because two failure logs have identical bytes.

**Valid adjacent case:** Deduplicate only raw-byte storage, retaining both sets of event metadata and access boundaries.

**Checking entry point:** Byte identity, reference closure and event-ID uniqueness are checked automatically; mergeability of retention/permissions requires manual checking.

## PGX-06 Evidence retention, invalidation and correction

**Inputs and prerequisites:** Original inputs/failures/decisions, retention permissions, current references and sensitivity levels.

**Procedure:** Preserve originals within the scope actually obtained in a separate run directory or authorized evidence store, with fixed digests and sizes. Evidence indexes reference originals and Git objects or release identities; corrections retain original errors and replacement relationships. Evidence proves only its actual object, proposition and environment; after invalidation, retain history rather than falsifying it as never having occurred. Minimize retention/access; necessary redacted versions preserve their relationship to originals and identify scope that cannot be reproduced.

**Outputs and acceptance:** Original failures and repaired results can be verified separately; duplicate snapshots do not increase credibility.

**Failure and recovery:** If evidence is lost or damaged, record the gap, limit conclusions and inspect recoverable sources; MUST NOT generate a replacement log that appears to be original.

**Positive example:** A current report corrects an outdated digest while the old report and its actual object remain locatable.

**Direct failure example:** Deleting an original failure and changing the successful rerun's time to that of the first execution.

**Valid adjacent case:** Handle originals under expired, lawful sensitive-data retention rules, keeping permitted minimal audit records rather than retaining indefinitely.

**Checking entry point:** Verify recursive evidence identities and invalidation states; authenticity, retention rights and sensitive-data deletion conditions require substantive review.
