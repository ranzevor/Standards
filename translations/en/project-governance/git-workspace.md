# Git Workspace and Local Operations Standard

**Document ID:** STD-PG-007  
**Source version:** 0.1.0　**Status:** adopted　**Effective date:** 2026-10-30
Chinese is authoritative: [Chinese text](../../../standards/project-governance/007-Git工作区与本地操作规范--v0.1.0.md). This full translation retains the clause IDs. MUST/MUST NOT indicate applicable necessary requirements; SHOULD permits a reasoned deviation with equivalent safeguards; MAY denotes an option. Software capability does not confer permission to operate a project.

## PGW-01 Scope, terms and responsibility interfaces

**Inputs and applicability.** This standard covers ordinary complete Git working trees: initialization, cloning, inspection, staging, committing, saving unfinished work and multiple worktrees. The operator MUST obtain the target path, repository identity, allowed files and operations, baseline commit, tool version and responsible person. For a new repository the baseline is “no commits yet”; do not invent a HEAD commit. Bare repositories have no ordinary working tree. A submodule is a separate repository, addressed by [PGB-10](git-integration.md#pgb-10-submodule-and-lfs-applicability). Sparse, shallow or partial clones, large binary filters, and filesystem case/symlink differences are outside the examples' complete acceptance coverage and MUST receive explicit applicability and supplemental checks.

**Terms.** The working tree contains current on-disk files; the index/staging area holds the candidate tree for the next ordinary commit. HEAD usually names a branch, directly names a commit when detached, and may refer to an unborn branch. A commit ID is not a branch name: branch names move. Untracked files are absent from the index; ignored files normally match rules for intentionally untracked paths. “Clean” means the agreed checks found no pending index, working-tree or untracked changes; it does not mean no secrets, vulnerabilities or failing tests.

**Actions, outputs and failures.** The operator MUST record the inputs. The reviewer checks per-path differences and intent; the integrator consumes the baseline and commit identity; the adopter decides applicability and exceptions. Missing authority, unclear identity, an operation in progress or unknown file provenance MUST NOT be resolved by guessing and continuing writes. Report “unknown/pending resolution” and the missing input; independent checks may continue. One person may hold several roles, but self-review is not independent review.

**Entry points and boundary.** PGW-02–09 commands and synthetic scenarios execute technical checks. Rights, adoption, real workspaces and responsibility handover require human review. Interfaces are the [domain framework](../../../standards/project-governance/001-项目治理领域总则与职责接口--v0.1.0.md), [quality and evidence standard](../../../standards/project-governance/011-测试质量门禁与证据规范--v0.1.0.md), and [adoption and exception standard](../../../standards/project-governance/020-规范采用例外与升级规范--v0.1.0.md). Projects MUST identify the applicable scope of these interfaces. Independent adoption requires equivalent interfaces described here, not a purchased platform.

**Neighbor and counterexample.** One change record can be sufficient for a solo offline repository. A writable directory does not authorize overwriting another person's files.

## PGW-02 Creation, cloning and initial identity

**Preconditions.** The operator MUST confirm an empty or absent destination, a verified source and an explicit initial branch. An unidentified directory is not disposable. `repo` and `local.git` below are controlled example paths; real targets require individual verification.

```sh
git --version
git init -b main repo
git -C repo symbolic-ref HEAD
git -C repo rev-parse --verify HEAD
git init --bare -b main local.git
git clone --no-local --no-recurse-submodules file:///absolute/local.git consumer
```

**State and output.** Initialization creates repository administration and an unborn branch. A nonzero result when verifying a HEAD commit at this point is expected, not an initialization failure. A bare repository has no working tree. Cloning an empty bare repository may also leave no commits. After cloning an existing history, the operator MUST check branch, HEAD, source and checked-out contents, not merely the existence of a directory. `--no-recurse-submodules` does not imply dependencies are available.

**Failure and recovery.** Preserve clone errors and partial destination state. Retrying MUST NOT overwrite pre-existing material. Only after confirming that a failed directory contains disposable output of this attempt may the operator retry in a new directory or apply the project's retention policy. Identify unknown existing repositories read-only.

**Acceptance.** `index_snapshot` tests the unborn branch; `fetch_ff` checks the cloned tip and content. Real sources, access, path collisions and extensions require human checks. An empty clone without commits is a legal neighbor; treating every failed HEAD verification as failed initialization is a counterexample. Sources: GIT-INIT, GIT-CLONE.

## PGW-03 Distinguish HEAD, index and working tree before writing

**Inputs.** Identify repository root, branch or detached HEAD, affected paths and known baseline. The operator MUST inspect index and working-tree differences separately, including untracked and unmerged paths:

```sh
git status --porcelain=v1 -uall
git diff -- path/to/file
git diff --cached -- path/to/file
git ls-files --stage -- path/to/file
git ls-files -u
git rev-parse HEAD
```

**Interpretation.** Outside conflicts, the first short-status column concerns the index and the second the working tree. `MM` indicates changes in both; `??` is untracked. Conflict statuses have different semantics: inspect unmerged index entries instead of applying the ordinary two-column interpretation. Plain diff compares working tree against index; cached diff compares index against HEAD and can show staged additions before the first commit. Scripts accepting arbitrary filenames MUST use and correctly parse NUL-delimited output, not split paths at spaces. Fixed synthetic names in this example do not validate a general filename parser.

**Output and recovery.** Produce the baseline, branch, three-layer differences and outstanding paths. Unknown changes or an active merge/rebase require attribution and operation-state checks before overwriting. If another writer changes files during inspection, resample and review: a snapshot is not a lock.

**Acceptance.** `index_snapshot` asserts unchanged HEAD, index content, `MM` and both diff forms. Humans review meaning and concurrent ownership. A staged fix plus an unstaged experiment in the same file is legitimate; treating empty plain diff as proof of no staged changes is not. Sources: GIT-STATUS, GIT-DIFF.

## PGW-04 Per-path staging and committing

**Preconditions.** Inspect the entire current index and exclude unrelated or other writers' staged changes. The editor's open buffer does not define commit scope. The operator MUST stage allowed paths, review staged differences, then commit:

```sh
git add -- path/to/file
git diff --cached --stat
git diff --cached
git commit -m "Fix parser handling of empty records"
git show --stat --oneline HEAD
git status --porcelain=v1 -uall
```

**State and output.** Add captures content at invocation; later editing does not update that staged copy. Ordinary commit without path arguments commits the whole index and updates HEAD; when HEAD is attached it also advances that branch, while a detached HEAD commit does not move any branch. The operator MUST verify the new parent, tree and remaining working-tree changes. `git add -p -- path/to/file` permits hunk selection, followed by staged-diff review. `commit -- path` and `commit -a` select content differently and are not substitutes for committing an already-reviewed index.

**Failure and recovery.** After a failed commit, check whether HEAD changed and whether the index and working files remain; do not simply replay the command. Refusing an empty commit may be the correct result, not a reason to manufacture one. With an existing HEAD, `git restore --staged -- path` can undo mistaken staging without discarding working edits. An unborn branch requires a separately checked procedure to remove index entries; do not apply the HEAD-based recipe blindly.

**Acceptance.** `index_snapshot` uses `base → staged → later-worktree`, checks that the commit contains only the reviewed staged version, unrelated file b remains uncommitted, and the later edit survives. The `commit-all` mutation actually substitutes `-am` and fails the content assertion. `revert_tag` checks that a refused empty commit preserves state. Atomicity, intent and description need human review. Sources: GIT-ADD, GIT-COMMIT, GIT-RESTORE.

## PGW-05 Ignore rules do not untrack files or protect secrets

**Inputs and actions.** Shared patterns belong in `.gitignore`; repository-local auxiliary exclusions may use `info/exclude`. The operator MUST first check whether a path is tracked, then inspect its actual matching rule:

```sh
git ls-files -- path/to/file
git check-ignore -v -- path/to/untracked-file
git status --porcelain=v1 --ignored -uall
```

Example patterns:

```gitignore
*.log
build/*
!build/keep.txt
```

**Results and failures.** Already-tracked `tracked.log` can still be changed and committed. Ordinary add does not stage matching untracked `ignored.log`. Ignoring neither cleans history nor retracts disclosed secrets. Operators MUST NOT use `add -f` merely to make a submission succeed. An intentional tracked exception requires content review and either a revised rule or an explicit reviewed exception. Parent-directory exclusions constrain negation patterns; test actual paths rather than infer behavior from spelling.

**Output and recovery.** Record matching source, affected paths and permitted exceptions. For mistaken tracking, first confirm content and ownership, then remove it from the index and commit within allowed scope. Sensitive content goes to the security response interface; adding an ignore rule does not establish containment.

**Acceptance.** `ignore_rules` tests tracked-file staging, ignored-file rejection and the legal `build/keep.txt` neighbor. `force-add-ignored` actually stages an excluded file and is detected by an index assertion. Confidentiality and exclusion appropriateness require human review. Sources: GIT-IGNORE, GIT-ADD.

## PGW-06 Protect uncommitted work

**Applicability.** Before switching branches, merging, rebasing, restoring paths or removing worktrees, the operator MUST inventory staged, unstaged, untracked and relevant ignored files and choose a verified preservation method for each. Git's usual overwrite refusal is not a complete backup.

**Steps and output.** Inspect under PGW-03. Self-contained reviewed changes may become local commits; unfinished ordinary text may use PGW-07; parallel work may use PGW-08. Verify saved content, staging boundaries and untracked coverage before `git switch feature/parser`. Default stash excludes untracked files and `-u` excludes ignored files; separately decide how the latter must be preserved.

**Failure and recovery.** If Git refuses the switch because it would overwrite local edits, the operator SHOULD verify unchanged HEAD, index and files rather than bypassing the refusal with force or `reset --hard`. Failed saving, insufficient capacity or unknown filter behavior means unfinished preservation: keep originals and resolve the missing condition. Clean, forced checkout and hard reset are not default recovery steps.

**Acceptance.** `dirty_switch` creates a colliding uncommitted edit, checks nonzero switch and unchanged three-layer state, then saves, switches, returns and restores content plus the untracked file. Ignored files, binaries and preservation media need human checks. A separate worktree preserving the dirty original is legal; deleting unsaved drafts to “synchronize” is not. Sources: GIT-STASH, GIT-WORKTREE, GIT-SWITCH. Preservation sufficiency is a project requirement, not Git certification.

## PGW-07 Stash saving, application conflicts and recovery

**Preconditions and steps.** The repository has a commit and no unresolved conflict. The operator MUST inspect existing entries and record the new stash object's ID; numeric positions can move when further entries are added.

```sh
git stash list
git stash push -u -m "Before parser integration"
git rev-parse refs/stash
git stash show -p -u 'stash@{0}'
git stash apply --index <saved-stash-oid>
```

**State and output.** Check working-tree, index and untracked state after saving. Apply retains the saved entry; `--index` attempts to restore staging. Verify both content and staging boundaries, not just that files appeared. Prefer keeping the saved entry while validating recovery rather than defaulting to pop.

**Conflict recovery.** Preserve the stash object, unmerged paths and conflict files. There is no dedicated stash `--abort`; do not blindly use merge abort. A new worktree based on the stash's first parent can recover the saved state without changing the original conflict:

```sh
git worktree add -b recovery/parser ../parser-recovery <saved-stash-oid>^1
git -C ../parser-recovery stash apply --index <saved-stash-oid>
```

After verifying original index, working content and untracked files, integrate the conflicted workspace deliberately and stage/commit per path. Before dropping a stash, resolve the current list entry to the recorded OID again, verify recovery and retention conditions, then use `git stash drop 'stash@{n}'` on that exact entry. MUST NOT clear unknown saved work. Successful stash branch may automatically drop its selected list entry; it is not a retention-preserving equivalent.

**Acceptance.** `stash_conflict` produces a real conflict, checks the saved OID remains readable, and restores different index and working-tree contents plus an untracked file in another worktree. `dirty_switch` supplies the conflict-free neighbor; `drop-save-before-verify` actually removes the save reference and fails its retention assertion. Business choices, ignored files and deletion authority need human review. Sources: GIT-STASH, GIT-WORKTREE.

## PGW-08 Worktree parallelism and removal

**Preconditions and actions.** The operator MUST inspect `git worktree list --porcelain` and branch/path occupancy. Create a separate branch or an intentional detached inspection/experiment:

```sh
git worktree add -b feature/parser-check ../parser-check HEAD
git worktree add --detach ../inspect-candidate <commit-oid>
git -C ../parser-check status --porcelain=v1 -uall
```

**State and output.** Worktrees have separate HEADs and indexes but share the object database and most refs. They are neither independent clones nor locks on shared branch writes. Refusing to check out a branch already occupied elsewhere is protection; select a new branch or intentional detached state rather than routinely force it.

**Removal and recovery.** Save necessary work; verify cleanliness, reachable commits and retention conditions before `git worktree remove ../parser-check`. Removal does not delete the corresponding branch. Do not force past dirty-removal refusal. After lost paths or manual moves, locate and verify real content before running `git worktree repair ../moved-parser-check` from the main worktree for a verified moved path. Preview stale entries with `git worktree prune --dry-run --verbose`; actual pruning follows retention checks and confirmation that offline save points are not affected. Prune removes stale administrative entries, not restores files; an offline mount is not stale merely because it is absent now.

**Acceptance.** `worktree` tests duplicate-branch refusal, separate indexes, dirty-removal refusal, branch retention after clean removal, and the detached legal neighbor. `force-duplicate-worktree` bypasses occupancy protection and fails the path-state assertion. Offline mounts, repair/prune and moving worktrees containing submodules are not automated here. Shared-ref concurrency, mounts and removal authority need human checks. Source: GIT-WORKTREE.

## PGW-09 Path restoration and failure classification

**Actions.** Before restoring, the operator MUST identify source and destination layer and preserve overwritten material. With an existing HEAD:

```sh
git restore --staged -- path/to/file
git restore --source=<known-commit> --worktree -- path/to/file
git status --porcelain=v1 -uall
git diff -- path/to/file
git diff --cached -- path/to/file
```

**State and output.** The first command restores the index from HEAD, preserving working edits. The second changes working content to the selected source without moving HEAD; it can overwrite edits and remove a tracked path absent from that source. Verify results; it is not read-only undo. Undoing shared commits belongs to the new revert commit in PGB-09, not history rewriting here.

**Failure, unknown and recovery.** For nonzero exits, inspect state and distinguish protective refusal, content conflict and tool/storage failure. After a timeout or disconnection leaves an unknown result, establish side effects before retrying. Do not delete lock files as a universal repair. Restore preserved material by its exact OID/path. Without a save point, state the uncertain recoverability; reflog is not a guarantee for edits never stored in Git.

**Acceptance.** `index_snapshot` verifies unstaging without content loss. `restore-worktree-instead-of-index` makes a further edit after staging; the wrong working-tree restore really loses that edit and fails the content assertion; `revert_tag` verifies refused commits and revert abort. Specified-source overwrites, absent-path removal and actual fault recovery require separate human applicability checks and are not inferred from those automated results. Restoring a reviewed old file after saving current edits is legal; promising recovery after unsaved overwrite is not. Sources: GIT-RESTORE, GIT-REVERT.

## PGW-10 Executable acceptance and evidence contract

**Entry points from the repository root:**

```sh
python examples/project-governance/git_scenarios.py --scenario index_snapshot
python examples/project-governance/git_scenarios.py --scenario all
python -m unittest tests.test_project_git_scenarios -v
```

The module requires Python 3.10 or later and uses only its standard library plus an executable Git; this edition was exercised with Python 3.12.14 and Git 2.52.0. Each case creates synthetic directories and local bare repositories, isolates system/global Git configuration, and disables hooks and non-file transport. These are fixture properties, not permission to bypass a real project's security controls. Commands do not accept real repository or remote parameters. `--evidence-parent <existing-directory>` selects the report parent; `--min-free-bytes <n>` sets a pre-run free-space floor plus an 8 MiB run allowance.

**Required outputs.** Exact version, complete commands and exits, expected/actual values, assertion IDs, HEAD/index/working-tree/graph summaries, errors and evidence paths. Successful cases persist reports before reclaiming temporary repositories; failed cases keep logs and original fixtures, and a rerun must not overwrite them. CLI returns 0 for all passed cases and 1 for a scenario failure. Precondition failure produces not-run and exit 2, never a passing test. `--mutation commit-all --scenario index_snapshot` deliberately fails at `index.commit-uses-reviewed-index`, not because Git or an input file is missing.

**Judgment and limits.** Every applicable requirement MUST link to an actual check or a clearly pending human check. Keep passed, failed, not run, unknown and not applicable separate. Inapplicability requires evidence, such as absence of LFS objects. A missing extension does not make an LFS-using project inapplicable. The suite demonstrates bounded synthetic Git transitions, not real project correctness, remote protection, credential security, independent review or release authority.

**Sources and acceptance.** The [source claims](../../../sources/project-governance/git-operations.json) identify official manual versions, sections and supported propositions. When a version entry redirects, use the actual document version. The quality owner checks same-ID Chinese/English clauses, command results and pending checks. Passing synthetic tests while leaving platform protection “not run” is legitimate; equating a test count with all-clause conformance is not.
