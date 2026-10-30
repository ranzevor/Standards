# Git Branch Synchronization and Conflict Handling Standard

**Document ID:** STD-PG-008  
**Source version:** 0.1.0　**Status:** adopted　**Effective date:** 2026-10-30
Chinese is authoritative: [Chinese text](../../../standards/project-governance/008-Git分支同步与冲突处理规范--v0.1.0.md). The clause IDs are identical. MUST/MUST NOT are necessary requirements; SHOULD permits a reasoned equivalent safeguard; MAY is optional. Git capability, branch names and passing tests do not authorize real remote writes, publication or rewriting shared history.

## PGB-01 Scope, roles, terms and branch names

**Inputs and scope.** This standard covers synchronization, integration, conflict recovery, pushing and history preservation between Git branches and verified repositories. It does not mandate GitFlow, a particular main-branch name or hosting provider. Operators MUST obtain source/destination repositories, complete branch refs, exact baselines, allowed writes, integration strategy, sharing status and responsibility. Automated examples cover only complete local synthetic repositories. Hosted permissions/protection/queues, signature trust and real LFS services require separate checks.

**Roles and terms.** Contribution branches hold bounded changes; integration branches accept reviewed work; maintenance branches are needed only for genuine multi-version support. Branch refs move. Remote-tracking branches are local observations from fetching, not live remote locks. Upstream is a configured relationship, not an inference from similar names. Fast-forward means the current tip is an ancestor of the target. Divergence means both sides have unique commits. Shared history includes any commits consumed by others, not only a main branch.

**Actions and artifacts.** Projects SHOULD select meaningful topics such as `feature/parser` or `fix/cache-key`; maintenance naming follows the support policy. MUST check syntax with `git check-ref-format --branch feature/parser`, then manually check meaning, occupancy and ownership. Syntactic validity is not semantic appropriateness; a solo single-branch project is legitimate. Reviewers decide content, integrators apply the selected strategy and deliver the exact graph, and maintainers protect shared history and recovery. Combining roles does not turn self-review into independent review.

**Failure and acceptance.** Unknown targets, rights or sharing remain pending; do not assume private rewritability. `worktree` covers branch occupancy and legal neighbors; real roles and rights are manual checks. Dependencies are the [workspace standard](git-workspace.md), [domain framework](../../../standards/project-governance/001-项目治理领域总则与职责接口--v0.1.0.md), [quality/evidence standard](../../../standards/project-governance/011-测试质量门禁与证据规范--v0.1.0.md) and [adoption/exception standard](../../../standards/project-governance/020-规范采用例外与升级规范--v0.1.0.md). Independent adoption requires equivalent responsibility and evidence interfaces, with the exact version and applicable scope recorded. Sources: GIT-REFNAME, GIT-BRANCH.

## PGB-02 Preserve a recoverable pre-integration state

**Preconditions and steps.** Operators MUST check current branch, HEAD, index, working tree and other worktrees, protecting unfinished changes under PGW-06/07. Preserve the exact old tip and comparison target, rather than relying only on ORIG_HEAD, which later commands may change.

```sh
git status --porcelain=v1 -uall
git branch --show-current
git rev-parse HEAD
git worktree list --porcelain
git log --graph --oneline --decorate --all
git branch backup/parser-before-integration <original-tip>
```

**Outputs and failures.** Record old/target tips, baseline, cleanliness, save point and selected strategy. A backup branch must be local, unused by another name owner, and within allowed scope. Do not stack operations on another writer's changes, unresolved merge/rebase or unidentified objects. A branch backup preserves commits, not uncommitted working content. On failure inspect actual state before the relevant abort or save-point recovery; hard reset is not a universal remedy.

**Acceptance.** `merge_conflict` and `rebase_conflict` check clean pre-state and abort recovery; the latter retains a reachable old-tip reference. Preservation sufficiency and concurrency coordination are human checks. Trial integration in a new worktree is legal; claiming a backup branch saves an uncommitted draft is not. Sources: GIT-MERGE, GIT-REBASE, GIT-WORKTREE, GIT-BRANCH.

## PGB-03 Fetch the selected objects and refs

**Inputs and action.** Identify source and refspec rather than infer them from unknown configuration. An ordinary fetch of main into its remote-tracking ref is:

```sh
git fetch --no-tags --no-recurse-submodules origin refs/heads/main:refs/remotes/origin/main
git rev-parse refs/remotes/origin/main
git rev-list --left-right --count HEAD...refs/remotes/origin/main
git log --graph --oneline HEAD refs/remotes/origin/main
```

