# SP-01 — Database Foundation
## PostgreSQL · Async SQLAlchemy · Alembic · Repository Pattern

**Status:** Not started  
**Duration:** 12 hours (Days 1–2.5)  
**Depends on:** Nothing — this is the root  
**Enables:** SP-02, SP-03, SP-04, SP-05, SP-06  

---

## START HERE

**Before touching any file, answer these three questions from memory:**
1. What is the difference between `alembic revision --autogenerate` and `alembic upgrade head`?
2. Why must AsyncSession open and close per request, not per application?
3. What does CASCADE DELETE do at the database level?

If you cannot answer all three, read Section 6 and Section 7 first.

**First concept to understand:** AsyncSession lifecycle — Section 6.2  
**First existing file to inspect:** `src/config/settings.py` — your Phase 5 config  
**First file to create:** `src/core/enums.py`  
**First implementation decision:** UUID vs integer primary keys (answer: UUID — see Section 3)  
**First verification:** `alembic upgrade head` on a fresh database completes without error  

**Recommended implementation order:**
```
enums.py → base.py → models (users first) → alembic init → 
alembic env.py configure → migration 001 → repositories → 
session dependency → conftest.py → tests
```

**What successful completion looks like:**
- Fresh PostgreSQL database receives `alembic upgrade head` without error
- `alembic downgrade base` reverses all migrations cleanly
- Deleting a startup also deletes its conversations, messages, memories
- Concurrent message inserts produce unique sequence numbers

---

## TEST DATABASE STRATEGY

**Use a separate test database — never your development database.**

Set `TEST_DATABASE_URL` in your `.env`:
```
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/cofoundr_dev
TEST_DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/cofoundr_test
```

Create the test database manually once:
```
createdb cofoundr_test
```

**conftest.py strategy:**  
`tests/conftest.py` is the root pytest config file. It must:
1. Read `TEST_DATABASE_URL` from environment
2. Run `alembic upgrade head` against the test database before tests start
3. Provide an `async_session` fixture that each test uses
4. Roll back or truncate tables between tests (do not drop/recreate for speed)

Recommended approach: wrap each test in a transaction that rolls back after the test. This gives you a clean slate per test without recreating tables.

**conftest.py location:** `tests/conftest.py` (root level, shared across all integration test files)

---

## CONCEPTS TO UNDERSTAND

### What you must learn for SP-01

🟢 **BASIC — PostgreSQL basics**  
You already know SQL. PostgreSQL adds: UUID type, TIMESTAMPTZ (timezone-aware), native enum types, `gen_random_uuid()` server function. No new concepts — just PostgreSQL-specific syntax.

🟢 **BASIC — SQLAlchemy ORM**  
You have seen basic async SQLAlchemy syntax already. Models are Python classes. Columns are class attributes. Relationships are declared with `relationship()`. The ORM translates Python into SQL automatically.

🟡 **INTERMEDIATE — Repository Pattern**  
Instead of writing DB queries everywhere, you create one class per table that owns all queries for that table. Routes call repositories, never the DB directly. This keeps DB logic in one place and makes testing easier.

What you need to understand:
- Each repository takes an `AsyncSession` as input
- Repository methods are async functions
- No raw SQL allowed outside repositories
- One repository class = one table = one responsibility

🟡 **INTERMEDIATE — Alembic Migration Workflow**  
Alembic tracks schema changes like Git tracks code. Every schema change = one migration file. See Section 7 for full explanation.

🔴 **ADVANCED — Alembic env.py async configuration**  
By default, Alembic uses a synchronous engine. Your project uses async SQLAlchemy. The `alembic/env.py` file must be modified after `alembic init` to use an async engine. This is a required manual step — autogenerate will not work until this is done. See Section 7.1 for what must be configured.

🔴 **ADVANCED — Async SQLAlchemy Session Lifecycle**  
The most critical concept in SP-01. See Section 6.2. Read it twice.

🔴 **ADVANCED — Concurrent Message Sequence Numbers**  
See Section 5. This is a real concurrency problem with a specific solution.

