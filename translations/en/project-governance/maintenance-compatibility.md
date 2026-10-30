# Maintenance, response and compatibility commitments

**Source version:** 0.1.0　**Status:** adopted　**Effective date:** 2026-10-30

**Document ID:** STD-PG-017　**Language:** en　**Authority:** Chinese (zh-Hans) only

This is the full, non-authoritative translation of the [Chinese source](../../../standards/project-governance/017-维护响应与兼容承诺规范--v0.1.0.md). In a conflict, consult the Chinese source. MUST/MUST NOT bind only when the applicability condition holds and the exact version is selected for adoption.

## Applicability and responsibilities

Applies to ongoing maintenance, user support and compatibility commitments already made; one-off research or personal tools may make no response-time commitment, but should state their actual status. Maintenance states are active/limited/unmaintained/retired/undecided, independent of document, adoption and acceptance states. Maintainers receive and diagnose issues, publishers deliver repairs, support decision-makers confirm windows/service scope, and successors confirm handover. Depends on [PGK](work-items-responsibility.md), [PGV](version-release.md) and [PGP](security-privacy.md).

## PGM-01 Maintained objects and actual support scope

**Inputs and prerequisites:** Current versions, actual maintenance capacity, user tasks and committed platforms/interfaces.

**Procedure:** List maintained objects, supported versions/platforms/configurations and exclusions, stating status, intake channels, whether time limits are committed and their basis. If no team or channel exists, say so truthfully; template roles, CODEOWNERS examples or repository readability do not establish configured support.

**Outputs and acceptance:** Users can determine what is supported, how to report and which responses are not promised; support descriptions match actual intake/handling capabilities.

**Failure and recovery:** If capacity decreases or channels fail, update current descriptions, assess existing commitments and notify affected consumers; merely renaming a state does not erase commitments already made.

**Positive example:** A personal library supports two actually tested versions and explicitly has no response SLA.

**Direct failure example:** Stating 24×7 response without actual on-call staff or configuration.

**Valid adjacent case:** An exploratory project without an ongoing-maintenance decision states undecided rather than inventing a support-end date.

**Checking entry point:** `validate_maintenance` checks consistency among state/window/actual-configuration fields; corresponding decisions and actual observations verify real capacity and commitments.

## PGM-02 Intake, classification and diagnosis

**Inputs and prerequisites:** Exact versions/environments, symptoms, impacts and minimal safe reproduction.

**Procedure:** Classify security/data/availability/compatibility/general defects, recording reproduction status, affected scope and current handling; severity follows actual impact, not only reporter labels. During diagnosis, preserve original inputs and outputs first, then progressively narrow environment/dependency/configuration differences.

**Outputs and acceptance:** Every issue has a traceable state and next verification condition; unconfirmed causes remain unknown, and temporary mitigation is distinguished from root-cause repair.

**Failure and recovery:** For non-reproduction, list missing information and executable steps to supplement it; closing an Issue does not constitute verified repair. Handle sensitive reproductions privately under PGP.

**Positive example:** Replay the same input under old/new configuration combinations and establish that only one combination fails.

**Direct failure example:** Claiming the user's device is damaged without obtaining logs.

**Valid adjacent case:** A confirmed copy-only typo needs no production dump or customer data.

**Checking entry point:** Work-item/environment/reproduction reference consistency can be checked; root causes and impacts require substantive review.

## PGM-03 Repairs, updates and change notices

**Inputs and prerequisites:** Failure mechanisms, repair plans, affected requirements and supported versions.

**Procedure:** Establish direct failure and valid adjacent cases, repair bodies/implementations/tools and re-review under PGC; decide whether to backport to each supported version and list dependency/configuration changes. Notices state impacts, required user actions, compatibility windows and recovery entry points rather than meaningless “optimized” claims.

**Outputs and acceptance:** Repair objects and results are exact; unverified platforms do not support a claim that every platform is fixed. Backports and mainline with different source identities are bound separately.

