<!-- Copilot instructions for MicroBlogHub -->
# MicroBlogHub — AI coding assistant quick guide

Purpose: give an AI coding agent the minimal, actionable context to be productive in this Django repository.

- **Big picture**: single-service Django web app. Core logic lives in the `core` app. The project uses Django templates + server-rendered HTML (no SPA). Key flows: users -> posts -> likes/comments/follows. See routes in [microblog_project/core/urls.py](microblog_project/core/urls.py#L1-L40) and main entry [microblog_project/microblog_project/urls.py](microblog_project/microblog_project/urls.py#L1-L30).

- **Where to look first**:
  - App entrypoints: [microblog_project/manage.py](microblog_project/manage.py#L1) and [microblog_project/microblog_project/settings.py](microblog_project/microblog_project/settings.py#L1-L120).
  - Core logic: [microblog_project/core/views.py](microblog_project/core/views.py#L1-L40) (feed, search, profile, like/unlike, follow/unfollow).
  - Templates: [microblog_project/templates/](microblog_project/templates)
  - Static files: [microblog_project/static/](microblog_project/static)
  - Migrations: [microblog_project/core/migrations/](microblog_project/core/migrations)

- **Important structural details (discoverable patterns)**:
  - Single app `core` handles posts, likes, comments, follows (models in `core/models.py`). Views rely heavily on `select_related` and `annotate` to avoid N+1 queries (see `home()` and `search()` in `core/views.py`). When editing queries, preserve `select_related('user')` and `annotate(like_count=Count('like'))` patterns.
  - Trending hashtags are computed in views by scanning a limited recent set (`Post.objects.order_by('-created_at')[:500]`) to reduce work; keep that limit or implement a dedicated cache if changing the approach.
  - Authentication uses Django auth and view-level `@login_required`. Login URL is configured in settings (`LOGIN_URL`, `LOGIN_REDIRECT_URL`).
  - Settings load environment via `python-dotenv` and use `dj_database_url.parse()` for `DATABASES` — the current `settings.py` contains a remote Postgres URL. Check environment variables before switching DBs.

- **Developer workflows / commands** (Windows dev + repository layout):
  - Create venv and install deps (if `requirements.txt` exists):
```bash
python -m venv venv
venv\Scripts\activate
pip install -r microblog_project/requirements.txt
```
  - Common Django commands (run from `microblog_project/`):
```bash
# run dev server
python manage.py runserver

# apply migrations
python manage.py migrate

# create admin
python manage.py createsuperuser

# run tests
python manage.py test

# collect static for production
python manage.py collectstatic --noinput
```
  - Environment variables: `DJANGO_SECRET_KEY` (settings reads it), and `DATABASE_URL` style values are parsed by `dj_database_url`. There's also `python-dotenv` usage — `.env` files are expected if present.

- **Project-specific conventions**:
  - Templates are placed under `microblog_project/templates/` with app-specific templates in `templates/core/` (e.g., profile page: [microblog_project/templates/core/profile.html](microblog_project/templates/core/profile.html)).
  - Views often prepare extra attributes for template convenience (e.g., `p.tags = ...` in `search()`); follow that pattern when adding view-side helpers.
  - Mutating actions (delete) enforce POST-only deletes in views (see `delete_post`), follow the same safety patterns on new destructive endpoints.

- **Integration & external deps**:
  - `dj_database_url` used to parse DB URLs.
  - `python-dotenv` loads env vars.
  - No external 3rd-party APIs discovered in code; most integration points are DB and Django admin.

- **Small examples to follow**:
  - Use `select_related('user')` + `annotate(like_count=Count('like'))` in list queries to avoid N+1 and to compute badges shown in templates (see [core/views.py#home](microblog_project/core/views.py#L1-L60)).
  - For following/unfollowing, views use `get_or_create` and `delete()` patterns to be idempotent (see `follow_user` / `unfollow_user`).

- **When changing DB or secrets**: modify environment variables, not `settings.py` hardcoded values. `settings.py` already uses `load_dotenv()` and `dj_database_url.parse()` — update `.env` or CI secrets.

- **What to avoid**:
  - Don’t remove the limited-scan heuristics for trending (`[:500]`) without adding caching — it was added for performance.
  - Avoid returning raw QuerySets to templates without `select_related` for objects that access `user`.

- **If you need more**: ask for specifics — tests, CI, or deployment steps I should expand on.