---

## 1. Database Architecture

| Property | Value |
|---|---|
| Database | PostgreSQL (single database) |
| Driver | asyncpg (async PostgreSQL driver) |
| ORM | SQLAlchemy 2.0 async |
| Migrations | Alembic |
| Connection pooling | SQLAlchemy built-in async pool |
| Session model | One AsyncSession per HTTP request |

**Development expectation:**  
PostgreSQL runs locally. Connection string lives in `.env` as `DATABASE_URL`. No Docker required but recommended for clean setup.

**Runtime expectation:**  
FastAPI starts → creates async engine once → each request gets its own session → session commits or rolls back → session closes.

---

## 2. Complete Schema

### 2.1 users

| Column | Type | Required | Key | Default | Constraint | Purpose |
|---|---|---|---|---|---|---|
| user_id | UUID | YES | PK | gen_random_uuid() | — | Unique identifier |
| email | VARCHAR(255) | YES | UNIQUE | — | NOT NULL | Login identity |
| password_hash | TEXT | YES | — | — | NOT NULL | Argon2id hash |
| created_at | TIMESTAMPTZ | YES | — | now() | NOT NULL | Record creation time |
| updated_at | TIMESTAMPTZ | YES | — | now() | NOT NULL | Last modification time |

No soft delete on users. Hard delete only.

---

### 2.2 startups

| Column | Type | Required | Key | Default | Constraint | Purpose |
|---|---|---|---|---|---|---|
| startup_id | UUID | YES | PK | gen_random_uuid() | — | Unique identifier |
| owner_id | UUID | YES | FK → users | — | NOT NULL | Ownership |
| name | VARCHAR(255) | YES | — | — | NOT NULL | Startup name |
| description | TEXT | NO | — | NULL | — | Optional description |
| stage | VARCHAR(50) | YES | — | 'IDEA' | NOT NULL | IDEA/MVP/TRACTION/GROWTH |
| created_at | TIMESTAMPTZ | YES | — | now() | NOT NULL | — |
| updated_at | TIMESTAMPTZ | YES | — | now() | NOT NULL | — |

CASCADE: deleting a user cascades to their startups.

---

### 2.3 conversations

| Column | Type | Required | Key | Default | Constraint | Purpose |
|---|---|---|---|---|---|---|
| conversation_id | UUID | YES | PK | gen_random_uuid() | — | Unique identifier |
| startup_id | UUID | YES | FK → startups | — | NOT NULL | Parent startup |
| title | VARCHAR(255) | YES | — | — | NOT NULL | Display name |
| created_at | TIMESTAMPTZ | YES | — | now() | NOT NULL | — |
| updated_at | TIMESTAMPTZ | YES | — | now() | NOT NULL | — |

CASCADE: deleting a startup deletes all its conversations.

---

### 2.4 messages

| Column | Type | Required | Key | Default | Constraint | Purpose |
|---|---|---|---|---|---|---|
| message_id | UUID | YES | PK | gen_random_uuid() | — | Unique identifier |
| conversation_id | UUID | YES | FK → conversations | — | NOT NULL | Parent conversation |
| role | VARCHAR(20) | YES | — | — | NOT NULL | USER / ASSISTANT / SYSTEM |
| content | TEXT | YES | — | — | NOT NULL | Message text |
| sequence_number | INTEGER | YES | — | — | NOT NULL | Ordering (no gaps) |
| created_at | TIMESTAMPTZ | YES | — | now() | NOT NULL | — |

UNIQUE constraint: `(conversation_id, sequence_number)` — no two messages in same conversation can share a sequence number.

CASCADE: deleting a conversation deletes all its messages.

---

### 2.5 memories

