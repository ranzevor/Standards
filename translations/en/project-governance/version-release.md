# Versions, tags and releases

**Source version:** 0.1.0　**Status:** adopted　**Effective date:** 2026-10-30

**Document ID:** STD-PG-015　**Language:** en　**Authority:** Chinese (zh-Hans) only

This is the full, non-authoritative translation of the [Chinese source](../../../standards/project-governance/015-版本标签与发行规范--v0.1.0.md). In a conflict, consult the Chinese source. MUST/MUST NOT bind only when the applicability condition holds and the exact version is selected for adoption.

## Objects and terms

Applies to documentation/software versions, source tags, installation packages and formal releases made available to users; a local candidate is not a published version. Register document revisions, software versions, repository delivery sets and specification-adoption states separately. Publishers manage manifests and actual publication, maintainers confirm support scope, rights decision-makers confirm licenses, and adopters decide specification scope. Version rules may use SemVer or another explicit scheme; SemVer is not imposed on research results that declare no public API. Depends on [PGC](change-review-merge.md), [PGQ](quality-evidence.md) and [PGL](rights-license.md).

## PGV-01 Version spaces and compatibility semantics

**Inputs and prerequisites:** Public APIs/formats/protocols, documentation obligations, support commitments and the selected version scheme.

**Procedure:** Identify which object each version number denotes; record additions, corrections and breaking changes with compatibility consumers. When adopting SemVer, define public APIs and major/minor/patch semantics under its 2.0.0 rules; list documentation-obligation changes and migrations separately, without inferring specification adoption from a repository version. Do not silently replace the content of an already released version.

**Outputs and acceptance:** Users can determine compatibility and migration from version descriptions; candidate/prerelease identifiers are not described as formal publication or actual deployment.

**Failure and recovery:** If compatibility was mislabeled, provide a correction, affected scope and replacement version while retaining the old release identity; do not overwrite old tags to hide version errors.

**Positive example:** Removing a public parameter breaks compatibility and has a separate migration and version change under the selected scheme.

**Direct failure example:** Replacing a specification body's content while retaining the old same-version digest and adoption decision.

**Valid adjacent case:** A research dataset uses date/content-identity versions without claiming SemVer API guarantees.

**Checking entry point:** Consistency among versions, declarations, filenames and difference types can be checked; compatibility semantics require substantive review.

## PGV-02 Release manifests and readiness gates

**Inputs and prerequisites:** Complete candidates, necessary checks, independent review, licenses/notices, dependencies and maintenance arrangements.

**Procedure:** Release builds generate complete file manifests, sizes and digests from the actual delivery set and ship them with artifacts; source is bound to the exact commit/tree. Release notes list tools/pins, user-relevant changes, applicability/support, known defects, installation/recovery and necessary decisions. Readiness gates check necessary items, current results and unresolved matters, distinguishing ready-for-review from ready-to-publish.

**Outputs and acceptance:** All objects proposed for distribution are in the manifest; unresolved necessary blockers prevent ready-to-publish. A documentation revision without a release task may remain a reviewable candidate.

**Failure and recovery:** For missing artifacts, stale checks or unresolved license scope, locate the corresponding blockers and continue work not dependent on them; do not invent an “approver” to fill a blank.

**Positive example:** A local specification candidate contains complete documentation and offline tools, but does not claim public-release readiness while the root license remains undecided.

**Direct failure example:** Publishing third-party fonts with unchecked rights merely because tests exit 0.

**Valid adjacent case:** A project with no binary artifacts releases only a source/documentation set, accurately listed in its manifest.

**Checking entry point:** The `release_ready` finite model checks complete necessary sets, exact evidence and distribution prerequisites, not real rights or publication permissions.

## PGV-03 Associate tags, source and artifacts

**Inputs and prerequisites:** The exact release commit, tag name, selected tag/signature policy and build artifacts.

**Procedure:** Before creation, confirm that the source object matches gates; use annotated tags according to policy and record the tag object and peeled commit. Artifacts record their own digests and build inputs rather than deriving package content from tag names. If signatures are required, verify signer trust and the specific object; projects not requiring signatures accurately state that the guarantee is not established.

**Outputs and acceptance:** Tags resolve to expected commits and artifact digests agree with manifests; a signature result belongs to the specific signed object, not a security certification of the entire project.

