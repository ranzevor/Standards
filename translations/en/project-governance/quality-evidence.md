# Testing, quality gates and evidence

**Source version:** 0.1.0　**Status:** adopted　**Effective date:** 2026-10-30

**Document ID:** STD-PG-011　**Language:** en　**Authority:** Chinese (zh-Hans) only

This is the full, non-authoritative translation of the [Chinese source](../../../standards/project-governance/011-测试质量门禁与证据规范--v0.1.0.md). In a conflict, consult the Chinese source. MUST/MUST NOT bind only when the applicability condition holds and the exact version is selected for adoption.

## Scope, terms and layers

Applies to every “verified” claim and its tools; it does not require every project to run cloud services, hardware or real payments. A contract specifies initial state, inputs, independent expectations, observations and terminal state; raw records are actual outputs and execution facts; a summary is a derived explanation of raw records. Document structure, substantive semantic review, finite models, isolated implementation and real targets are assessed separately. Developers run checks, acceptance assessors verify criteria, independent reviewers assess adequacy, and evidence custodians control retention and access. Depends on [PGT](requirements-traceability.md) and [PGC](change-review-merge.md).

## PGQ-01 Define executable contracts first

**Inputs and prerequisites:** Exact requirements, target behaviors, candidates/environments and permitted side effects.

**Procedure:** State the initial state, input fixtures, commands or tool steps, clock/randomness, expected outputs/states/side-effect counts, observation points and failure terminal states. Comparison rules include units, ordering, tolerances and their independent basis; fault injection identifies its boundary before or after commit.

**Outputs and acceptance:** Another executor can judge pass/fail/unknown from the contract; command exit 0 is not a sufficient criterion for arbitrary business goals.

**Failure and recovery:** If expectations are undefined, repair the contract first; if dependencies/equipment are missing, record blocked or not-run and the missing conditions without generating an execution event.

**Positive example:** After a crash following an output write, either the old file or a complete new file is allowed, a truncated file is not, and the original-input digest MUST remain unchanged.

**Direct failure example:** Copying actual results into expected after execution and then claiming the test conforms to the specification.

**Valid adjacent case:** Scientific measurement without a single exact value may use intervals and statistical methods with a predefined basis, without forced false determinism.

**Checking entry point:** Automated contract models evaluate only the finite comparison types implemented; expert expectations and tolerance sources require manual checks.

## PGQ-02 Positive, negative and valid adjacent cases, and mutation

**Inputs and prerequisites:** Necessary rules, invariants, permitted variations and failure mechanisms.

**Procedure:** Important rules have at least a normal input, an input directly violating the rule and an adjacent but valid input. State-related cases cover duplication, reordering, concurrency, timeout, unknown outcomes and recovery; mutations should actually change the target implementation or data semantics, and failure must be confirmed at the target criterion. An import error, syntax error or earlier whole-document hash rejection does not stand in for killing a semantic mutation.

**Outputs and acceptance:** The target mechanism rejects negative cases or exhibits the prescribed failure, while valid adjacent cases remain accepted; count methods, parameterized scenarios, actual targets and skips separately rather than adding them together as coverage adequacy.

**Failure and recovery:** If a mutation misses the target, correct its injection point; if a valid adjacent case is wrongly rejected, repair the rule rather than prohibiting the valid path to manufacture green results.

**Positive example:** Removing the revision comparison lets a stale concurrent write overwrite a new value, and an assertion precisely catches that overwrite; conflict-free updates remain valid.

**Direct failure example:** Deleting a module causes ImportError, which is then claimed to test the idempotency defense.

**Valid adjacent case:** A comment change without behavioral impact should keep tests passing; not every file change must be rejected.

**Checking entry point:** Direct tests of the corresponding implementation/parser; substantive review assesses natural-language “important rules” and combination adequacy.

## PGQ-03 Exact objects and actual environments

**Inputs and prerequisites:** Complete source/artifact/configuration identities, tool versions, dependencies and actual execution environments.

**Procedure:** Before execution, fix actual candidate identity and environment: Git repositories use the worktree's tree including uncommitted changes under test and the baseline commit; offline release packages use verified build-manifest identity. Afterward, recheck that the same source object has not drifted. Save actual argv, cwd, necessary non-secret configuration, versions and targets; dynamically detected dependency results cannot be claimed as pinned versions. Modifying tested content during execution means that run cannot prove the final object.

**Outputs and acceptance:** Results locate exact objects and environments; different targets or changed source trigger impact assessment and rechecking.

**Failure and recovery:** On drift, truncation, dependency changes or concurrent writes, retain execution results and mark invalid-for-final-object; rerun after fixing isolation or object control, rather than merely updating digests.