| Column | Type | Required | Key | Default | Constraint | Purpose |
|---|---|---|---|---|---|---|
| memory_id | UUID | YES | PK | gen_random_uuid() | — | Unique identifier |
| startup_id | UUID | YES | FK → startups | — | NOT NULL | Scope |
| memory_type | VARCHAR(50) | YES | — | — | NOT NULL | startup_fact/preference/decision/goal/constraint |
| content | TEXT | YES | — | — | NOT NULL | Extracted memory text |
| importance | FLOAT | YES | — | 0.5 | NOT NULL | 0.0 to 1.0 |
| created_at | TIMESTAMPTZ | YES | — | now() | NOT NULL | — |

CASCADE: deleting a startup deletes all its memories.

---

### 2.6 Indexes

```
users: email (UNIQUE — already indexed)
startups: owner_id (for listing user's startups quickly)
conversations: startup_id (for listing startup's conversations)
messages: conversation_id + created_at (for paginated retrieval in order)
messages: (conversation_id, sequence_number) UNIQUE
memories: startup_id (for retrieval by startup)
```

---

## 3. ER Diagram

```mermaid
erDiagram
    users ||--o{ startups : owns
    startups ||--o{ conversations : contains
    startups ||--o{ memories : scopes
    conversations ||--o{ messages : contains

    users {
        uuid user_id PK
        varchar email UK
        text password_hash
        timestamptz created_at
        timestamptz updated_at
    }

    startups {
        uuid startup_id PK
        uuid owner_id FK
        varchar name
        text description
        varchar stage
        timestamptz created_at
        timestamptz updated_at
    }

    conversations {
        uuid conversation_id PK
        uuid startup_id FK
        varchar title
        timestamptz created_at
        timestamptz updated_at
    }

    messages {
        uuid message_id PK
        uuid conversation_id FK
        varchar role
        text content
        int sequence_number
        timestamptz created_at
    }

    memories {
        uuid memory_id PK
        uuid startup_id FK
        varchar memory_type
        text content
        float importance
        timestamptz created_at
    }
```

---

## 4. Cascade Behavior

```mermaid
flowchart TD
    U[DELETE user] --> S[Cascade → delete startups]
    S --> C[Cascade → delete conversations]
    S --> M[Cascade → delete memories]
    C --> MSG[Cascade → delete messages]
```

This cascade lives at the **database level** using `ON DELETE CASCADE` on foreign keys. You do not write Python code to handle this. PostgreSQL handles it automatically when you delete a parent record.

---

## 5. 🔴 ADVANCED — Message Sequence Numbers

**The problem:**  
Two users send messages to the same conversation at the exact same millisecond. Both read `MAX(sequence_number) = 5`. Both compute `next = 6`. Both insert with `sequence_number = 6`. You now have two messages with sequence 6 — a uniqueness violation or, worse, silent data corruption if no constraint exists.

**Why this matters:**  
Messages must display in correct order. Gaps or duplicates break conversation history. This is a real concurrency problem even in development with multiple browser tabs.

**What you need to understand:**  
- `SELECT MAX(sequence_number)` followed by `INSERT` is not atomic — another thread can run between those two operations
- You need both operations inside a single transaction with a row-level lock
- `SELECT ... FOR UPDATE` locks the parent conversation row so only one transaction at a time can compute the next sequence number

**Implementation hint (conceptual):**  
Inside your `MessageRepository.append()` method:
1. Begin a transaction
2. Lock the conversation row with SELECT FOR UPDATE
3. Query MAX sequence number for that conversation
4. Compute next = MAX + 1 (or 1 if no messages yet)
5. Insert the message with that sequence number
6. Commit

The lock on step 2 forces any concurrent inserts to wait until step 6 completes.

**Common mistake:**  
Forgetting to use `FOR UPDATE` and assuming `UNIQUE` constraint is enough. The constraint will catch it, but as an error — you want to prevent the collision, not just detect it.

**Verify after implementing:**  
Run 10 concurrent insert requests to the same conversation. All 10 should succeed. Sequence numbers should be 1 through 10 with no duplicates and no gaps.

---

## 6. SQLAlchemy Architecture

### 6.1 Models

Every model inherits from a shared `Base` and a `TimestampMixin`.

**Base:** SQLAlchemy `DeclarativeBase` subclass. Gives models their ORM mapping capability.

