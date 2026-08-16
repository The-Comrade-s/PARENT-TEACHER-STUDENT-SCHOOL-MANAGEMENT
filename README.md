# Parent-Teacher Communication and Student Monitoring System (PTMS)

Pure Python + Streamlit rebuild of the original Next.js/FastAPI project. No
Next.js, React, TypeScript, FastAPI, Flask, Django, Node.js, or any framework
outside the Python/Streamlit stack is used anywhere in this codebase.

Status: all seven build phases complete (PTMS-001 through PTMS-007).

## What is included

**PTMS-001 -- Foundation**
Project structure, SQLAlchemy models for RBAC (User/Role/Permission,
AuditLog), school setup, and student/parent/teacher profiles. Bcrypt password
hashing, login with lockout after repeated failures, session-timeout
handling, role-based access control enforced both in navigation and inside
every page. Parent and teacher registration (teacher accounts start pending
admin approval; the class selector loads active classes live from the
database). Role-aware dashboards. Deep blue / off-white / black visual
identity, zero emoji anywhere in the codebase.

**PTMS-002 -- School setup and people management**
Full CRUD for school profile, academic sessions/terms, departments, classes,
and subjects. Teacher approval workflow. The class-teacher relationship has
a single source of truth (`SchoolClass.class_teacher_id`) managed entirely
through `services/teacher_service.py`, which always clears the previous
class-teacher link before writing a new one -- this directly fixes the
class-assignment bug called out in the original project brief. Full student,
parent, and teacher management screens, including parent-child linking.

**PTMS-003 -- Attendance, assignments, grading, report cards**
Attendance taking with per-date locking/reopening and class/student
summaries. Assignment creation, submission, and teacher review. Configurable
grading (grade bands and CA/exam weighting are database-driven, not
hardcoded) with a draft -> submitted -> published workflow. PDF report cards
generated directly in Python with reportlab, downloadable by students and
parents.

**PTMS-004 -- Behaviour, messaging, notifications, meetings**
Positive/negative behaviour records with resolution tracking and optional
parent notification. Internal messaging (conversations, search, archive)
between teachers, parents, and admins -- no external chat provider.
Persistent notifications and role-targeted announcements. Parent-teacher
meeting requests and status tracking, plus PTA meetings with recorded
minutes.

**PTMS-005 -- Security and audit**
Student check-in/check-out, pickup authorization with one-time PIN
verification, visitor registration and checkout, incident reporting with
severity/status tracking, student movement logging (out-and-back during the
day), and emergency alerts restricted to admin roles. A full audit log
records logins, approvals, assignments, and key administrative actions, with
a searchable/filterable admin viewer.

**PTMS-006 -- Reporting, settings, search**
CSV and Excel exports for students and class results, with export history.
System settings as a key-value store (maintenance mode, password policy,
self-registration toggles) plus a system health snapshot. Global search
across students, teachers, parents, classes, and subjects.

**PTMS-007 -- Hardening and delivery**
Centralized input validators (`utils/validators.py`) used alongside each
service's own checks -- Streamlit widget constraints are never the only line
of defense. A safe-error wrapper (`utils/error_handling.py`) so raw SQL
errors, stack traces, or file paths are never shown to end users; app
startup is wrapped so a configuration/database problem shows one plain
message instead of crashing. A pytest suite covering auth, the
teacher-class-assignment fix, people management, attendance locking,
grading/publishing, and the security module, run against an isolated
in-memory SQLite database. Deployment config (`Procfile`,
`.streamlit/config.toml`, `.streamlit/secrets.toml.example`). A final
project-wide emoji sweep confirming zero emoji characters anywhere.

## Running locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

By default the app uses a local SQLite file (`ptms_local.db`) and seeds a
default super admin:

- Email: `admin@ptms.local`
- Password: `ChangeMe123!`

Change these immediately via environment variables or
`.streamlit/secrets.toml` (copy `.streamlit/secrets.toml.example` and fill
in real values -- that file is git-ignored and must never be committed):

```
DATABASE_URL=postgresql://user:password@host:5432/dbname
SECRET_KEY=replace-with-a-random-value
DEFAULT_ADMIN_EMAIL=your-admin@example.com
DEFAULT_ADMIN_PASSWORD=a-strong-password
```

## Running tests

```bash
pip install -r requirements.txt -r requirements-dev.txt
pytest
```

Tests run against an isolated in-memory SQLite database (see
`tests/conftest.py`) and never touch a real deployment's data.

## Deployment

- **Render / any Procfile platform**: the included `Procfile` runs
  `streamlit run app.py` bound to `$PORT`. Set `DATABASE_URL` and the other
  secrets above as environment variables in the platform's dashboard.
- **Streamlit Community Cloud**: point it at `app.py`; add the same values
  under the app's Secrets settings using the TOML format shown in
  `.streamlit/secrets.toml.example`.
- Docker is intentionally not included, per the project's technology
  constraints, unless a specific deployment target requires it.

## Project structure

```
parent_teacher_system/
    app.py                   Entry point, startup, role-aware navigation
    config/settings.py       Env/secrets-driven configuration
    database/connection.py   Engine, session factory, table creation
    models/                  SQLAlchemy models, one module per domain
    auth/                    Password hashing, session/auth state
    permissions/rbac.py      Role and permission checks
    services/                All business logic, one module per domain
    pages/                   Streamlit pages, grouped by role
    components/              Shared UI building blocks (cards, messaging UI)
    reports/report_card.py   PDF report card generation
    utils/                   Validators and error-handling helpers
    assets/styles.css        Deep blue / off-white theme
    tests/                   Pytest suite
    .streamlit/               Theme config and secrets template
```

## Known limitations of this delivery

This project was built and verified in an offline sandbox with no package
registry access, so it could not be `pip install`-ed and run live end to end
here. Every file was verified with `python3 -m py_compile` (syntax-clean),
a project-wide emoji sweep (zero found), and a manual trace of each
service's call signatures against its test suite and callers. Please run
`pip install -r requirements.txt && streamlit run app.py` in a normal
environment and report anything that surfaces -- a runtime issue that only
appears with real package versions installed is the most likely remaining
gap.
