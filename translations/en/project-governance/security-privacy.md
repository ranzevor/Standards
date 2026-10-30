# Security, privacy and operational boundaries

**Source version:** 0.1.0　**Status:** adopted　**Effective date:** 2026-10-30

**Document ID:** STD-PG-013　**Language:** en　**Authority:** Chinese (zh-Hans) only

This is the full, non-authoritative translation of the [Chinese source](../../../standards/project-governance/013-安全隐私与操作边界规范--v0.1.0.md). In a conflict, consult the Chinese source. MUST/MUST NOT bind only when the applicability condition holds and the exact version is selected for adoption.

## Applicability, terms and responsibilities

Applies to secrets, restricted data, permissions, vulnerabilities and operations affecting external resources; purely offline projects still protect input files and local permissions but need not create accounts or collect telemetry. Secrets include tokens, passwords, private keys and other values granting access; sensitive-data classification depends on actual content and applicable commitments. Security owners maintain threats and responses, data owners confirm purposes and retention, and operators check specific targets and environments. Deeper technical mechanisms reference security, identity, cloud and corresponding data-domain specifications; this domain owns their project-process interfaces.

## PGP-01 Data inventories, purposes and minimization

**Inputs and prerequisites:** Actual input/output/log/backup data flows, processing purposes, recipients and storage locations.

**Procedure:** Classify owned/third-party/personal/secret data and register acquisition basis, necessary fields, purposes, accessors and retention/deletion conditions. Prefer synthetic data for examples/tests; when real materials are necessary, first confirm permitted purposes and retention boundaries. Reassess cross-environment copying, third-party transmission and new purposes rather than treating “development needs” as a blanket description of every action.

**Outputs and acceptance:** Every data flow has an explicit purpose and responsibility; logs do not contain complete request bodies or real credentials by default; projects without personal-data usage truthfully record the absence of corresponding flows.

**Failure and recovery:** On discovering out-of-scope collection or disclosure, limit further propagation, preserve necessary incident evidence and follow actual response procedures; do not delete all logs to hide the incident or unconditionally retain all personal data forever.

**Positive example:** Conversion tests use artificially generated names rather than copying customer files into public Issues.

**Direct failure example:** Exporting an entire production database into a personal shared directory for debugging convenience.

**Valid adjacent case:** An offline tool without accounts registers local file flows without inventing a user database or consent forms.

**Checking entry point:** Data-flow, recipient and retention fields and synthetic-fixture markers can be checked; lawfulness of purpose, actual content classification and necessity require the corresponding professional judgments.

## PGP-02 Secrets and configuration isolation

**Inputs and prerequisites:** Secret-provider interfaces, environments/identities, permitted readers and disclosure-response methods.

**Procedure:** Obtain values from the selected secret interface only when needed; source/templates/examples use explicitly synthetic values or references, and logs/error outputs are restricted. Distinguish development, test and production identities; the name “test” is no substitute for checking actual resources. Secret rotation includes consumer switchover, revocation of old values and assessment of affected sessions/artifacts.

**Outputs and acceptance:** No real secrets enter released source or reports; missing secrets reject the related functionality or invoke an explicit secret-free mode, rather than silently using a higher-privilege identity.

**Failure and recovery:** If a value has leaked, revoke/rotate it on the actual platform and inspect usage scope; removing it only from the latest commit does not eliminate historical copies or existing access.

**Positive example:** Configuration stores secret_reference; tests store SYNTHETIC-NOT-A-CREDENTIAL.

**Direct failure example:** Exception handling prints a complete Authorization header to prove request success.

**Valid adjacent case:** Documentation shows field names and synthetic formats without a mechanical secret scanner treating them as real disclosure.

**Checking entry point:** Known-pattern scans provide clues only, not proof of complete absence of secrets; permissions, rotation and historical disclosure effects undergo acceptance on the target platform.

## PGP-03 Least privilege and environment side effects

**Inputs and prerequisites:** Operation intent, resource identity, actor, environment, permitted actions, cost/sharing scope and validity period.

**Procedure:** At execution, verify that the specific action and target are within the permitted scope and select minimum necessary permissions; assess read, write, disclosure, publication, deletion, production changes and real transactions separately. Check implementation to determine whether previews/tests can actually trigger external effects; possession of credentials, tool availability or specification adoption does not constitute a business decision.

**Outputs and acceptance:** Operation records identify exact resources and environments; out-of-scope, expired, different-actor or mismatched-target operations are rejected; approval to read does not automatically approve writing.