**TimestampMixin:** Adds `created_at` and `updated_at` to every model automatically. `updated_at` must refresh on every update via `onupdate=func.now()`.

**File ownership:**
```
src/repositories/base.py → Base class + TimestampMixin
src/repositories/models/user.py → User model
src/repositories/models/startup.py → Startup model
src/repositories/models/conversation.py → Conversation model
src/repositories/models/message.py → Message model
src/repositories/models/memory.py → Memory model
```

### 6.2 🔴 ADVANCED — AsyncSession Lifecycle

**What it means:**  
AsyncSession represents one unit of database work. It holds a connection from the pool, tracks changes, and either commits or rolls back when done.

**Why per-request, not per-application:**  
One shared session across all requests means: Request A's uncommitted changes are visible to Request B. Request A's error rolls back Request B's work. Connections are held open forever, exhausting the pool.

**What you need to understand:**  
- Engine is created once at application startup (expensive)
- Session is created once per HTTP request (cheap)
- Session commits on success, rolls back on exception
- Session closes when request ends — connection returns to pool

**Implementation hint:**  
Use an async context manager as a FastAPI dependency. The dependency yields the session, then the `finally` block closes it regardless of what happened.

**Common mistake:**  
Creating the session at module level or as a class variable. This shares one session across all requests — a critical bug.

**Verify after implementing:**  
Two simultaneous requests must each get their own session. An error in one request must not roll back changes in the other.

### 6.3 Repository Pattern

Each repository class:
- Takes `AsyncSession` as constructor argument
- Owns all queries for its table
- Returns typed Python objects (not raw rows)
- Never contains business logic

Routes → Service → Repository → Database  
Routes never touch the database directly.

---

## 6.4 src/core/enums.py — Content

This is the first file you create. It defines all Python enums used across models and business logic.

**Enums to define:**

| Enum | Values | Used by |
|---|---|---|
| `StartupStage` | IDEA, MVP, TRACTION, GROWTH | Startup model |
| `MessageRole` | USER, ASSISTANT, SYSTEM | Message model |
| `MemoryType` | startup_fact, preference, decision, goal, constraint | Memory model |
| `DocumentStatus` | UPLOADED, PROCESSING, READY, FAILED | Document model (SP-04) |
| `WorkflowStatus` | QUEUED, RUNNING, COMPLETED, FAILED | Workflow model (SP-06) |

**Rules:**
- All enums use `str, Enum` inheritance — this makes them JSON-serializable automatically
- Values must exactly match what the database stores
- Import from `src/core/enums.py` everywhere — never redefine the same enum in another file

---

## 7. Alembic Migration System

### 7.1 🔴 ADVANCED — Configuring env.py for Async Engine

After running `alembic init alembic`, open `alembic/env.py`. This file must be modified to:

1. **Import your Base metadata:**  
   Add import of `Base` from `src/repositories/base.py`. Set `target_metadata = Base.metadata`. Without this, `--autogenerate` cannot detect your models.

2. **Use async engine for migrations:**  
   Alembic's default `run_migrations_online()` function uses a sync engine. Replace it with an async version using `asyncio.run()` wrapping an async function that creates an `AsyncEngine` from your `DATABASE_URL`.

3. **Read DATABASE_URL from environment:**  
   Use `os.environ["DATABASE_URL"]` or load from `.env` with `python-dotenv` inside `env.py`. Never hardcode the connection string.

**What must be in env.py after configuration:**
- `target_metadata` set to `Base.metadata`
- `asyncio.run()` wrapping the migration function
- `AsyncEngine` created from `DATABASE_URL`
- All model files imported so SQLAlchemy registers them with Base

**Common mistake:**  
Forgetting to import your model files in `env.py`. Alembic discovers tables through SQLAlchemy's model registry. If a model file is never imported, its table is invisible to autogenerate — even if `target_metadata` is set correctly.

**Verify after configuring:**  
Run `alembic revision --autogenerate -m "initial"`. The generated file must contain `create_table` operations for all 5 tables. If it shows empty `upgrade()` and `downgrade()` functions, your models are not being imported.