**Result.** This specific command obtains objects and updates the selected tracking ref and FETCH_HEAD without integrating remote content into the current working tree. Do not generalize that every possible fetch refspec leaves all local refs unchanged. `--no-tags` does not assert the project has no tags. Do not expand scope to all remotes, pruning or recursive submodules without a decision. MUST compare current HEAD, index and files before/after: fetched is not integrated.

**Failure and recovery.** Failed fetching may still leave objects or state changes. Record the result and check whether the required ref was obtained. Unknown identity, insufficient permission or interruption requires diagnosis instead of blind repetition. Establish unknown effects first. Retrieved commits still need content and strategy review before integration.

**Acceptance.** `fetch_ff` fetches while a tracked file has staged and later unstaged edits, asserts all three layers unchanged and the tracking tip updated. Fetch-only with local work retained is a legal neighbor; calling fetch success integrated work is not. Real transport and refspec scope are manual checks. Source: GIT-FETCH.

## PGB-04 Explicitly select fast-forward, merge or rebase

**Decision inputs.** Verify both tips, ancestry, sharing, history policy and save points. The integrator MUST select a strategy before writes and state its expected graph:

| Choice | Command | Expected graph change | Important distinction |
| --- | --- | --- | --- |
| Fast-forward only | `git merge --ff-only <target-tip>` | Move to target when possible without a merge commit; reject divergence | Divergence refusal is not a content conflict |
| Preserve both histories | `git merge --no-ff --no-commit <target-tip>`, then reviewed commit/continue | A nontrivial merge retains both parent chains in a new merge commit | `--no-commit` alone cannot stop a fast-forward |
| Replay unshared topic commits | `git rebase <target-tip>` | Usually create new commit identities and move the topic tip | Similar content is not unchanged identity |

If already integrated with no new changes, do not manufacture a commit. Shared history normally uses merge or additive fixes, not unapproved rebase for visual linearity. Other strategies require explicit state and acceptance rules; configuration defaults must not silently decide.

**Failure and recovery.** Missing ancestry, unavailable objects or incomplete shallow history require a recorded reason, not automatic unrelated-history permission. After divergence refusal, review the graph and choose merge/rebase only within existing authority. Establish unknown effects before retrying.

**Acceptance.** `fetch_ff` checks forward progress and refusal; `merge_conflict` checks two parents; `rebase_conflict` checks new identity and parent. Humans determine suitability. Replaying a private topic is legal. The `pull-merge-instead-of-ff` mutation really merges a divergent graph and fails the unchanged-state assertion, demonstrating that changing strategy is not equivalent recovery. Sources: GIT-MERGE, GIT-REBASE, GIT-PULL.

## PGB-05 Pull fetches and integrates

**Preconditions and action.** Use pull only with known source, branch and strategy and protected unfinished work. MUST specify a strategy rather than rely on global configuration:

```sh
git pull --ff-only --no-recurse-submodules origin main
```

An explicit project decision may instead use pull with `--no-rebase` or `--rebase`, with other required options specified. If the fetched exact tip must be reviewed before integration, split fetch from merge/rebase. Pull is not a read-only refresh.

**State, failure and recovery.** Pull fetches before attempting integration. On ff-only divergence refusal, current branch/index/working tree should retain pre-state while tracking refs or FETCH_HEAD may already have changed. Check both phases rather than report “nothing changed.” Resolve integration conflicts through PGB-06/07; do not automatically switch strategies and retry. After recovery, reread the graph instead of retaining old ahead/behind counts.

**Acceptance.** `fetch_ff` tests fast-forwarded content, divergence refusal, retained local state and updated tracking ref after failed integration. Real remote identity/rights are manual. Already-synchronized or fast-forwardable ff-only success is legal; treating fetch success as whole-pull success is not. Sources: GIT-PULL, GIT-FETCH.

## PGB-06 Merge conflicts and abort

**Steps.** Start the selected merge from a protected clean state. On conflict, MUST read status, `git ls-files -u` and conflict files. For ordinary two-branch text conflicts inspect the three index stages:

```sh
git show :1:path/to/file
git show :2:path/to/file
git show :3:path/to/file
# Edit the final content to meet both sides' requirements, then:
git add -- path/to/file
git diff --cached
git ls-files -u
git merge --continue
```

Stage 1 is the base, 2 the current side, and 3 the incoming side. Add/delete conflicts may lack a stage; absence is not automatically corruption. MUST explain resolution choices, check for no unmerged entries or leftover markers, and run affected tests before completing the commit. Blind ours/theirs selection or deleting markers alone does not establish correctness.

**State and recovery.** During an unresolved merge HEAD stays at the old tip, the index contains conflict stages, working files may have markers, and MERGE_HEAD identifies the other parent. To abandon this integration, use `git merge --abort`, then check HEAD, index, files and cleared merge state. Starting dirty can prevent full reconstruction of previous edits, hence prior preservation is required. Do not blindly abort when no merge exists.