**Failure and recovery:** If a same-named tag already exists, inspect its object first rather than overwriting a public tag; correct a mistagged release through a new identifier or withdrawal. After creation/upload timeout, inspect actual tags/objects before retrying.

**Positive example:** After `git tag -a v0.1.0 <commit> -m 'Version 0.1.0'`, verify that `git rev-parse v0.1.0^{commit}` equals the intended commit.

**Direct failure example:** The tag points to a new commit, but the installation package is still a cached build of old source.

**Valid adjacent case:** A local synthetic tag scenario verifies resolution relationships without claiming a remote release occurred.

**Checking entry point:** Local Git examples actually test tags/commits; artifacts and signatures use the target build/verification tools.

## PGV-04 Publication operations and result verification

**Inputs and prerequisites:** Readiness gates, exact targets, publication scope and actual required permissions/confirmations.

**Procedure:** Reread target state and version occupancy before publication; after upload/registration, read back the version, source, file set and content identity from the target. Record publication events, specification-adoption decisions and production deployment separately, without letting one automatically trigger the other two.

**Outputs and acceptance:** Users can obtain the expected exact content from formal entry points; published requires an actually accessible object and read-back evidence.

**Failure and recovery:** Partial upload success or a lost response is recorded as partial/unknown and the target inspected; retry only when non-execution is confirmed or the target's explicit idempotency contract makes it safe. MUST NOT infer that no remote object was created merely because the client was canceled.

**Positive example:** After upload, verify each artifact's digest before updating the formal download entry point.

**Direct failure example:** Writing “formally released” into CHANGELOG as soon as a tool starts uploading.

**Valid adjacent case:** A local-delivery-only project uses its exact local set as the delivery object without fabricating a remote Release event.

**Checking entry point:** Finite publication-state models check evidence and unknown branches; actual target read-back is necessary independent acceptance.

## PGV-05 Release failure, withdrawal and recovery

**Inputs and prerequisites:** Erroneous versions/artifacts, affected consumers, original failures and available alternatives.

**Procedure:** Distinguish source repair, artifact rebuild, version withdrawal, download-entry correction and operational rollback; notify specific impacts, replacement versions and migration. Retain old identities and withdrawal reasons and follow ecosystem rules for versions that cannot be republished; do not delete all history to pretend publication never occurred.

**Outputs and acceptance:** Old/new object relationships are clear and users can avoid or handle erroneous versions; recheck manifests, acquisition paths and compatibility after recovery.

**Failure and recovery:** If old programs are incompatible with new data, follow PGU recovery points/forward repair; copies already acquired by consumers do not automatically disappear on withdrawal and need separate remedies.

**Positive example:** Release 0.1.1 repairs an installation script and explicitly identifies the 0.1.0 error and affected platforms.

**Direct failure example:** Replacing content under the same package name while continuing to claim the old digest and signature valid.

**Valid adjacent case:** An undistributed local failed build may be rebuilt with necessary failure records retained, without falsely claiming a public version was withdrawn.

**Checking entry point:** Withdrawal/replacement relationships and state records can be checked; consumer impacts and actual acquisition behavior are tested directly.

## PGV-06 Post-release adoption and maintenance interfaces

**Inputs and prerequisites:** Exact release sets, support matrices, adoption selections and maintenance states.

**Procedure:** Deliver versions/artifacts/known limitations to maintenance and adoption interfaces; adopters pin actual selections rather than upgrading automatically when upstream releases a new version. Documentation-correction/security-update notices state whether necessary obligations, configuration and migration are affected instead of merely saying “please update.”

**Outputs and acceptance:** Releases trace to maintenance scope and adoption-change conditions; a release's existence proves neither that all downstream consumers upgraded nor that all implementations passed.

**Failure and recovery:** If notices were omitted or support information conflicts, correct current entry points and retain original records; versions no longer supported receive alternatives and retention strategies under PGA.

**Positive example:** A new-version notice lists breaking fields and the old-version support window; projects decide upgrades against exact clauses themselves.

**Direct failure example:** Overwriting a project's pinned specification version as soon as a new upstream tag appears.

**Valid adjacent case:** Different projects may adopt the same software version at different times, with states registered separately.

**Checking entry point:** Interface records under [PGN](adoption-exceptions-upgrades.md) and [PGM](maintenance-compatibility.md), and verification of actual consumers.
