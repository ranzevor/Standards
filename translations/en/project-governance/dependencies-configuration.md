# Dependencies, configuration and supply chain

**Source version:** 0.1.0　**Status:** adopted　**Effective date:** 2026-10-30

**Document ID:** STD-PG-012　**Language:** en　**Authority:** Chinese (zh-Hans) only

This is the full, non-authoritative translation of the [Chinese source](../../../standards/project-governance/012-依赖配置与供应链规范--v0.1.0.md). In a conflict, consult the Chinese source. MUST/MUST NOT bind only when the applicability condition holds and the exact version is selected for adoption.

## Applicability, terms and responsibilities

Applies to third-party code, tools, specifications, services, images and build configuration; projects without third-party runtime packages still register their tools and specification references, without being forced to introduce a package manager. Runtime dependencies run with the product; development dependencies support authoring, building and checking. Pinning means exact versions and necessary content identities, not security certification. Dependency maintainers manage versions and sources, configuration owners manage layering and sensitive values, and publishers manage artifact identity. Technical dependencies consume [L3, Chinese](../../../standards/L3/001-通用工程规范--v0.1.0.md) and actual L4/L5 requirements.

## PGS-01 Classification, versions and pinning

**Inputs and prerequisites:** Source-code imports/build entry points, platforms and tools, dependencies in use and support commitments.

**Procedure:** List runtime/development/optional/external-service/specification-reference dependencies separately, recording purpose, version range, actual resolved version, source and content verification. When adopting ecosystem lockfiles, synchronize them with declarations; without a locking mechanism, provide equivalent versions/digests and acquisition methods. Include transitive dependencies in upgrade and risk assessments, rather than registering only direct dependencies.

**Outputs and acceptance:** The necessary dependency set can be reproduced from the project entry point; lockfile versions/digests agree with acquired objects, and latest is not used as an immutable identity.

**Failure and recovery:** If resolution changes, verification fails or upstream objects become unavailable, stop that build/upgrade, retain the previous valid pins and verify sources; do not disable verification to continue.

**Positive example:** Runtime packages and documentation-checking tools are grouped separately, and CI uses the reviewed lockfile.

**Direct failure example:** Each installation resolves arbitrary latest versions while the build is claimed to be reproducible.

**Valid adjacent case:** A Python-standard-library-only project registers the actual Python version and verification scope, without inventing a requirements lockfile.

**Checking entry point:** `validate_dependencies_config` checks consistency among declarations, pins, digests and references; ecosystem resolvers run under the selected L5 tools.

## PGS-02 Sources, acquisition and artifact identity

**Inputs and prerequisites:** Official publishers/repositories/package sources, proposed versions, digests or signatures and their trust sources.

**Procedure:** Obtain exact objects from selected sources and verify downloaded content against expected identities; signatures use trusted publishing keys/identities and applicable verification procedures, not the mere presence of a signature field. Pin image artifacts, source packages, installation packages and documentation references separately; reading upstream documentation does not confer redistribution permission.

**Outputs and acceptance:** Publication sources, object digests and verification results are locatable; changing download mirrors or publication sources MUST include assessment of trust differences.

**Failure and recovery:** On digest/signature mismatch, isolate the object and record failure; for unknown results, first inspect cached content and sources rather than automatically trusting a reuploaded same-named file.

**Positive example:** A same-version package restored from cache is still checked against its pinned digest.

**Direct failure example:** Using a hash computed after download as the “verified expected upstream hash.”

**Valid adjacent case:** An ecosystem without signatures may use trusted sources and integrity checks while accurately listing guarantees it lacks.

**Checking entry point:** Local artifact digests can be automatically compared with expected values; publisher trust and actual signature verification undergo acceptance in the target ecosystem.

## PGS-03 Configuration layers and secret references

**Inputs and prerequisites:** Defaults, environment/project overrides, runtime arguments, secret-provider interfaces and configuration schema.

**Procedure:** Specify merge precedence, types, units, required fields and value boundaries; non-secret defaults may be versioned, while secrets are stored only as references or synthetic examples. Parse and validate final effective configuration at startup; reject unknown fields or missing critical values under an explicit policy. Redact logs while retaining the ability to explain configuration sources.

**Outputs and acceptance:** Identical inputs yield deterministic effective configuration; production and test configurations have distinguishable identities, and a directory named test does not establish isolation.