**Acceptance.** `merge_conflict` compares all three actual stage contents, HEAD and MERGE_HEAD, verifies return to the clean pre-state on abort, then retries and checks final content and both exact parents. The `merge-ours-only` mutation commits only current-side content; its successful commit still fails final-content verification. Humans check business correctness and nonordinary conflicts. Independent-file merging is a legal conflict-free neighbor; a successful commit exit does not prove another side's functionality survived. Source: GIT-MERGE.

## PGB-07 Rebase conflicts, continue and abort

**Applicability.** Topic commits are confirmed rewritable, the old tip has a saved ref and the working tree is clean. After `git rebase <target-tip>`, conflicts require per-commit inspection of the current patch, unmerged stages and content. During rebase, ours normally denotes the new base/replayed result and theirs the topic commit being replayed; do not mechanically interpret ours as the original topic branch.

```sh
git rebase --show-current-patch
git ls-files -u
# After resolving the current conflict:
git add -- path/to/file
git rebase --continue
# To restore the branch state before this rebase:
git rebase --abort
```

**Results and failure.** Continue can encounter another conflicting commit; repeat checks to completion. Skip discards the current replayed patch: it is not generic conflict resolution and requires an explicit decision and impact record. Quit does not restore the original HEAD like abort. After completion, MUST compare old/new ranges, final content, parent chain, pending edits and tests. Equivalent content does not automatically extend an old exact-OID review.

**Recovery.** After abort, check original branch/tip, index and working tree. If abort fails, retain operation administration and files, then recover using recorded refs and individual state checks. Deleting the rebase directory is not proof of completion. Unknown sharing cannot be decided retrospectively after rewriting.

**Acceptance.** `rebase_conflict` tests temporary HEAD, new-base/topic stage contents, abort branch and three-layer restoration, new identity after continue and reachable old tip. The `skip-conflicting-commit` mutation actually skips the patch and fails final-content verification. Empty commits, merge replay, renames and business equivalence require manual checks. Sources: GIT-REBASE, GIT-RESTORE.

## PGB-08 Push scope and shared-history protection

**Preconditions and steps.** MUST verify destination repository, target ref, reviewed local OID and permission. Restrict the push ref instead of defaulting to all branches/tags:

```sh
git push origin <reviewed-commit>:refs/heads/feature/parser
```

Read back the destination ref after success. Exit 0 does not imply all external checks passed. On non-fast-forward rejection, fetch, inspect other writers' changes and integrate rather than automatically force. Dry-run previews current conditions; it reserves no remote state.

**Exception mechanism.** An authorized private-topic rewrite requires impact, affected consumers and recovery OIDs. If using a lease, pin the exact expected value: `git push --force-with-lease=refs/heads/feature/parser:<expected-old-oid> origin <new-oid>:refs/heads/feature/parser`. Unqualified leases can be affected by background fetching. Leases guard a ref concurrency condition, not permission or the validity of removed commits. Unknown sharing is not a private exception.

**Failure and recovery.** For unknown network outcomes, read the destination ref before repeating. Distinguish unchanged old value, expected new value and a third value written by someone else. Prefer additive repair/revert for shared mistakes; do not rewrite evidence to hide them. Diagnose real platform refusals rather than bypass protections.

**Acceptance.** `push_history` uses a local bare repository to check non-fast-forward refusal, stale exact-lease refusal and a normal push after integrating both writers. `force-overwrite-shared` really overwrites an isolated demonstration ref and is detected by its destination-tip assertion. A separate private demonstration ref exercises a matching explicit lease. Real protection, access and rewrite decisions remain manual. Source: GIT-PUSH.

## PGB-09 Revert, tags and failed-operation recovery

**Actions and outputs.** To undo a shared ordinary commit, SHOULD use `git revert --no-edit <bad-commit>` from clean state, reviewing new commit, parents, content and tests. This adds reversal history rather than deleting the old commit. Resolve conflicts then revert continue, or revert abort and inspect pre-state. Reverting a merge requires choosing/explaining mainline and future-merge consequences, not blindly applying the ordinary-commit example.

A candidate tag MUST bind an exact commit; check both tag object and peeled commit:

```sh
git tag -a v0.1.0 -m "Candidate version" <reviewed-commit>
git rev-parse refs/tags/v0.1.0
git rev-parse 'v0.1.0^{commit}'
git cat-file -t refs/tags/v0.1.0
```