**Failure and recovery:** If a repair introduces regression, retain the original chain and withdraw erroneous artifacts or repair forward; security-incident disclosure is handled separately under PGP.

**Positive example:** Each of two supported versions has an exact patch and corresponding regression results.

**Direct failure example:** Testing only mainline while claiming all historical releases repaired.

**Valid adjacent case:** An unaffected old branch may have a verifiable rationale for no backport, instead of copying changes without reason.

**Checking entry point:** Support-set/patch-object/evidence closure is checked automatically; backport necessity and compatibility commitments require manual checking.

## PGM-04 Compatibility commitments and dependency currency

**Inputs and prerequisites:** Public APIs/data formats, supported-version matrices, dependencies and upstream changes.

**Procedure:** Specify guaranteed dimensions and windows: source/binary/data/protocol/configuration/behavior may differ. Recheck dependency deprecations, vulnerabilities, licenses and protocol updates periodically or on triggers; a source's read date identifies only the object actually read, not automatic proof that all upstream information is current.

**Outputs and acceptance:** New changes can be assessed as breaking against commitments; exact consumer versions do not change silently. Unsupported combinations have explicit rejection or migration paths.

**Failure and recovery:** If upstream support ends, assess continued pinning, replacement or termination and retain residual risks; do not relabel untested combinations “compatible” to keep a table green.

**Positive example:** File reading is backward-compatible but the write format cannot be rolled back; explain the distinction.

**Direct failure example:** Promising behavioral, performance and data compatibility solely because API names are unchanged.

**Valid adjacent case:** A commitment limited to stable specification-text references does not include guarantees for all real business implementations.

**Checking entry point:** Support matrices and version references are checked automatically; real compatibility behavior undergoes acceptance on selected domain targets.

## PGM-05 Handover, permissions and responsibility continuity

**Inputs and prerequisites:** Current versions, open issues/risks, release/key/data-management responsibilities and actual recipients.

**Procedure:** Deliver exact entry points, unresolved/unknown matters, build/verification/recovery methods and support commitments; recipients confirm necessary inputs are obtainable. Permission handover uses real system changes with verified effects, and keys are not written into handover documents; old-actor revocation and necessary notification are completed separately.

**Outputs and acceptance:** Continuity of maintenance responsibilities and access boundaries is verifiable; without a recipient, reduce the state to limited/unmaintained and address existing commitments rather than inventing a successor team.

**Failure and recovery:** If receipt fails or necessary permissions are lost, retain specific blockers and first restore access or adjust support scope; old snapshots must not restore revoked permissions.

**Positive example:** A synthetic handover record lists only secret references and rotation steps, never private-key values.

**Direct failure example:** Changing the maintainer's name and claiming permissions on all platforms have migrated.

**Valid adjacent case:** The same person changing development tools need not invent a departure event, but still protects object and secret boundaries.

**Checking entry point:** Handover-record identities and states can be checked; platform revocation, acquisition and confirmation require actual evidence.

## PGM-06 Maintenance-termination interface

**Inputs and prerequisites:** Maintenance-termination decisions, consumers, alternatives and retention conditions.

**Procedure:** Distinguish end of support, deprecation, archival and deletion; communicate affected versions, termination conditions, migration and security risks. Hand necessary consumers and retention responsibilities to [PGA](deprecation-retirement.md), without treating repository archival as data deletion.

**Outputs and acceptance:** Entry points accurately show status, and users can find old objects and available migration information; no fictitious response commitments exist.

**Failure and recovery:** On discovering omitted consumers or remaining retention obligations, supplement handling without expanding deletion; resumed maintenance requires explicit new scope and responsibilities rather than automatic restoration of old commitments.

**Positive example:** A library no longer maintained retains exact source, license notices and alternative guidance.

**Direct failure example:** Immediately deleting sole recovery materials after archival without retention assessment.

**Valid adjacent case:** A completed one-off delivery with no subsequent support commitment may remain completed without inventing service retirement.

**Checking entry point:** State/migration/retention interface checks and actual entry-point reading review.