**Failure and recovery:** Invalid configuration rejects startup or returns to an explicit prior valid configuration, rather than silently falling back to weaker security values; a failed hot update keeps the original configuration and reports that the update was not applied.

**Positive example:** A timeout defaults to 30 seconds, is overridden by the project to 20 seconds and by a command argument to 10 seconds; the final value and source are recorded as 10 seconds.

**Direct failure example:** Automatically using a production account or disabling authentication when a token is missing.

**Valid adjacent case:** Unconfigured optional telemetry disables telemetry without requiring fabricated secret fields.

**Checking entry point:** Finite configuration models check precedence, types, boundaries and rejection, not whether a secret-management platform is configured; [PGP](security-privacy.md) owns security boundaries.

## PGS-04 Upgrades, compatibility and known risks

**Inputs and prerequisites:** Old and new versions, change logs, known vulnerabilities/deprecations, consumers and support matrices.

**Procedure:** Compare API/ABI, data formats, configuration defaults, toolchains and license changes; assess risks in light of actual usage paths. Upgrade requests list affected files/tests/documentation and rollback objects, with verification first in an isolated environment; even security updates do not skip data-compatibility checks.

**Outputs and acceptance:** Old/new combinations are verified according to commitments; residual risks and deferral reasons have owners and deadlines or trigger conditions. “No vulnerabilities found” is not written as a permanent security guarantee.

**Failure and recovery:** If an upgrade breaks contracts, return to previous pins or repair forward; if new data has been written, first determine whether the old program can read/write it, rather than merely downgrading package versions.

**Positive example:** A database-driver upgrade tests transactions, retries and error types, not merely successful import.

**Direct failure example:** Automatically accepting new default permissions based on a visible version-number change.

**Valid adjacent case:** If risk assessment confirms the affected functionality is unused, record the basis and subsequent monitoring rather than blindly changing unrelated code.

**Checking entry point:** Pin changes and necessary test sets are checked automatically; substantive review assesses compatibility mechanisms and risk acceptability.

## PGS-05 Build environments, caches and isolation

**Inputs and prerequisites:** Build commands, tool/dependency pins, cache keys, external-contributor inputs and output paths.

**Procedure:** Execute with the minimum necessary permissions; do not let untrusted builds read production secrets. Cache keys cover tools, pins, configuration and targets affecting results, and retrieved content is verified; a cache hit does not prove current checks actually ran. Separate source, cache, dependency and artifact directories and give reacquisition commands for rebuildable items.

**Outputs and acceptance:** Clean and cached builds have consistent contracts, corrupted caches are detected without contaminating authoritative sources, and artifact identities correspond to declared inputs.

**Failure and recovery:** If cache identity does not match, stop using that cache and rebuild from trusted inputs while retaining necessary failure records; do not copy a contaminated cache into the next round's authoritative input.

**Positive example:** A cache only accelerates dependency acquisition; test events still record the current actual execution.

**Direct failure example:** Directly reusing green test text from another commit as the current gate.

**Valid adjacent case:** A content-addressed pure-build cache with identical input identity may be reused, explicitly stating that no rebuild occurred this time.

**Checking entry point:** Verify cache/artifact references and digests; reclamation follows [PGX](materials-evidence-lifecycle.md).

## PGS-06 Supply-chain incidents and alternatives

**Inputs and prerequisites:** Credible reports of dependency withdrawal, source unavailability, identity anomalies, malicious releases or maintenance termination.

**Procedure:** Identify affected versions/artifacts and actual consumption scope, and restrict further distribution/deployment; inspect existing objects in use, select a trusted old version, patch or alternative, and update pins and sources. Separate facts, unknowns and handling in notices; treat sensitive reports under [PGP](security-privacy.md).

**Outputs and acceptance:** It is possible to trace which deliverables contain affected dependencies, differences between replacement and previous guarantees, and recovery acceptance.

**Failure and recovery:** Temporary source unavailability does not permit acquisition from arbitrary download mirrors; without a trusted alternative, mark blocked rather than skipping verification. Handle existing external effects separately when rollback has not eliminated them.

**Positive example:** A pinned digest is unchanged but upstream withdraws the package; assess actual content and distribution risks before deciding a replacement.

**Direct failure example:** Declaring a supply-chain incident repaired because package installation succeeds.

**Valid adjacent case:** A project not consuming that version records verifiable version evidence of non-impact without requiring unrelated downtime.

**Checking entry point:** Version/artifact consumption closure is checked automatically; the corresponding responsible parties assess incident credibility, impact and disclosure.
