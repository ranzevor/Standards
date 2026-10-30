# README branding and badges

**Source version:** 0.1.0　**Status:** adopted　**Effective date:** 2026-10-30

**Document ID:** STD-PG-005　**Language:** en　**Authority:** Chinese (zh-Hans) only

This is the full, non-authoritative translation of the [Chinese source](../../../standards/project-governance/005-README品牌与徽章规范--v0.1.0.md). In a conflict, consult the Chinese source. MUST/MUST NOT bind only when the applicability condition holds and the exact version is selected for adoption.

## Applicability and exclusions

Applies when creating or revising a project root README, language entry points, cover and status badges. The audience is Chinese-speaking developers, adopters and maintainers visiting for the first time. A README is not an iteration review log, the entire normative corpus or a product certificate. A project without a remote does not need to create a remote, CI or Release for this specification.

## Terms and prerequisites

An entry point helps a reader take the next step; a cover identifies the brand; a badge is a short claim with an object, state and evidence destination; a local link resolves relative to its document; a named link has visible text conveying its purpose; maturity describes document state, not implementation acceptance.

Before authoring or adoption, identify the clause's object, responsible actor, necessary inputs and expected artifacts; unknown is not not-applicable. The following clauses separately specify inputs, steps, artifacts, exceptions and recovery; global slogans are no substitute.

## Clauses

### PGE-01 Reader tasks and entry structure

- **Applicability, responsibility and inputs:** When positioning changes or is first written, the maintainer supplies actual product scope, intended readers, current directories and available channels; reader tasks are not inferred from an organization name.
- **Required steps and outputs:** The home page MUST explain in natural Chinese what the project is, the problem it addresses and its limits, followed by a shortest-use path, task navigation, maturity, version, contribution, security and licensing entry points. Self-contained prose is required; badges do not replace positioning. Output is a README readable sequentially by a newcomer.
- **Failure, unknowns and recovery:** If a task or channel is unknown, identify the missing entry and an actually available alternative; remove inaccurate instructions rather than inventing a service. Re-walk the shortest path after repositioning.
- **Positive example:** A standards repository explains clause selection and adoption, then links to the local catalog and adoption interface.
- **Direct failure example:** The home page contains only “world-leading, fully passed” and review rounds, with no usable next step.
- **Valid adjacent case:** A documentation-only library needs no installation command; read, select and record adoption is a valid shortest path.
- **Acceptance and automated/manual boundary:** A human walks newcomer tasks and confirms a real artifact at each step; automation checks contracted section anchors and navigation targets, not readability through keyword counts, paragraph length or file count.

### PGE-02 Cover, alternatives and narrow screens

- **Applicability, responsibility and inputs:** The brand maintainer supplies the name, graphic-rights scope and target renderer; the documentation maintainer owns image alternatives and the textual equivalent.
- **Required steps and outputs:** A locally loadable cover or brand icon MUST be provided. Meaningful images need purpose-bearing alternative text, and local SVG covers or icons need title/desc. Essential information MUST also appear as selectable prose. Inspect actual pixels at 320 CSS px and a normal desktop width for clipping, glyphs, scaling and horizontal overflow; decoration must not carry the only operating information.
- **Failure, unknowns and recovery:** Image failure must leave positioning, status and use steps readable. Without a browser, record the unexecuted renderer/width; inspecting SVG source is not visual acceptance. When available, inspect the same file digest.
- **Positive example:** A banner contains only the Standards brand; maturity is separate prose and the name remains recognizable at 320px.
- **Direct failure example:** An installation command exists only inside a 1280px image, unreadable when reduced on a narrow screen and with empty alt text.
- **Valid adjacent case:** An explicitly decorative, unlinked background may have empty alt; a cover identifying the project cannot use that exception.
- **Acceptance and automated/manual boundary:** Automation checks image paths, non-decorative alt and SVG parseability; a human inspects both widths, image-off reading and scaling. Two screenshots do not establish complete WCAG conformance or all-platform behavior.

### PGE-03 Badge object, state and evidence

