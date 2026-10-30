# Project governance framework and responsibility interfaces

**Source version:** 0.1.0　**Status:** adopted　**Effective date:** 2026-10-30

**Document ID:** STD-PG-001　**Language:** en　**Authority:** Chinese (zh-Hans) only

This is the full, non-authoritative translation of the [Chinese source](../../../standards/project-governance/001-项目治理领域总则与职责接口--v0.1.0.md). In a conflict, consult the Chinese source. MUST/MUST NOT bind only when the applicability condition holds and the exact version is selected for adoption.

## Objects, terms and normative strength

This domain specifies decision-making, collaboration, versioning and delivery mechanisms from project initiation to retirement, and applies to software, tool, research and specification projects. A project without deployment, user data or a team is not thereby required to create a production environment, collect data or appoint a fictitious team; it should determine the corresponding trigger conditions on the facts. Algorithms, protocols, interfaces and industry business rules belong to L3–L5; this domain specifies only their selection, traceability, change and acceptance interfaces.

The “specification body” means requirements in the single Standards registry; a “project record” means an adopter's selection, configuration, execution and exceptions for exact clauses; “repository policy” constrains only a particular repository. A “decision-maker” has decision authority over the stated business scope; an “executor” operates on specific objects; a “reviewer” assesses requirements, differences and evidence; a “maintainer” handles ongoing changes. One person may hold compatible responsibilities, but author self-review does not thereby become independent review. MUST/MUST NOT are necessary requirements after applicability and adoption selection; SHOULD permits explained deviation; names, dates and thresholds in examples do not become defaults for every project.

## PGF-01 One specification authority and project records

**Actor and inputs:** The adopter; inputs are the document ID, version, path, SHA256 and selected clauses from the Standards registry.

**Procedure:** 1) Resolve the body from the single registry; 2) pin its identity and clauses in the project's adoption record; 3) fill in only project applicability, configuration, operating steps and exceptions; 4) return defects in general requirements to Standards for revision. A project may quote short clause titles and necessary locator text, but does not maintain a full specification text claiming independent effect.

**Failure and recovery:** If a path becomes invalid or a digest does not match, retain the original reference, mark it unresolved, and first inspect the old identity and migration mapping; do not silently substitute a same-named file or latest. Offline work may use an exact specification object already obtained, but its provenance and identity still belong to the same authority.

**Outputs and acceptance:** Project records contain no second set of general specification bodies; any applicable requirement resolves to one exact specification object. Automated checks verify references and digests; whether content exceeds its boundary requires reading.

**Positive example:** A project pins PGQ-03 of STD-PG-011 and supplies its own test command and database version.

**Direct failure example:** Copying this domain's entire text into the project's AGENTS, changing two places and still claiming the same version as Standards.

**Valid adjacent case:** A project's deployment runbook specifies its ports, migration commands and recovery order and references PGU clauses; it is not a second specification.

## PGF-02 Four product layers and responsibility map

**Actor and inputs:** The domain maintainer; inputs are the current document catalog, applicable scenarios and downstream consumers.

**Procedure:** Organize as A: framework/catalog; B: topic specifications; C: guides/templates/completed examples; D: acceptance/tools. A specifies applicability and dependencies without repeating B's steps; B fixes required actions and failure mechanisms; C turns B into operating records without creating implicit necessary conditions; D lists actual checking capabilities and manual criteria. Repository governance files contain only Standards' own selections and reference B.

**Failure and recovery:** If two different rules address the same responsibility, pause the adoption judgments affected by the conflict and list both identities and conflicting inputs; after designating a single responsible document, revise references and acceptance checks rather than eliminating the conflict by deleting necessary actions.

**Outputs and acceptance:** The [domain catalog, Chinese](../../../standards/project-governance/README.md) gives responsibilities, inputs/outputs, downstream consumers and supporting files item by item; a scenario without deployment can still fully adopt the other layers. Checkers verify catalog coverage, not the adequacy of responsibility allocation.

**Positive example:** PGV manages release manifests and tag identity; PGU manages environments, data migration and operational rollback. They share artifact identity without repeating publication steps.

**Direct failure example:** Using the Standards repository's branch convention instead of the Git topic specifications for all projects.

**Valid adjacent case:** A guide connects initiation, traceability and release, while necessary rules still point to their respective topics.

## PGF-03 Stable identity, revisions and source mappings

**Actor and inputs:** The author; inputs are added or changed technical obligations and their previous clauses, sources and consumers.

**Procedure:** Document IDs remain stable across revisions; local clause IDs are unique within a document, with cross-document identity expressed as document_id::clause_id. Changes to obligations, criteria or compatibility relationships create a new revision and clause-by-clause differences; changes of location alone update paths and digests without relabeling old review as new review. When reorganizing input requirements, establish source mappings by responsibility and preserve exact source bytes and decision identity.

**Failure and recovery:** If an old ID is reused for an unrelated obligation, a previous necessary action is omitted, or a verbatim-preservation claim is false, return the corresponding mapping row for correction; compare complete paragraphs and their context, then state the rationale for retention, splitting, modification or removal.