**Failure and recovery:** On permission denial, preserve the denial and report specific missing items rather than bypassing it through another account/entry point. If effects are unknown after timeout or cancellation, first inspect authoritative state rather than blindly repeating side-effecting actions.

**Positive example:** A synthetic local transaction model contains no real payment SDK or production endpoint.

**Direct failure example:** Treating a local test pass as permission for actual charges.

**Valid adjacent case:** Replaying a side-effect-free read-only query within the same permitted scope remains subject to budget and target constraints.

**Checking entry point:** The `operation_allowed` finite model checks actor/target/action/environment/time/generation; real authorization and platform effects are not facts that a JSON boolean can authenticate.

## PGP-04 Threats, controls and project acceptance

**Inputs and prerequisites:** Assets, trust boundaries, attack surfaces, dependencies and intended support scope.

**Procedure:** List important threats, possible paths, impacts, existing controls and residual risks; bind controls to implementation and verification. Select authentication/authorization, path traversal, injection, resource exhaustion and supply-chain controls according to actual exposure; an offline tool is not forced to add networking to “satisfy” tests.

**Outputs and acceptance:** Every necessary control has observable rejection/allowance behavior and failure handling; security tests stay within authorized targets, and sensitive production data is not the default input.

**Failure and recovery:** On finding a missing control, determine affected assets and prioritize isolation/repair, pausing the corresponding functionality when necessary; the responsible party records the object, reason, deadline and compensation for risk acceptance rather than having the checker accept risk automatically.

**Positive example:** Path-write validation rejects escape from the destination root while allowing valid Unicode filenames.

**Direct failure example:** Claiming threats are controlled solely because a “Security” heading exists.

**Valid adjacent case:** A project without stored accounts may mark password-storage controls not applicable, while still testing file permissions and data-disclosure paths.

**Checking entry point:** Technical controls reference the [security domain, Chinese](../../../standards/L4/security/README.md) and the actual stack; expert review assesses threat adequacy and residual risks.

## PGP-05 Reporting, response and disclosure

**Inputs and prerequisites:** Available, authorized private reporting channels, affected versions, minimal safe reproduction and contact states.

**Procedure:** The SECURITY entry point states actually available channels; if unconfigured, explicitly state that receipt is not guaranteed rather than inventing an email address or response SLA. Record receipt, triage, confirmation, mitigation, repair, verification and disclosure separately; minimize collection of secrets and customer data. Disclosure decisions consider consumer notification, patch acquisition and exposure of sensitive details, rather than making public Issues the default vulnerability entry point.

**Outputs and acceptance:** Reporters know how to submit necessary information safely; confirmed fixes must identify affected versions and rechecks, and “received” does not imply “resolved.”

**Failure and recovery:** If a channel is unavailable, provide a real alternative or retain unconfigured status; if sensitive content is accidentally public, restrict propagation and assess revocation/rotation and notification, retaining restricted evidence instead of multiplying copies.

**Positive example:** First provide an available private entry point and synthetic reproduction, then agree on disclosure scope.

**Direct failure example:** An Issue template requires uploading a real token to demonstrate a vulnerability.

**Valid adjacent case:** Public discussion of general hardening suggestions without exploitable details may follow the ordinary Issue process.

**Checking entry point:** Channel fields and response-state consistency can be checked; channel availability, disclosure decisions and legal obligations are confirmed in the actual project environment.

## PGP-06 Incident recovery and continual improvement

**Inputs and prerequisites:** Incident timelines, affected objects, authoritative states, responses/backups and necessary notifications.

**Procedure:** Retain facts and unknowns, prioritizing limitation of further harm; verify code/configuration/data/permission/artifact recovery separately and record risks that remain valid. Retrospectives produce specific controls, tests and maintenance work items rather than substituting individual blame for mechanism improvement.

**Outputs and acceptance:** Recovery criteria have actual observations, with unverified scope still unknown/not-run; coordinate incident-evidence retention and privacy-deletion conditions under [PGX](materials-evidence-lifecycle.md).

**Failure and recovery:** If old backups contain leaked secrets or old permissions, do not restore them directly as currently valid state; reapply revocations/corrections, then verify old/new compatibility and external effects.

**Positive example:** After restoring a database, replay still-valid access revocations and confirm old identities cannot access it.

**Direct failure example:** Claiming leaked data has automatically been retracted after rolling back a binary.

**Valid adjacent case:** When only a local synthetic test failed and no external effects occurred, retain test-repair records without inventing a security incident.

**Checking entry point:** Finite-state recovery checks and target security-domain acceptance; actual observations determine incident impact and recovery adequacy.
