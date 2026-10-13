# CoFoundr AI — Architecture Decision Log

## Purpose
Records any deviation from the frozen Phase 6 architecture discovered during implementation.
Required by Block G before any architectural change is made.

## Process
When implementation reveals a genuine architectural problem:
1. Stop the specific implementation path.
2. Add an entry below using the template.
3. Assess impact.
4. Propose the minimum required change.
5. Obtain approval.
6. Continue implementation only after approval is recorded here.

## Decision Template
*ADR-XXX* — [Short Title]

*Date* : YYYY-MM-DD  
*Sub-Phase* : SP-0X  
*Status* : PROPOSED | APPROVED | REJECTED | SUPERSEDED  
*Finding* : What the implementation revealed.  
*Conflict* : Which frozen decision this conflicts with.  
*Impact* : What breaks or changes if unresolved.  
*Proposed Change* : Minimum change required.  
*Approval* : [approved / rejected by whom and when]  
*Resolution* : What was actually done.  

---

## Decision Log

### ADR-C1 — Async Alembic Configuration

*Date* : 2026-10-13<br>
*Sub-Phase* : SP-02<br>
*Status* : PROPOSED<br>
*Finding* : `alembic/env.py` creates an async engine and reads the configured application database URL, but its comments describe a synchronous migration driver. `.env.example` still defines `ALEMBIC_DATABASE_URL` with `psycopg2`, and `requirements.txt` includes `psycopg2-binary` solely for migrations.<br>
*Conflict* : The migration configuration and environment template describe separate synchronous migration connectivity instead of the asynchronous PostgreSQL connection used by the application.<br>
*Impact* : Maintaining separate URLs and drivers can cause application and migration configuration to drift and adds an unnecessary migration-only dependency.<br>
*Proposed Change* : Derive the migration URL from the configured database URL, use `asyncpg` for the asynchronous migration connection, and do not retain a separate `ALEMBIC_DATABASE_URL` or `psycopg2-binary` solely for Alembic.<br>
*Approval* : Pending.<br>
*Resolution* : Pending. No migration configuration, dependency, or acceptance-test changes were made or verified in this documentation update.

### ADR-C2 — Explicit Infrastructure Initialization Lifecycle

*Date* : 2026-10-13<br>
*Sub-Phase* : SP-02<br>
*Status* : APPROVED<br>
*Finding* : The approved architectural preference is to create database engines and stateful infrastructure clients through explicit factories or application-lifecycle functions, not as import-time side effects. Source inspection found factories for the database engine, ChromaDB client, and file storage, and dependencies retrieve objects from `app.state`. However, `src/infrastructure/chroma/embedder.py` also creates a module-level `Embedder` instance; the inspected Phase 6 source does not establish that all infrastructure initialization is wired through an application lifecycle.<br>
*Conflict* : The module-level embedder instance does not fully follow the preference to defer stateful infrastructure initialization to an explicit lifecycle.<br>
*Impact* : Import-time state can complicate tests and lifecycle ownership. Treating the preference as a completed refactor would overstate the inspected implementation.<br>
*Proposed Change* : Keep the explicit-factory/lifecycle preference. Verify and complete application-lifecycle wiring; document any remaining import-time initialization as a justified exception with its implications.<br>
*Approval* : The architectural preference is designated approved by the SP-02 requirements; no individual approver or approval date is recorded in the repository.<br>
*Resolution* : Pending implementation and lifecycle verification. Existing factory functions were observed, but a complete refactor is not claimed.

### ADR-D1 — Phase 6 ChromaDB Persistence Path

*Date* : 2026-10-13<br>
*Sub-Phase* : SP-02<br>
*Status* : PROPOSED<br>
*Finding* : The Phase 5 ChromaDB path is `data/chroma_db`; the current Phase 6 settings and `.env.example` also point at that path. Phase 6 requires an isolated persistence directory.<br>
*Conflict* : Reusing the Phase 5 path would put Phase 6 persistence in the location whose existing data must remain available until SP-06 integration or migration.<br>
*Impact* : Sharing a directory before the migration plan is handled could conflate Phase 5 and Phase 6 data or disrupt existing Phase 5 behavior.<br>
*Proposed Change* : Use `./data/chroma_p6` for Phase 6 ChromaDB persistence. Preserve the Phase 5 path and its data until SP-06 handles integration or migration.<br>
*Approval* : Pending.<br>
*Resolution* : Pending. The current settings and environment template have not been changed or verified for the Phase 6 path.

### ADR-D2 — Centralized Frozen Settings

*Date* : 2026-10-13<br>
*Sub-Phase* : SP-02<br>
*Status* : PROPOSED<br>
*Finding* : Phase 6 configuration is intended to be centralized in one module-level `settings` instance. The inspected `src/core/config.py` defines that instance and configures the `Settings` model as frozen. Centralization supports typed, consistent configuration access; freezing prevents runtime mutation of loaded settings.<br>
*Conflict* : Duplicated settings instances or mutable configuration would weaken the single-source-of-truth configuration model.<br>
*Impact* : Divergent or mutable settings can make infrastructure behavior inconsistent across components.<br>
*Proposed Change* : Use one module-level `settings` instance and keep its settings model frozen. Verify configuration acceptance separately; no test result is asserted here.<br>
*Approval* : Pending.<br>
*Resolution* : Source structure observed; implementation acceptance and tests remain unverified.

### ADR-D3 — Phase 5 Provider Key Pools

*Date* : 2026-10-13<br>
*Sub-Phase* : SP-02<br>
*Status* : PROPOSED<br>
*Finding* : `src/config/settings.py` retains the Phase 5 provider key pools, and `src/core/config.py` is the separate Phase 6 settings model. The SP-02 guide directs that Phase 5 settings and agents remain in place until SP-06 migration.<br>
*Conflict* : Moving or duplicating provider key pools in the Phase 6 settings model before that migration risks changing Phase 5 imports or rotation behavior.<br>
*Impact* : Premature changes can break Phase 5 consumers or create competing key-pool and rotation configuration.<br>
*Proposed Change* : Keep provider key pools and their existing rotation behavior in the Phase 5 `settings.py` implementation until SP-06. Do not duplicate those pools in the Phase 6 settings model.<br>
*Approval* : Pending.<br>
*Resolution* : Pending end-to-end compatibility verification through SP-06; no Phase 5 runtime behavior was changed or tested in this documentation update.

### ADR-D4 — Startup-Scoped ChromaDB Access

*Date* : 2026-10-13<br>
*Sub-Phase* : SP-02<br>
*Status* : PROPOSED<br>
*Finding* : The inspected `src/infrastructure/chroma/scoped.py` provides startup ID validation, stamps writes, scopes reads, combines startup and extra metadata filters with `$and`, and scopes document deactivation and startup deletion. `query_records` does not itself require an active-record filter; callers must currently supply `is_active=True` among extra filters.<br>
*Conflict* : Startup scoping is a correctness boundary, and active queries that omit an explicit active filter can return inactive records.<br>
*Impact* : Missing or conflicting startup filters can expose another startup's records; omitting the active condition can surface inactive records.<br>
*Proposed Change* : Require a valid `startup_id` for every scoped Phase 6 operation; stamp writes with that ID; filter reads by it; combine it and any additional metadata filters using `$and`; keep deactivation and deletion startup-scoped; and ensure active queries exclude inactive records.<br>
*Approval* : Pending.<br>
*Resolution* : The scoped helpers implement several of these requirements, but automatic active-record filtering and acceptance verification remain pending. No test result is asserted here.