- **Applicability, responsibility and inputs:** The release/status maintainer supplies an exact document version, adoption record or real execution record. CI, coverage, downloads and Release badges cannot be invented without the corresponding object.
- **Required steps and outputs:** Project badges MUST use official standard Shields.io endpoints; custom-drawn or generated substitutes are not allowed. Each badge records its official URL, object, visible text, destination and state source. Static badges encode label, message and color using the official format and link to the corresponding project explanation. Adoption and draft state MUST be distinct; drafts do not inherit another object's adoption or review conclusions. Dynamic badges additionally require project, branch/workflow and status time checks.
- **Failure, unknowns and recovery:** If the state source is stale or unavailable, remove the success claim or use an evidence-based unknown/not-run state; correct the target and recheck the claim and data. When the image service is temporarily unreachable, alternative text, prose and the destination link MUST still provide the same information. Do not generate a custom badge as a fallback.
- **Positive example:** A standard Shields.io static draft badge links to the exact draft. A distribution-version badge matches project metadata, while adopted counts and states are checked against the current standards registry.
- **Direct failure example:** A handwritten SVG replaces a standard badge; build passing is shown without CI; or one file's adoption is represented as approval of the entire system.
- **Valid adjacent case:** A project without remote CI but with a recorded draft state may use a gray Shields.io static badge. Alternative text and prose still convey that state when read offline.
- **Acceptance and automated/manual boundary:** Offline checks validate the official URL format, encoded visible text, alternative text, destination and local state source without depending on remote SVG byte digests. A human checks claim meaning, service rendering and the exact objects behind dynamic data. Static badges do not represent unobserved live results.

### PGE-04 Named links and destination anchors

- **Applicability, responsibility and inputs:** The writer supplies the source document location, target file/section and renderer anchor rules; local paths resolve against the source document directory.
- **Required steps and outputs:** Links MUST have an intelligible name, existing file and existing target anchor. Parse inline, reference-style and image links; code examples and comments are not clickable navigation. Directory links lead to a real README. Prefer local entry points; record external-link verification scope without presenting offline existence checks as network availability.
- **Failure, unknowns and recovery:** When a target moves, update callers or retain an explicit migration entry. Do not generate a placeholder link for an unknown target. Decoded out-of-root paths, symlink escapes and unsupported protocols fail; click again from the real entry after repair.
- **Positive example:** “License notice” links to LICENSE-NOTICE.md and “Quick start” to an existing explicit anchor.
- **Direct failure example:** The license link exists only in a code block, or the file exists but its fragment does not.
- **Valid adjacent case:** Named reference links, percent-encoded Chinese paths and valid same-file anchors are allowed.
- **Acceptance and automated/manual boundary:** Automation validates actual link structure, relative paths and explicit/supported heading anchors. External reachability, label-purpose fit and renderer differences require manual checking. A finite parser must report its supported scope.

### PGE-05 Shortest use path and executable commands

- **Applicability, responsibility and inputs:** The feature maintainer supplies runtime, working directory, required inputs, output location and success criteria; documentation and software projects select reading or execution paths respectively.
- **Required steps and outputs:** Steps MUST follow actual execution order. Commands state prerequisites, missing-input behavior, outputs and capability limits. Runnable finite checks and complete acceptance are separate. Documentation-only projects provide at least a path from selecting a standard to recording scope.
- **Failure, unknowns and recovery:** Missing inputs, failed commands and unexecuted commands are distinct. A run with a missing required test fixture cannot pass. Retain error output, supply inputs of the required identity and rerun affected steps.
- **Positive example:** Give the local documentation entry first, then the required Python version, test fixture location, check command and expected exit code.
- **Direct failure example:** “One command verifies everything” silently skips a missing required test fixture.
- **Valid adjacent case:** Acceptance requiring project-specific inputs may provide a contract and input format rather than pretending to run a real business workload.
- **Acceptance and automated/manual boundary:** Execute listed quick commands and compare outputs; a code block’s existence does not prove executability. A human checks whether a newcomer knows where to start and how to recover.

### PGE-06 Navigation, maturity and versions

- **Applicability, responsibility and inputs:** The maintainer supplies the current catalog, adopted snapshots and release state; domain owners provide reachable entry points.
- **Required steps and outputs:** Task navigation and domain navigation MUST remain available, distinguishing current drafts, adopted versions and history. Version, contribution, security and licensing links stay discoverable. The home page summarizes maturity rather than carrying per-run review logs, internal staffing schedules or task dispatch.
- **Failure, unknowns and recovery:** If the central catalog has not yet been updated, do not call new bodies registered or adopted; identify them as drafts. Repair navigation/catalog mismatches and recheck; older versions retain their state.
- **Positive example:** Specification adoption, document versions and actual Releases are shown separately, each linking to the exact object.
- **Direct failure example:** An old review is used to claim all standards have passed, or navigation silently points to a historical copy.
- **Valid adjacent case:** A README can omit test counts and link maintenance/version policies while remaining complete.
- **Acceptance and automated/manual boundary:** Automation validates destinations and the bilingual navigation contract; a human checks the precise versions behind state claims. Navigation coverage is not domain technical sufficiency.