**Positive example:** The actual candidate tree containing the specification and checker source agrees before and after regression, and execution results bind to that tree; the candidate may include uncommitted changes.

**Direct failure example:** Testing the old program but manually changing the log's version to the new version.

**Valid adjacent case:** Logs saved outside the source directory do not affect tested-source identity.

**Checking entry point:** Content identity, environment matching and before/after snapshot digests can be checked automatically; file digests prove neither the authenticity of execution nor semantic adequacy.

## PGQ-04 Result states and defenses against false passes

**Inputs and prerequisites:** Contracts, actual execution events, exit codes, observations and reasons for non-execution.

**Procedure:** States are not-run/pass/fail/partial/unknown/not-applicable. not-run means no actual execution; unknown means initiation occurred but effects remain unverified; not-applicable requires absence of the trigger condition. pass requires actual observations satisfying the contract, exits/exceptions matching predefined rules and consistent object/environment identity; important unexecuted steps cannot be aggregated into an overall pass.

**Outputs and acceptance:** Distinguish skips, infrastructure failures, expected business rejections and test failures; automated aggregation MUST check all required subitems, not only the final output line.

**Failure and recovery:** On subprocess timeout, preserve captured output and unknown effects; verify authoritative state before recovery. An intentionally tested nonzero exit may satisfy the contract, but failure of the test process itself is not automatically the expected target failure.

**Positive example:** A command should reject invalid input with exit 2 and leave files unchanged; both observations hold, so that negative-case test passes.

**Direct failure example:** The browser never starts and ten targets are skipped, but the total method count is reported as all browser targets passing.

**Valid adjacent case:** Documentation can be reviewed while real business implementation remains not-run; the two states can be reported separately.

**Checking entry point:** The `evaluate_check` and `aggregate_checks` finite models check explicit contracts and required sets; substantive review assesses actual target capabilities and applicability.

## PGQ-05 Raw evidence and derived summaries

**Inputs and prerequisites:** Actual-run stdout/stderr, start/end/exit records, observations and object identities.

**Procedure:** Save both raw output streams and machine results as actually obtained in a separate run directory, CI artifacts or an authorized evidence store, marking uncaptured or truncated content. Derived summaries reference necessary originals' paths, sizes, SHA256 and corresponding layers; source identity references the relevant Git tree or release manifest. Multilayer indexes also verify current identities of referenced inner layers. The existence of an outer file does not prove its inner digests remain valid. Handle sensitive values according to retention boundaries first and make the relationship between redacted versions and originals explicit.

**Outputs and acceptance:** Summaries trace back to raw results; failure, repair and reruns do not overwrite each other. Irreplaceable evidence is retained under PGX; redundant full-repository copies are not necessary evidence.

**Failure and recovery:** If originals are lost or unreadable, downgrade the corresponding conclusion to missing evidence rather than reconstructing logs; correct stale current indexes while retaining the original error record.

**Positive example:** A supplemental verification report links the original failure and the exact new run after repair, with their digests pinned separately.

**Direct failure example:** Updating an outer “verified” marker without rechecking changed inner artifacts.

**Valid adjacent case:** A rebuildable temporary build directory is reclaimed while irreplaceable raw execution logs and source/pinned entry points remain obtainable.

**Checking entry point:** Recursive references, digests, paths, duplicates and truncation markers are checked automatically; execution authenticity and evidence completeness require manual checking.

## PGQ-06 Gates, reuse and the tools themselves

**Inputs and prerequisites:** The current candidate, required check set, previous results and change-impact analysis.

**Procedure:** Gates run necessary automated checks and manual reviews against exact integration objects; old evidence may be reused only when the object, environment and proven proposition remain consistent, with differences and reasons listed. Checkers themselves have direct negative and valid adjacent cases; when assert validates external input, reject Python optimization mode or replace it with explicit validation that optimization cannot remove.

**Outputs and acceptance:** Automatically checkable claims all have runnable implementations; manual items state judgment methods and actual records rather than allowing generators to autofill semantic pass.

**Failure and recovery:** For a false gate pass, save a direct reproduction, repair tools/criteria and related documentation, then recheck affected and complete objects; do not close the issue by lowering thresholds, silently skipping or changing counting methods.

**Positive example:** If only translation navigation changes, original algorithm experiments may be reused after independent identity/impact verification, while current links and source/translation identities are rechecked.

**Direct failure example:** Using an old green badge as full acceptance of a new file set.

**Valid adjacent case:** Unchanged, expensive real-business experiments need not be repeated without reason, but this does not make untested new targets passed.

**Checking entry point:** `python checks/validate_all.py` runs repository validation, and `python -m unittest discover -s tests -v` runs regression tests; projects use their own contracts and environments, and automated-check capabilities cannot be extrapolated.