**Boundary and recovery.** An annotated tag's OID differs from its target commit. A lightweight tag lacks that annotation object and is not evidence of a signature. A tag is an identifier, not release approval. After duplicate-name refusal, check the original tag remains unchanged; do not default to tag force for shared tags. A mistaken candidate can receive a new corrected tag plus correction record. Tag pushing, remote deletion and releases require their actual permissions. Unperformed signature/trust checks remain unverified.

**Acceptance.** `revert_tag` checks that the bad commit remains an ancestor, the new revert parent/content, conflict abort and empty-commit failure; it verifies annotation type, peeled target and unchanged duplicate tag. `reset-shared-instead-of-revert` and `move-existing-tag` perform a real hard reset and forced retag respectively, failing new-commit identity/tag-retention assertions. A new tag on a corrected commit is legal; relocating an old tag and claiming its old acceptance still applies is not. Sources: GIT-REVERT, GIT-TAG.

## PGB-10 Submodule and LFS applicability

**Submodule inputs and steps.** If gitlinks or `.gitmodules` exist, MUST inspect each repository, path, source, required commit and independent permission. Superproject permission does not expand automatically to every recursive source. For a verified authorized path:

```sh
git submodule status -- deps/library
git ls-files --stage -- deps/library
git submodule update --init --checkout -- deps/library
git -C deps/library rev-parse HEAD
```

The superproject records a mode-160000 commit pointer, not all subproject files. Checkout update can obtain missing objects and detach the submodule at the recorded commit. Remote update selects a remote-tracking target and is not equivalent to restoring a pinned dependency. Review and commit submodule changes inside that repository before explicitly staging the superproject gitlink. Preserve update failures, missing-object evidence and dirty submodule state separately; do not erase with force. Verified absence of submodules can be not applicable.

**LFS inputs and boundary.** If LFS attributes/pointers exist, MUST confirm extension version, actual object availability, storage/transfer conditions and permission. LFS is an additional extension; a Git commit or pointer does not prove large-file retrieval. An adopting project needs a version-pinned operating procedure and checks of `.gitattributes`, actual content/object integrity and restoration in another working tree. New tracking patterns do not automatically migrate history. History migration requires separate rewrite assessment, not a side action during pull recovery.

**Output and acceptance.** `submodule_pointer` exercises gitlinks, recorded-commit checkout/detached HEAD, a child commit leaving the parent's index unchanged, and explicit add updating the pointer. It does not contact or validate real recursive remotes. This suite does not install/run LFS; service transfer, quotas and recovery are untested and MUST NOT be reported passed. Human applicability review distinguishes a no-LFS legal neighbor from an LFS-using project with a missing extension: the latter has an unresolved dependency, not inapplicability. Sources: GIT-SUBMODULE, GIT-LFS, whose rolling official overview supports limited mechanism claims only.

## PGB-11 Acceptance entry points, states and handover

**Executable entry points:**

```sh
python examples/project-governance/git_scenarios.py --scenario fetch_ff
python examples/project-governance/git_scenarios.py --scenario merge_conflict
python examples/project-governance/git_scenarios.py --scenario rebase_conflict
python examples/project-governance/git_scenarios.py --scenario all
python -m unittest tests.test_project_git_scenarios -v
```

Each run creates fresh local synthetic repositories, isolates system/global configuration and disables hooks and non-file transport. Python 3.10 or later, its standard library and Git suffice; this edition was exercised with Python 3.12.14 and Git 2.52.0. Fixture isolation is not advice to change actual project security controls. Reports contain commands, exits, expected/actual values, assertions, graphs and content; evidence-parent selects an existing directory. Successful reports are saved before reclaiming temporary synthetic repositories; failed originals/logs remain. An expected refusal does not fail the whole scenario, while unexpected nonzero exits cannot be ignored.

**Required handover.** Old/new tips, destination ref, strategy, conflict decisions, unfinished-work save points, actual results/exits, affected tests, remaining items, source versions and accountable recipient. Operators supply evidence, reviewers check content/graph semantics, integrators verify the exact target state, and adopters decide effectiveness. Without actual remote results, report only local completion. Unknown interrupted-transfer outcomes remain unknown.

**Coverage matrix.** PGB-01/02 → worktree plus human roles/pre-state; 03/04/05 → fetch_ff; 06 → merge_conflict; 07 → rebase_conflict; 08 → push_history; 09 → revert_tag; 10 → submodule_pointer plus manual LFS; 11 → CLI reports/unit tests and manual handover. Mutations must change command semantics, not just labels, and legal neighbors must still pass. Automated results do not replace independent review or adoption.

**Sources.** The [claim/version table](../../../sources/project-governance/git-operations.json) identifies official versions, sections and supported scope. When a version entry redirects, use the actual document. LFS services and hosted-platform capabilities require separate acceptance in the project environment.
