# Documentation authoring and internationalization

**Source version:** 0.1.0　**Status:** adopted　**Effective date:** 2026-10-30

**Document ID:** STD-PG-006　**Language:** en　**Authority:** Chinese (zh-Hans) only

This is the full, non-authoritative translation of the [Chinese source](../../../standards/project-governance/006-文档编制与国际化规范--v0.1.0.md). In a conflict, consult the Chinese source. MUST/MUST NOT bind only when the applicability condition holds and the exact version is selected for adoption.

## Applicability and exclusions

Applies to authoring, updating and delivering specifications, guides, references, tutorials, records and translations. UI copy is covered only for language identification, fallback and examples shared with documentation; this does not replace product UI localization, regional legal adaptation or create a second normative authority.

## Terms and prerequisites

Authoritative source (权威源): the single Chinese body determining clause meaning. Translation (译文): a non-authoritative language rendering. Digest (摘要): byte identity; summary (摘要文字): a content synopsis, not interchangeable. Full (完整): all body text, examples, failure/recovery and dependencies are covered; it does not mean reviewed or adopted. Outdated (过时): the bound source has changed.

Before authoring or adoption, identify the clause's object, responsible actor, necessary inputs and expected artifacts; unknown is not not-applicable. The following clauses separately specify inputs, steps, artifacts, exceptions and recovery; global slogans are no substitute.

## Clauses

### PGD-01 Document types and single authority

- **Applicability, responsibility and inputs:** The author supplies audience, task, document type, Chinese source ID/version and state; the maintainer identifies the existing authoritative entry.
- **Required steps and outputs:** Specifications (adoptable requirements), guides (task completion), references (field/API facts), tutorials (repeatable learning paths) and records (facts of an occurrence) MUST be distinguished. Each states purpose and scope. Chinese is the sole normative authority; translations prominently identify source path, version, non-authority and conflict fallback, and are not registered as a second specification.
- **Failure, unknowns and recovery:** If a guide silently adds requirements, place the obligation explicitly in the Chinese specification or mark it as an example. A translation lacking source identity is unmapped and cannot supply adoption input.
- **Positive example:** A tutorial explains how to check links under PGE-04 without inventing a mandatory extra badge.
- **Direct failure example:** The English translation increments an independent normative version and claims to override Chinese.
- **Valid adjacent case:** An English tutorial can use a different teaching order if clearly non-normative and consistent with source requirements.
- **Acceptance and automated/manual boundary:** Automation checks source path/version/ID and declared fields; humans verify truthful type, authority and purpose rather than inferring authority from filenames.

### PGD-02 Glossary and normative language

- **Applicability, responsibility and inputs:** The domain author and translator supply definitions, context, abbreviations and potential collisions; preserve exact industry terms and source sections where applicable.
- **Required steps and outputs:** Maintain Chinese–English–meaning–context mappings, distinguishing 必须/MUST, 不得/MUST NOT, 建议/SHOULD and 可/MAY; these strengths bind only when applicable and selected for adoption. Do not translate not-run as failed or not-applicable as unknown.
- **Failure, unknowns and recovery:** For a missing term, retain the Chinese term with a provisional explanation and record it as unresolved rather than guessing an established legal/technical term. After domain-owner confirmation, update all occurrences and reread.
- **Positive example:** “采用/adoption” selects an exact specification object; “实现验收/implementation acceptance” concerns target execution evidence.
- **Direct failure example:** Translating a justified-deviation SHOULD into an unconditional must increases obligations.
- **Valid adjacent case:** Existing precisely defined API identifiers may remain in English; code names need not be translated.
- **Acceptance and automated/manual boundary:** Automation may compare registered terms and identifiers but cannot judge contextual obligation strength; humans read conditions, negation, exceptions and terms and record dispute resolution.

### PGD-03 Implementable bodies and reader paths

