# Rights, licensing and third-party materials

**Source version:** 0.1.0　**Status:** adopted　**Effective date:** 2026-10-30

**Document ID:** STD-PG-014　**Language:** en　**Authority:** Chinese (zh-Hans) only

This is the full, non-authoritative translation of the [Chinese source](../../../standards/project-governance/014-权属许可与第三方材料规范--v0.1.0.md). In a conflict, consult the Chinese source. MUST/MUST NOT bind only when the applicability condition holds and the exact version is selected for adoption.

## Applicability and exclusions

Applies to project-owned prose, code, graphics, examples, translations, third-party excerpts/dependencies and their contribution, notice and distribution decisions. This specification establishes material governance, not judicial determinations or a substitute for applicable law/professional advice. Linking third-party material is distinct from copying it.

## Terms and prerequisites

Ownership/rights title (权属) concerns rights in specified material. A license (许可) authorizes particular uses; ownership alone does not imply public permission. Project-owned material (自有材料) is within a valid owner confirmation. Third-party material (第三方材料) has separate rights and restrictions. Provenance (来源) is not a license. Contribution authorization (贡献授权) is not automatic assignment.

Before authoring or adoption, identify the clause's object, responsible actor, necessary inputs and expected artifacts; unknown is not not-applicable. The following clauses separately specify inputs, steps, artifacts, exceptions and recovery; global slogans are no substitute.

## Clauses

### PGL-01 Owner confirmation and material classification

- **Applicability, responsibility and inputs:** The material maintainer supplies specific files/scope, provenance and valid confirmation by the actual rights holder; the rights holder determines the claim and tools only record it.
- **Required steps and outputs:** Record confirmed project-owned material collectively within the paths or material types covered by the valid confirmation; locate actual third-party, specifically disputed and genuinely unknown objects separately. A valid owner confirmation is the basis for the project’s title record; missing extra creation-history, signature or registration evidence alone MUST NOT revert all owned material to unknown. Record actor, object scope, date, evidence reference and exclusions; identify objects through Git versions and paths, release manifests or external-original digests.
- **Failure, unknowns and recovery:** Record specific contradictions or out-of-scope objects separately and ask the rights holder to clarify; a local issue must not invalidate undisputed scope. Update the affected object’s decision after clarification while retaining the prior record.
- **Positive example:** The owner confirms owned prose; cited external standards remain third-party rather than project-owned.
- **Direct failure example:** All confirmed prose is marked title-unknown merely because no creation video exists.
- **Valid adjacent case:** A newly added vendor image outside the confirmation may remain pending without affecting the original prose confirmation.
- **Acceptance and automated/manual boundary:** Humans examine confirmation and scope; automation may check record completeness and object digests. Passed checks, attribution or repository access do not themselves create title.

### PGL-02 Per-material third-party permission

- **Applicability, responsibility and inputs:** The introducer supplies original source, version, copied/adapted extent, actual license text and intended use; the maintainer checks direct and bundled dependencies.
- **Required steps and outputs:** Distinguish links only, limited summaries, verbatim excerpts, adapted code, bundled dependencies and graphics/fonts. Record object, source, license version, notice duties, modification markings, allowed uses, distribution restrictions and unresolved items individually. An upstream license MUST NOT be extended to the whole repository or other material.
- **Failure, unknowns and recovery:** If permission is unknown or conflicts with planned use, do not claim permission for that use. Retain source and issue, then obtain permission, replace the material or omit it from that distribution, and recheck dependencies.
- **Positive example:** Use WCAG’s official link and a limited proposition without copying the full standard into the repository.
- **Direct failure example:** A downloaded font is treated as redistributable merely because it was available to download.
- **Valid adjacent case:** When only a reference link is retained, record link-only rather than inventing a copied-license inventory.
- **Acceptance and automated/manual boundary:** Automation checks source/notice locations and file identity; humans examine actual terms against use, and the rights holder or a professional handles legal uncertainty.

### PGL-03 Root license and distribution scope