**Outputs and acceptance:** The mapping covers all necessary requirements being superseded; obligations, tools and templates can be associated through stable IDs. Approval of an old object does not automatically confer effect on its revision.

**Positive example:** Write coordination in the input requirements is split between branches and change review, preserving the corresponding failure and recovery provisions in each.

**Direct failure example:** Marking a set of revisions with different new content as “already approved” without corresponding adoption decisions.

**Valid adjacent case:** Two topics jointly carry one old requirement, and the mapping states which inputs and criteria each owns.

## PGF-04 Lifecycle and proportionate processes

**Actor and inputs:** The decision-maker and maintainer; inputs are project type, actual participants, delivery boundaries and support commitments.

**Procedure:** Determine entry and exit conditions in sequence for initiation, design and implementation, verification, delivery, maintenance and retirement. Record four axes separately: document state, independent technical review, project adoption and implementation acceptance; facts missing on one axis are not inferred from another. A single-person project may use one set of versioned records for several processes, but MUST distinguish decision-making, execution and review.

**Failure and recovery:** When an owner leaves, an entry condition is lost or support capacity is insufficient, mark the specific activity blocked/limited and hand it over; retain completed facts rather than rewriting the entire project as if it never existed.

**Outputs and acceptance:** Project records state each stage's current state, next condition, uncertainties and responsibility interfaces; a documentation project with no actual deployment may record reasoned non-applicability for deployment.

**Positive example:** A personal CLI project uses one file to record requirements and release checks, with substantive independent review for security-critical changes.

**Direct failure example:** Changing implementation acceptance from not-run to pass because every field has been filled in.

**Valid adjacent case:** Without a support commitment, no fictitious SLA is set, but the maintenance state is still disclosed accurately.

## PGF-05 Dependency order and cross-domain interfaces

**Actor and inputs:** The adopter and domain maintainer; inputs are project functions, topic dependencies and exact L0–L6 references.

**Procedure:** Establish PGI scope and PGT traceability first, then fix PGR content/identity and PGN adoption; select other topics according to actual functionality. Necessary dependency records identify the providing document/clause, guarantee, consumption prerequisites and verifier. L3 owns general engineering mechanisms; L4/L5 own domain- or stack-specific implementation constraints; L6 ADP-01 through 07 own project adoption and actual implementation-acceptance contracts. This domain supplements project governance records without inventing contradictory state semantics.

**Failure and recovery:** If a necessary provider is unresolved, versions conflict or execution dependencies form a cycle, locate the blocked clauses rather than declaring closure; a shared interface may be extracted or the order changed, but a necessary edge cannot be changed to a reference to bypass the problem.

**Outputs and acceptance:** Necessary dependencies of every applicable topic can be resolved; explanatory links are not all treated as execution dependencies. Graph checks detect missing edges and cycles; technical review verifies necessity.

**Positive example:** Data migration consumes transaction/backfill guarantees from the database schema migration specification; PGU specifies only the project's release window and responsibilities.

**Direct failure example:** Two documents each state that “approval of the other automatically approves this one.”

**Valid adjacent case:** Mutual links between a README and an authoring guide are navigation relationships, not an execution deadlock.

## PGF-06 Clause-by-clause acceptance and downstream entry points

**Actor and inputs:** The author, adopter and acceptance assessor; inputs are all current clauses, applicability and actual checking capabilities.

**Procedure:** For each clause, record the checking entry point, inputs, observation points, expected results, failure criteria and manual items. Automated checks identify only the fields, identities, states or finite models they actually implement; the necessity of natural-language requirements, README reading experience, independence and the truth of rights ownership are assessed through the corresponding reading or factual processes. Register new candidates as pending first and enter actual results separately after execution.

**Failure and recovery:** If tools and the body disagree, valid inputs are wrongly rejected or a negative example does not break its target, retain failure records, repair the target and independent expectations, and recheck affected clauses and integration entry points.

**Outputs and acceptance:** The [adoption guide, Chinese](../../../guides/ADOPTION.md), templates and completed examples support bidirectional navigation between clauses and actual records; keywords or clause counts alone never yield a semantic pass.

**Positive example:** A tool rejects expired exceptions, but a reviewer determines whether equivalent compensating safeguards exist for the specific risk.

**Direct failure example:** Declaring recovery steps usable because “a failure-and-recovery field exists.”

**Valid adjacent case:** An automated state model has passed while the real environment has not yet been exercised; both states coexist without overwriting each other.

## Dependencies and sources

System placement references [L0, Chinese](../../../standards/L0/001-体系架构与规范编制准则--v0.1.0.md), [L3, Chinese](../../../standards/L3/001-通用工程规范--v0.1.0.md) and [L6 ADP-01–08, Chinese](../../../standards/L6/001-项目采用与实现验收接口规范--v0.1.0.md); projects combine them according to their applicable scope. The four-layer responsibilities and project governance procedures are this domain's specification design, not a claim that external standards prescribe these directories verbatim. [Sources and supported claims, Chinese](../../../sources/project-governance/README.md) distinguish organizational rules, tools' original semantics and their respective applicability.