- **Applicability, responsibility and inputs:** A specification author supplies the actual problem, applicable/inapplicable branches, mechanism and consumers; a guide author supplies task prerequisites and observable results.
- **Required steps and outputs:** Every necessary requirement MUST have a stable ID and define actor, terms, inputs/prerequisites, ordered steps, outputs, failure/unknown states and recovery, responsibility interfaces and acceptance. Provide a positive case, a direct bad case breaking the key mechanism and a valid adjacent case outside its trigger. Preserve ID migration when merging or splitting; more headings cannot substitute for content.
- **Failure, unknowns and recovery:** If inputs or failure terminal states cannot be evaluated, clarify the mechanism; “handle according to best practice” is not a substitute. Requirement changes trigger checks of affected examples and consumers.
- **Positive example:** A link requirement supplies source path, decoding, boundary validation, destination and anchor criteria.
- **Direct failure example:** “Ensure internationalization quality” says nothing about who checks what or how failure recovers.
- **Valid adjacent case:** An offline local specification treats external reachability as a separate check rather than inventing a network-execution obligation.
- **Acceptance and automated/manual boundary:** Automation checks IDs/artifact identity and implemented finite mechanisms; humans walk from input to terminal state and judge whether examples exercise the mechanism. Complete fields do not prove sufficiency.

### PGD-04 Clause-by-clause mapping and full-text completeness

- **Applicability, responsibility and inputs:** The translator receives the exact Chinese body, source version/digest and clause sequence; the Chinese maintainer supplies the additions/deletions/changes.
- **Required steps and outputs:** A full translation MUST cover title, scope, terms, each same-ID requirement, all examples, failure/recovery, dependencies and source limits. Mapping records source path/digest, translation path/digest, source version, language tags, ordered matching IDs and state. English retains Chinese IDs and adds no obligations; omissions cannot be marked full.
- **Failure, unknowns and recovery:** Missing sections are partial, changed sources are outdated and disputed translations are needs-review. After correction compare the full text again; matching digests never become semantic-review evidence.
- **Positive example:** PGL-07 keeps its ID, objection recovery and all three examples with the same conditions in English.
- **Direct failure example:** Only clause titles are translated while the record claims full text.
- **Valid adjacent case:** A useful English synopsis may be labeled summary, but not the specification’s full translation.
- **Acceptance and automated/manual boundary:** Automation checks mapping uniqueness, both file digests and ID sequence; humans read all corresponding scope, conditions and cases and record specific mismatches.

### PGD-05 Version, digest and state synchronization

- **Applicability, responsibility and inputs:** The documentation maintainer receives the Chinese revision, prior translation mapping and current changeset; translation version binds to source version, while translation edits have a separate revision identity.
- **Required steps and outputs:** Any source byte change MUST invalidate or explicitly outdate the previous mapping, even without a version-number change. After translation fix the Chinese digest, then translation digest and clause sequence; reread the source to detect concurrent change. Current mapping and historical evidence remain separate; old reviews do not apply to new digests.
- **Failure, unknowns and recovery:** Any digest mismatch fails as stale; do not silently refresh mappings to hide an untranslated change. Review differences and reread before recording a new binding. Even unchanged meaning requires recording a formatting change and rechecking identity.
- **Positive example:** A Chinese typo fix may need no English wording change, but requires rechecking and rebinding the new source digest.
- **Direct failure example:** Chinese adds “MUST NOT”; only the JSON digest changes while English still permits the action.
- **Valid adjacent case:** A translation punctuation fix need not change the Chinese normative version but does update the translation digest and affected rereading.
- **Acceptance and automated/manual boundary:** Automation detects digest/version identity, source/translation IDs and duplicate mappings; humans alone determine actual semantic synchronization. The checker reports identity-verified, not semantic-equivalent.

### PGD-06 Link, example and data synchronization

- **Applicability, responsibility and inputs:** The author/translator receives actual file hierarchy, example commands, data fields, units, error states and link contracts.
- **Required steps and outputs:** Relative links MUST be recalculated after translation relocation. Examples preserve the mechanism, inputs, outputs, units and expected failures. Code identifiers, paths and protocol literals are not freely translated. Link to English only if a real translation exists; otherwise identify the Chinese destination.
- **Failure, unknowns and recovery:** Broken links, unit changes or an error example becoming success require repairing both contracts and rerunning. If a real service is unavailable, retain finite-fixture results and mark the real environment unexecuted.
- **Positive example:** Both languages use the same Python command and exit code; English links account for its three directory levels.
- **Direct failure example:** Seconds become milliseconds without numeric conversion, or copying Chinese relative paths breaks translation links.
- **Valid adjacent case:** Illustrative names or comments not affecting the mechanism may be localized while key inputs and criteria remain unchanged.
- **Acceptance and automated/manual boundary:** Automation checks local links/anchors and registered command literals; humans inspect example mechanisms and units, with actual execution reported separately from text checking.