### What each command does

| Command | What it does |
|---|---|
| `alembic init alembic` | Creates alembic directory + config files — run once |
| `alembic revision --autogenerate -m "description"` | Inspects your models, generates a migration file showing what changed |
| `alembic upgrade head` | Applies all pending migrations to the actual database |
| `alembic downgrade base` | Reverses all migrations — database returns to empty |
| `alembic downgrade -1` | Reverses only the last migration |
| `alembic current` | Shows which migration the database is currently at |

### Migration workflow

```mermaid
flowchart LR
    A[Edit SQLAlchemy model] --> B[alembic revision --autogenerate]
    B --> C[Review generated file]
    C --> D{Correct?}
    D -->|Yes| E[alembic upgrade head]
    D -->|No| F[Edit migration file manually]
    F --> E
    E --> G[Test upgrade + downgrade]
```

### Migration safety rules

- Every migration must have a working `downgrade()` function — test it
- Never mix model changes and business logic changes in one migration
- Always review autogenerated files before running — autogenerate can miss things
- One logical change per migration file
- Never edit a migration file that has already been applied to a real database

### Configuration requirement

Alembic's `env.py` must import your `Base.metadata` so autogenerate can detect model changes. It must also use your async engine, not a sync one.

---

## 8. File Map

| Order | File | Status | Action | Responsibility | Depends On |
|---|---|---|---|---|---|
| 1 | `src/core/enums.py` | NEW | Create | All enum definitions | Nothing |
| 2 | `src/repositories/base.py` | NEW | Create | Base + TimestampMixin | enums.py |
| 3 | `src/repositories/models/user.py` | NEW | Create | User model | base.py |
| 4 | `src/repositories/models/startup.py` | NEW | Create | Startup model | base.py, enums.py |
| 5 | `src/repositories/models/conversation.py` | NEW | Create | Conversation model | base.py |
| 6 | `src/repositories/models/message.py` | NEW | Create | Message model | base.py |
| 7 | `src/repositories/models/memory.py` | NEW | Create | Memory model | base.py, enums.py |
| 8 | `src/infrastructure/database/engine.py` | NEW | Create | Async engine + sessionmaker | settings.py |
| 9 | `src/infrastructure/database/session.py` | NEW | Create | get_db() dependency | engine.py |
| 10 | `alembic/` | NEW | Init + configure | Migration management | all models |
| 11 | `alembic/versions/001_initial.py` | NEW | Generate | First migration | all models |
| 12 | `src/repositories/user_repository.py` | NEW | Create | User DB operations | models, session |
| 13 | `src/repositories/startup_repository.py` | NEW | Create | Startup DB operations | models, session |
| 14 | `src/repositories/conversation_repository.py` | NEW | Create | Conversation DB operations | models, session |
| 15 | `src/repositories/message_repository.py` | NEW | Create | Message DB operations + sequence | models, session |
| 16 | `src/repositories/memory_repository.py` | NEW | Create | Memory DB operations | models, session |
| 17 | `tests/conftest.py` | NEW | Create | Shared pytest fixtures, test DB setup | engine.py |
| 18 | `tests/integration/test_repositories.py` | NEW | Create | All repository tests | conftest.py, repositories |

**New dependencies to add to requirements.txt:**
```
sqlalchemy[asyncio]>=2.0
alembic>=1.13
asyncpg>=0.29
pytest>=8.0
pytest-asyncio>=0.23
```

**Phase 5 files — DO NOT MODIFY:**
```
src/agents/         → all agent files untouched
src/tools/          → all tool files untouched
src/rag/            → untouched until SP-05
src/prompts/        → untouched
workflow_state.py   → untouched
```

---

## 9. Repository Responsibilities

### UserRepository
- `create(email, password_hash)` → User
- `get_by_id(user_id)` → User or None
- `get_by_email(email)` → User or None
- `delete(user_id)` → None
- Constraint: email uniqueness enforced at DB level — catch IntegrityError