### PGE-07 Equivalent Chinese/English entry and fallback

- **Applicability, responsibility and inputs:** The Chinese author and English translator receive the same scope, steps, state and navigation list; Chinese is the authoritative source.
- **Required steps and outputs:** The English README MUST contain a real, complete corresponding entry, not “coming soon.” Tasks, state, commands, limits and licensing meaning remain equivalent, with reciprocal links. Chinese-only targets are identified as such; English labels cannot masquerade as English full text.
- **Failure, unknowns and recovery:** If the source changes without translation, record outdated and disclose fallback to Chinese. Resolve disputed meaning against Chinese; English cannot expand permissions or obligations. Recompute digests and read both after repair.
- **Positive example:** The English domain list explicitly marks its targets Chinese; translated drafts link to real English bodies.
- **Direct failure example:** English claims a formal release while Chinese says draft, or a Chinese catalog is called English documentation.
- **Valid adjacent case:** A legal notice may remain Chinese-only if English clearly explains its state and destination without claiming an English license text.
- **Acceptance and automated/manual boundary:** Automation checks both sets of anchors, matching navigation roles/targets and command contracts; the translator reads meaning, limits and examples paragraph by paragraph. Matching digests prove identity, not translation accuracy.

### PGE-08 Acceptance and maintenance of entry changes

- **Applicability, responsibility and inputs:** The entry-change author supplies file digests, change scope, actual check results and render targets; the receiving maintainer reviews them without treating self-review as independent review.
- **Required steps and outputs:** Link, badge and language-contract checks MUST run against the exact modified object, validating official standard Shields.io URLs, encoded text, destinations and state sources and rejecting handcrafted substitutes. Removing configuration MUST NOT let the current project bypass the standard-badge requirement. Complete shortest-path and narrow/wide reading checks, recording passed, failed, unexecuted and pending-manual items with object identity; old reviews belong only to their original objects.
- **Failure, unknowns and recovery:** A broken essential entry or false state fails entry acceptance; after repair rerun direct failures and valid adjacent cases. If a platform is unavailable, retain local results and list the untested platform, never presenting local screenshots as remote ones.
- **Positive example:** Local Chromium screenshots at two widths and link tests are recorded separately; remote rendering remains unexecuted.
- **Direct failure example:** Counting occurrences of “use, security, license” is treated as README acceptance.
- **Valid adjacent case:** A typo-only change may narrow human rereading, but exact digests, links and affected translations are still rechecked.
- **Acceptance and automated/manual boundary:** Check entries are checks/project_readme.py, checks/readme_badges.py and their tests. Direct failures include non-Shields.io URLs, mismatched text or destinations, invented state and removal of the required protocol configuration. Valid adjacent cases include officially escaped badges matching local sources. Humans assess prose, visuals, dynamic state sources and accessibility purpose. Complete acceptance needs both, and machine success authorizes neither release nor adoption.

## Exact dependencies and source interfaces

PGF-01, PGF-02, PGF-06 in STD-PG-001@0.1.0 supply the single-authority, document-responsibility and acceptance interfaces consumed by this topic. PGD-01, 04, 05, 06, 07, 08 in STD-PG-006@0.1.0 supply single Chinese authority and source/translation verification; PGL-02, 03, 06 in STD-PG-014@0.1.0 supply third-party, licensing and graphic-rights interfaces. These standards provide complementary interfaces; each project determines the applicable clauses.

- [Project governance framework and responsibility interfaces 0.1.0, Chinese](../../../standards/project-governance/001-项目治理领域总则与职责接口--v0.1.0.md); [standards registry](../../../registry/standards.json).
- [README branding and badges 0.1.0](readme-branding.md); [documentation authoring and internationalization 0.1.0](documentation-i18n.md); [rights, licensing and third-party materials 0.1.0](rights-license.md).
- [Limited source propositions and read scope](../../../sources/project-governance/documentation-rights.json). External sources do not prescribe this project's clause IDs, approval procedure or specific title; being readable does not make material freely copyable.
- [Shields.io static badge format](https://shields.io/badges/static-badge) defines the standard endpoint, label/message/color fields and character escaping. This clause establishes the requirement to use Shields.io for project badges.