- **Applicability, responsibility and inputs:** The rights holder supplies owned material they can license, recipients/channels and proposed terms; the maintainer aggregates third-party restrictions.
- **Required steps and outputs:** A root license MUST be explicitly selected by an authorized rights holder, with LICENSE specifying the license text, covered paths or material types, actual exclusions and effective time. Git identifies file versions, and builds generate release-file sets. If none is selected, state that no repository-wide open-source license has been granted. Do not automatically choose MIT, Apache or CC, and do not confuse confirmed ownership with a granted open-source license. Third-party material retains its own terms.
- **Failure, unknowns and recovery:** Without a license decision, retain license-not-selected, not owner-unknown. Do not mark public distribution ready when its prerequisites are missing. After a concrete decision, update notices, distribution manifest and entry points and recheck exact objects.
- **Positive example:** Project-owned rights are confirmed while LICENSE-NOTICE still says the repository-wide license is unselected.
- **Direct failure example:** A MIT license is added merely to clear a tool warning, or the root license swallows third-party restrictions.
- **Valid adjacent case:** The rights holder may choose different code and documentation licenses with clearly specified, unambiguous scopes.
- **Acceptance and automated/manual boundary:** Automation can compare notices, license files and records; validity of the choice and compatibility require human/legal assessment. An absent LICENSE file does not negate confirmed title.

### PGL-04 Contribution authorization and unselected agreements

- **Applicability, responsibility and inputs:** The contributor supplies submitted material, provenance, permission to contribute and existing obligations; the receiving maintainer supplies the actual contribution-terms state.
- **Required steps and outputs:** Contribution intake MUST check the contributor’s grantable scope against intended project use. State whether a DCO, CLA, inbound-equals-outbound or another mechanism actually exists and identify its exact text. Without a selected mechanism, do not assume signature or accept/select agreements on anyone’s behalf; submission, review and signing are distinct facts.
- **Failure, unknowns and recovery:** If authorization is unclear, record pending uses of that contribution. Technical review may continue without expanding use, but merging or passing tests cannot hide a grant gap. Record the decision against the exact contribution after clarification.
- **Positive example:** A contribution identifies adapted code’s original license and the contributor’s grantable scope for maintainer review.
- **Direct failure example:** Sending a patch is treated as signing an undisclosed CLA.
- **Valid adjacent case:** A spelling correction still follows provenance and the actual contribution process, without forcing an agreement the project has not adopted.
- **Acceptance and automated/manual boundary:** Humans confirm actual terms and authorization; automation only checks record identity and gaps and cannot sign or determine contract formation.

### PGL-05 Notices, provenance and modification chain

- **Applicability, responsibility and inputs:** The material maintainer supplies original notices, license requirements, changes and distribution composition; the translator supplies the relationship between translated notices and authoritative originals.
- **Required steps and outputs:** Retain required copyright/license/attribution notices and connect source, change scope, Git objects or release identities and notice locations. Git locates source modification chains; external originals have pinned versions or digests. Project ownership statements cover only confirmed scope; third-party statements MUST NOT be rewritten as project ownership. Translated notices cannot override original license meaning, and summaries do not replace required complete license texts.
- **Failure, unknowns and recovery:** Record missing notices or version mismatches and affected distributions. After restoring them, check content and in-package accessibility, preserving the revision chain rather than removing failure evidence.
- **Positive example:** Adapted code retains its license notice and marks changes; a newly written summary only links upstream.
- **Direct failure example:** A source URL is kept while a license-required in-package notice is deleted.
- **Valid adjacent case:** A material requiring attribution receives it under its actual terms without imposing that license on the whole repository.
- **Acceptance and automated/manual boundary:** Automation checks registered notice existence, digests and distribution-manifest consistency; humans verify precise terms, change markings and attribution meaning.

### PGL-06 Brands, graphics, fonts and generated material

- **Applicability, responsibility and inputs:** The asset introducer supplies graphic/font sources, identifier use, generation/adaptation method and rights scope; the brand owner confirms naming boundaries.
- **Required steps and outputs:** Record actual restrictions on brand names, trademarks, graphics, fonts and generated material separately. A code license does not automatically permit trademark or font use. A generation tool or newly created SVG is not a legal conclusion; record specific provenance and valid owner confirmation instead of indiscriminately leaving all new assets unconfirmed.
- **Failure, unknowns and recovery:** If a graphic contains unknown third-party content or an unlicensed embedded font, scope the issue to that asset and verify/replace it; then recheck image digest and notices.
- **Positive example:** A cover uses project-specific geometric SVG and ordinary font-family references, with no bundled font file; record that exact composition.
- **Direct failure example:** A traced third-party trademark is declared wholly owned because the SVG was saved locally.
- **Valid adjacent case:** Referencing a system font family does not copy a font file; later embedding a woff requires checking its distribution permission.
- **Acceptance and automated/manual boundary:** Humans examine source content and identifier use; automation may locate embedded/external resources and fix digests. Visual success is not graphic-rights clearance.