### PGD-07 Availability, terminology fallback and UI boundary

- **Applicability, responsibility and inputs:** The maintainer supplies the language-coverage list; the UI owner supplies actual product language behavior, which a documentation translator does not implement by assumption.
- **Required steps and outputs:** Use accurate language tags such as zh-Hans and en. Distinguish full, partial, outdated, summary and unavailable from semantic-review state. Clearly label missing translation and fall back to authoritative Chinese. A UI language selector cannot imply untranslated content is localized, nor can translation change security/legal boundaries.
- **Failure, unknowns and recovery:** For unknown language or missing terminology, retain and explain the original term. Refer incomprehensible critical requirements to the domain owner rather than clearing them through machine translation. Update coverage and entry points after resolution.
- **Positive example:** The English README marks the sixteen domains without English full text as Chinese only.
- **Direct failure example:** Selecting English labels a Chinese specification English full without a translation.
- **Valid adjacent case:** A documentation repository without UI maintains language links and fallback without adding preference storage.
- **Acceptance and automated/manual boundary:** Automation checks registered tags and actual destinations; humans check fallback notices, critical terms and UI behavior. Correct tags prove neither regional compliance nor translation quality.

### PGD-08 Read-through acceptance and update responsibility

- **Applicability, responsibility and inputs:** The author, translator and receiving maintainer supply exact bilingual objects, clause mappings, source read scope and check results; any independent review separately identifies reviewer and object.
- **Required steps and outputs:** Separate automated identity checks, author clause-by-clause reading and independent review. Reading checks conditions, strength, examples, recovery, dependencies and gaps and records differences/disposition. The maintenance interface has the Chinese author notify the translator, the translator return mappings, and the maintainer accept or retain pending status.
- **Failure, unknowns and recovery:** Retain specific differences when errors are found, repair Chinese or English, then recheck identity and meaning; checker success must not overwrite an unread state.
- **Positive example:** A report states that 24 source/translation IDs match and the author has read each; independent translation review remains pending.
- **Direct failure example:** Similar word counts are used to declare semantic equivalence.
- **Valid adjacent case:** The same author may write both languages and self-check, but cannot label that work independent review.
- **Acceptance and automated/manual boundary:** Artifacts are mappings, difference disposition, actual checks and manual-scope records. Unexecuted items remain unexecuted; adoption and implementation acceptance are separate decisions.

## Exact dependencies and source interfaces

PGF-01, PGF-03, PGF-05 in STD-PG-001@0.1.0 supply the authority/identity, responsibility and acceptance interfaces consumed by this topic. The exact directions are: PGD-06 consumes the PGE-04 link/navigation interface in STD-PG-005@0.1.0; PGE-07 consumes the full-document source/translation procedure in PGD-04; PGD-04 consumes the stable document/clause identity interface in PGF-03. PGL-02, 04, 05 in STD-PG-014@0.1.0 provide materials, contribution and notice interfaces. These provider/consumer relationships do not change the adoption state of either standard. Sources support only syntax, language tags and limited accessibility propositions.

- [Project governance framework and responsibility interfaces 0.1.0, Chinese](../../../standards/project-governance/001-项目治理领域总则与职责接口--v0.1.0.md); [standards registry](../../../registry/standards.json).
- [README branding and badges 0.1.0](readme-branding.md); [documentation authoring and internationalization 0.1.0](documentation-i18n.md); [rights, licensing and third-party materials 0.1.0](rights-license.md).
- [Limited source propositions and read scope](../../../sources/project-governance/documentation-rights.json). External sources do not prescribe this project's clause IDs, approval procedure or specific title; being readable does not make material freely copyable.