### StartupRepository
- `create(owner_id, name, description, stage)` → Startup
- `get_by_id(startup_id)` → Startup or None
- `get_by_id_and_owner(startup_id, owner_id)` → Startup or None ← used for auth
- `list_by_owner(owner_id, page, page_size)` → list[Startup], total
- `update(startup_id, fields)` → Startup
- `delete(startup_id)` → None (cascades at DB level)

### ConversationRepository
- `create(startup_id, title)` → Conversation
- `get_by_id(conversation_id)` → Conversation or None
- `list_by_startup(startup_id, page, page_size)` → list[Conversation], total
- `update(conversation_id, title)` → Conversation
- `delete(conversation_id)` → None (cascades messages at DB level)

### MessageRepository
- `append(conversation_id, role, content)` → Message ← uses SELECT FOR UPDATE
- `list_by_conversation(conversation_id, page, page_size)` → list[Message], total
- Messages are append-only: no update, no delete operations

### MemoryRepository
- `create(startup_id, memory_type, content, importance)` → Memory
- `list_by_startup(startup_id, page, page_size)` → list[Memory], total
- `delete(memory_id)` → None
- `get_by_id(memory_id)` → Memory or None

---

## 10. Testing

Run tests with `pytest tests/integration/ -v` after setting `DATABASE_URL` to a test database.

| Test | What to do | Expected result |
|---|---|---|
| DB connection | Run `SELECT 1` via async session | Returns without error |
| Table creation | `alembic upgrade head` on fresh DB | All 5 tables exist |
| Migration downgrade | `alembic downgrade base` | All tables removed cleanly |
| Create user | Insert user with valid email | User returned with UUID assigned |
| Duplicate email | Insert two users with same email | IntegrityError raised |
| Create startup | Insert startup for existing user | Startup returned with owner_id set |
| Cascade delete | Delete startup | Conversations + messages + memories also deleted |
| Append message | Insert first message to conversation | sequence_number = 1 |
| Append second message | Insert second message | sequence_number = 2 |
| Concurrent messages | 10 simultaneous inserts to same conversation | sequence numbers 1–10, no duplicates, no gaps |
| FK violation | Insert startup with non-existent owner_id | IntegrityError raised |
| Cross-owner access | get_by_id_and_owner with wrong owner | Returns None |
| Pagination | Insert 25 messages, list page 1 size 10 | Returns 10 items, total = 25 |

---

## NOT IN THIS SUBPHASE

- Redis — SP-02
- ChromaDB — SP-02
- FastAPI routes — SP-03
- JWT / Auth — SP-03
- PDF upload — SP-04
- Memory extraction — SP-05
- RAG pipeline — SP-05
- Any agent modifications — SP-06
- Any modifications to Phase 5 files

---

## SUBPHASE VALIDATION GATE

**Required files completed:**
- [ ] `src/core/enums.py`
- [ ] `src/repositories/base.py`
- [ ] All 5 model files
- [ ] `src/infrastructure/database/engine.py`
- [ ] `src/infrastructure/database/session.py`
- [ ] `alembic/` configured with async engine
- [ ] Migration `001_initial.py` generated and reviewed
- [ ] All 5 repository files

**Required behavior:**
- [ ] `alembic upgrade head` completes on fresh database
- [ ] `alembic downgrade base` completes from head
- [ ] All 5 tables exist with correct columns
- [ ] All foreign key constraints enforced
- [ ] CASCADE DELETE verified end-to-end

**Required tests passing:**
- [ ] All repository CRUD tests pass
- [ ] Concurrent message insert test: 10 inserts, 10 unique sequence numbers
- [ ] Cascade delete test passes
- [ ] Migration round-trip test passes

**Failure conditions:**
- Any test fails → do not move to SP-02
- `alembic downgrade base` fails → fix migration before moving on
- Concurrent sequence number test produces duplicates → fix SELECT FOR UPDATE logic

**Freeze criteria:**  
All checkboxes above checked. Zero test failures.  
PASS → freeze SP-01 → move to SP-02.