### PGL-07 Objections, disputes and recovery

- **Applicability, responsibility and inputs:** The maintainer receives a specific rights objection: contact, object, claimed right, basis and requested remedy, avoiding disclosure of unrelated personal or confidential information.
- **Required steps and outputs:** Retain the original object, notices, objection time and handling record, distinguishing confirmed scope from disputed scope. An authorized party assesses the matter; a checker does not decide infringement. Handle affected distribution/correction according to risk and existing authority, giving responsible parties concrete objects and decisions needed.
- **Failure, unknowns and recovery:** If unresolved, retain disputed rather than automatically admitting or denying. Recovery requires actual clarification, replacement or a licensing decision plus rechecking affected objects; evidence must not be altered to conceal the issue.
- **Positive example:** One image is challenged; retain its prior digest/notice and have the rights holder assess and decide replacement.
- **Direct failure example:** Historical files and the complaint record are deleted before claiming there was never a dispute.
- **Valid adjacent case:** A general inquiry lacking an object may require clarification without automatically disputing all project-owned material.
- **Acceptance and automated/manual boundary:** Humans assess facts, scope and disposition basis; automation checks state/object consistency, not infringement, ownership or legal remedies.

### PGL-08 Pre-distribution checks and responsibility handoff

- **Applicability, responsibility and inputs:** The release maintainer supplies the exact build-generated distribution manifest, root-license path rules, owner confirmation, actual third-party terms and contribution records; the rights holder owns licensing decisions.
- **Required steps and outputs:** Check the distribution set against the root license's path and material-type rules; check use and necessary notices individually for actual third-party objects and objects with different licensing conditions. Report passed, failed, unknown and not-applicable. Unresolved issues identify affected objects and required decisions. The releaser consumes checked scope rather than inferring public distributability from tests or directory completeness.
- **Failure, unknowns and recovery:** If the root license is unselected or third-party conditions unmet, the corresponding distribution remains not ready. After supplying decisions/notices, recheck the exact manifest. File changes leave prior checks valid only for prior objects, without deleting valid history wholesale.
- **Positive example:** Private reading material may retain an unselected root license; public release separately checks all required permissions and notices.
- **Direct failure example:** Passing every unit test changes license-not-selected into permission for commercial redistribution.
- **Valid adjacent case:** A third-party file absent from this distribution does not automatically impose its distribution notices on a package without it; dependencies must still be checked.
- **Acceptance and automated/manual boundary:** Artifacts are applicable license rules, actual third-party and differently licensed exceptions, distribution-notice check results and responsibility handoff; automated identity checks only find inconsistencies, while the relevant party verifies legal effect and actual authority.

## Exact dependencies and source interfaces

PGF-01, PGF-04 in STD-PG-001@0.1.0 supply the authority/identity, responsibility and acceptance interfaces consumed by this topic. PGD-01, 04, 05 in STD-PG-006@0.1.0 fix Chinese authority, translation and digest identity; PGE-03, 06 in STD-PG-005@0.1.0 consume license/state entry points. The actual rights holder makes licensing decisions, the release process consumes them and checkers provide no legal conclusion. The WIPO FAQ only supports distinguishing rights, licensing and registration; it does not establish this repository’s title.

- [Project governance framework and responsibility interfaces 0.1.0, Chinese](../../../standards/project-governance/001-项目治理领域总则与职责接口--v0.1.0.md); [standards registry](../../../registry/standards.json).
- [README branding and badges 0.1.0](readme-branding.md); [documentation authoring and internationalization 0.1.0](documentation-i18n.md); [rights, licensing and third-party materials 0.1.0](rights-license.md).
- [Limited source propositions and read scope](../../../sources/project-governance/documentation-rights.json). External sources do not prescribe this project's clause IDs, approval procedure or specific title; being readable does not make material freely copyable.
