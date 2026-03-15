# WP-Replacement — Technical Documentation

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Why This Exists](#2-why-this-exists)
3. [Architecture](#3-architecture)
4. [Project Structure](#4-project-structure)
5. [Backend (FastAPI)](#5-backend-fastapi)
   - 5.1 [Configuration & Environment](#51-configuration--environment)
   - 5.2 [Database Layer](#52-database-layer)
   - 5.3 [Models (WordPress Tables)](#53-models-wordpress-tables)
   - 5.4 [Authentication & Security](#54-authentication--security)
   - 5.5 [API Routers](#55-api-routers)
   - 5.6 [Schemas (Pydantic)](#56-schemas-pydantic)
   - 5.7 [File Uploads](#57-file-uploads)
6. [Frontend (React 19.2)](#6-frontend-react-192)
   - 6.1 [Tech Stack](#61-tech-stack)
   - 6.2 [Routing](#62-routing)
   - 6.3 [Auth State](#63-auth-state)
   - 6.4 [API Client Layer](#64-api-client-layer)
   - 6.5 [Pages & Components](#65-pages--components)
7. [REST API Reference](#7-rest-api-reference)
8. [Data Flow](#8-data-flow)
9. [Role & Permission Model](#9-role--permission-model)
10. [WordPress Compatibility](#10-wordpress-compatibility)
11. [Mobile / Flutter Readiness](#11-mobile--flutter-readiness)
12. [Deployment](#12-deployment)
13. [Security Considerations](#13-security-considerations)
14. [Future Extensibility](#14-future-extensibility)

---

## 1. Project Overview

**WP-Replacement** is a self-hosted blog admin portal that replaces the WordPress
dashboard with a modern, secure interface. It consists of:

- A **Python/FastAPI REST API** that reads and writes directly to the existing
  WordPress MySQL database.
- A **React 19.2 web admin portal** that consumes the REST API and provides a full
  blog-management experience.

The original WordPress PHP application is completely removed from the request path.
Only the MySQL database is retained. The existing static site generator that already
reads from the WordPress DB continues to work without any changes.

---

## 2. Why This Exists

WordPress PHP has a large attack surface (plugin vulnerabilities, XML-RPC exploits,
`wp-login.php` brute-force attacks, etc.). This project provides a drop-in replacement
using a narrower, purpose-built backend that:

- Exposes **only** the endpoints that are actually needed.
- Uses JWT-based authentication instead of WordPress cookie sessions.
- Validates all input with strict Pydantic schemas.
- Stores new passwords with bcrypt, while still verifying existing WordPress `$P$`
  phpass hashes (so no forced password reset on migration day).
- Applies MIME-type validation and file-size limits on every upload.

---

## 3. Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│  Browser / Mobile App / Flutter                                  │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  React 19.2 Admin Portal  (Vite, Tailwind, TanStack Query) │  │
│  │  http://localhost:5173  (dev)  |  http://localhost:3000    │  │
│  └───────────────────────┬────────────────────────────────────┘  │
│                          │  HTTP/JSON  +  Bearer JWT             │
└──────────────────────────┼───────────────────────────────────────┘
                           │
          ┌────────────────▼────────────────────┐
          │  FastAPI Backend                    │
          │  http://localhost:8000              │
          │                                     │
          │  /api/auth         → JWT issue      │
          │  /api/posts        → CRUD           │
          │  /api/pages        → CRUD           │
          │  /api/categories   → CRUD           │
          │  /api/tags         → CRUD           │
          │  /api/media        → upload/list    │
          │  /api/comments     → moderate       │
          │  /api/users        → manage         │
          │  /api/dashboard    → stats          │
          │                                     │
          │  /wp-content/uploads  → static      │
          └────────────────┬────────────────────┘
                           │  SQLAlchemy ORM
                           │
          ┌────────────────▼────────────────────┐
          │  Existing WordPress MySQL Database  │
          │                                     │
          │  wp_users         wp_usermeta       │
          │  wp_posts         wp_postmeta       │
          │  wp_terms         wp_term_taxonomy  │
          │  wp_term_relationships              │
          │  wp_comments      wp_commentmeta    │
          │  wp_options                         │
          └─────────────────────────────────────┘
                           │
          ┌────────────────▼────────────────────┐
          │  Existing Static Site Generator     │
          │  (unchanged — still reads same DB)  │
          └─────────────────────────────────────┘
```

---

## 4. Project Structure

```
wp-replacement/
├── docker-compose.yml          # Runs backend + frontend together
├── README.md                   # Quick-start guide
├── DOCUMENTATION.md            # This file
│
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── .env.example            # Copy to .env and fill in credentials
│   └── app/
│       ├── main.py             # FastAPI app entry point
│       ├── config.py           # Pydantic settings (reads .env)
│       ├── database.py         # SQLAlchemy engine + session factory
│       ├── dependencies.py     # FastAPI dependency injection (auth guards)
│       ├── core/
│       │   └── security.py     # phpass verification, bcrypt, JWT
│       ├── models/
│       │   ├── user.py         # WPUser, WPUserMeta
│       │   ├── post.py         # WPPost, WPPostMeta
│       │   ├── term.py         # WPTerm, WPTermTaxonomy, WPTermRelationship
│       │   ├── comment.py      # WPComment, WPCommentMeta
│       │   └── option.py       # WPOption
│       ├── schemas/
│       │   ├── user.py         # UserCreate/Update/Out, TokenResponse
│       │   ├── post.py         # PostCreate/Update/Out, PostListOut
│       │   ├── term.py         # CategoryCreate, TagCreate, TermOut
│       │   ├── comment.py      # CommentCreate/Update/Out
│       │   └── media.py        # MediaOut, MediaUpdate
│       └── routers/
│           ├── auth.py         # POST /auth/login, /auth/token
│           ├── posts.py        # CRUD /posts
│           ├── pages.py        # CRUD /pages
│           ├── taxonomy.py     # CRUD /categories, /tags
│           ├── media.py        # Upload/list/delete /media
│           ├── comments.py     # List/moderate/delete /comments
│           ├── users.py        # /users, /users/me
│           ├── dashboard.py    # GET /dashboard/stats
│           └── _post_helpers.py # Shared create/update/delete logic for posts+pages
│
└── frontend/
    ├── Dockerfile
    ├── nginx.conf              # Nginx config for production container
    ├── package.json
    ├── vite.config.ts          # Vite + path alias @/ → src/
    ├── tsconfig.json
    ├── tailwind.config.js
    ├── postcss.config.js
    └── src/
        ├── main.tsx            # React root, QueryClient, Toaster
        ├── App.tsx             # BrowserRouter + route definitions
        ├── index.css           # Tailwind base + custom component classes
        ├── types/
        │   └── index.ts        # Shared TypeScript interfaces
        ├── store/
        │   └── authStore.ts    # Zustand store (token + user, persisted)
        ├── api/
        │   ├── client.ts       # Axios instance, JWT interceptor, 401 handler
        │   ├── auth.ts         # login(), getMe(), updateMe()
        │   ├── posts.ts        # list/get/create/update/delete posts & pages
        │   ├── taxonomy.ts     # categories and tags API calls
        │   ├── media.ts        # upload/list/update/delete media
        │   └── dashboard.ts    # getStats()
        ├── components/
        │   ├── Layout.tsx      # Sidebar + topbar shell
        │   ├── ProtectedRoute.tsx # Redirects to /login if not authenticated
        │   ├── RichEditor.tsx  # TipTap WYSIWYG editor component
        │   └── Spinner.tsx     # Loading spinner
        └── pages/
            ├── Login.tsx       # Login form
            ├── Dashboard.tsx   # Stats cards + recent posts
            ├── PostsList.tsx   # Posts/Pages table with search + pagination
            ├── PostEditor.tsx  # Create/edit post with rich editor
            ├── MediaLibrary.tsx# Drag-and-drop upload + grid browser
            ├── TermManager.tsx # Category / Tag inline CRUD
            ├── CommentsPage.tsx# Comment moderation
            └── UsersPage.tsx   # User listing (admin only)
```

---

## 5. Backend (FastAPI)

### 5.1 Configuration & Environment

All settings live in `backend/.env` (copy from `.env.example`):

| Variable | Default | Description |
|---|---|---|
| `DB_HOST` | `localhost` | MySQL host |
| `DB_PORT` | `3306` | MySQL port |
| `DB_USER` | `wordpress` | MySQL username |
| `DB_PASSWORD` | _(required)_ | MySQL password |
| `DB_NAME` | `wordpress` | Database name |
| `WP_TABLE_PREFIX` | `wp_` | WordPress table prefix |
| `JWT_SECRET_KEY` | _(change this!)_ | Secret used to sign JWTs |
| `JWT_ALGORITHM` | `HS256` | JWT signing algorithm |
| `JWT_EXPIRE_MINUTES` | `1440` | Token lifetime (24 hours) |
| `CORS_ORIGINS` | `http://localhost:5173,...` | Comma-separated allowed origins |
| `UPLOAD_DIR` | `./uploads` | Directory where uploaded files are stored |
| `SITE_URL` | `http://localhost:8000` | Used when building attachment GUIDs |

`app/config.py` uses `pydantic-settings` so values are automatically validated and
typed. The `database_url` and `cors_origins_list` are computed properties.

### 5.2 Database Layer

`app/database.py` creates a single SQLAlchemy engine with connection pooling:

```python
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,   # reconnects on stale connections
    pool_recycle=3600,    # recycles connections hourly
    pool_size=10,
    max_overflow=20,
)
```

The `get_db()` generator is used as a FastAPI dependency in every router that
needs database access. It opens a session, yields it, and closes it regardless of
whether the request succeeded.

### 5.3 Models (WordPress Tables)

All models use SQLAlchemy's modern `Mapped` + `mapped_column` typed API. The table
names are prefixed with `settings.WP_TABLE_PREFIX` at module import time, so
non-standard prefixes work correctly.

| Model | Table | Notable relationships |
|---|---|---|
| `WPUser` | `wp_users` | → `WPUserMeta` (one-to-many), → `WPPost` (one-to-many) |
| `WPUserMeta` | `wp_usermeta` | → `WPUser` |
| `WPPost` | `wp_posts` | → `WPPostMeta`, → `WPTermRelationship`, → `WPUser` (author) |
| `WPPostMeta` | `wp_postmeta` | → `WPPost` |
| `WPTerm` | `wp_terms` | → `WPTermTaxonomy` |
| `WPTermTaxonomy` | `wp_term_taxonomy` | → `WPTerm`, → `WPTermRelationship` |
| `WPTermRelationship` | `wp_term_relationships` | → `WPPost`, → `WPTermTaxonomy` |
| `WPComment` | `wp_comments` | → `WPCommentMeta` |
| `WPCommentMeta` | `wp_commentmeta` | → `WPComment` |
| `WPOption` | `wp_options` | standalone |

The `WPUser.capabilities` property parses the `wp_capabilities` usermeta JSON blob
to extract role information without requiring an extra query pattern.

### 5.4 Authentication & Security

**File:** `app/core/security.py`

#### WordPress phpass verification

WordPress stores passwords as `$P$...` (phpass) or legacy 32-char MD5. The
`wp_check_password()` function replicates the phpass algorithm in pure Python:

1. Extract the iteration count from the 4th character of the hash (base64 index).
2. Extract the 8-character salt.
3. Compute `MD5(salt + password)` as the initial hash.
4. Iterate MD5(`previous_hash + password_bytes`) N times.
5. Base64-encode the result and compare against the stored hash.

This means existing WordPress users can log in immediately without any password reset.

#### New password hashing

New passwords (created through this portal or updated via the `/users/me` endpoint)
are stored as bcrypt hashes using `passlib`. bcrypt hashes start with `$2b$` which
are not `$P$` prefixed, so `verify_password()` automatically routes to the correct
verifier based on the hash prefix.

#### JWT

Tokens are issued by `create_access_token(subject=user.ID)` and expire after
`JWT_EXPIRE_MINUTES` (default 24 hours). The subject is the WordPress user `ID`
(integer stored as string per JWT spec).

`decode_access_token()` validates the signature and expiry, returning the user ID
string or `None` if invalid.

**File:** `app/dependencies.py`

Three dependency functions are provided for route protection:

| Dependency | Allows |
|---|---|
| `get_current_user` | Any authenticated user |
| `require_editor` | Users with `administrator` or `editor` capability |
| `require_admin` | Users with `administrator` capability only |

### 5.5 API Routers

#### `routers/auth.py`
- `POST /api/auth/login` — Accepts `{"username": ..., "password": ...}` JSON.
  Returns `{"access_token": "...", "token_type": "bearer", "user": {...}}`.
- `POST /api/auth/token` — OAuth2 `application/x-www-form-urlencoded` form.
  Required by the FastAPI `/api/docs` Swagger UI "Authorize" button.

Both endpoints authenticate by `user_login` OR `user_email`, so users can log in
with either credential.

#### `routers/posts.py` and `routers/pages.py`

Both use shared logic from `routers/_post_helpers.py`. The difference is only the
`post_type` field (`"post"` vs `"page"`).

Key operations:
- **List** — Supports `page`, `per_page`, `status`, `search` query parameters.
  Excludes `auto-draft` and `inherit` status posts (WordPress internal types).
- **Create** — Slugifies the title to produce a URL slug, ensures uniqueness by
  appending `-1`, `-2`, etc. Sets GUID. Assigns term relationships. Sets featured
  image postmeta (`_thumbnail_id`).
- **Update** — Patches only the fields provided (partial update). Re-computes term
  relationships if `category_ids` or `tag_ids` are provided: decrements old term
  counts, deletes old relationships, creates new ones with updated counts.
- **Delete** — Decrements all associated term counts, then deletes the post
  (cascades to postmeta and term relationships via SQLAlchemy).

The `_build_post_out()` function assembles the full response DTO from the ORM
object, resolving the author, categories, tags, and featured image URL.

#### `routers/taxonomy.py`

Manages `wp_terms` + `wp_term_taxonomy` together. A category or tag is actually
two rows: one in `wp_terms` (name, slug) and one in `wp_term_taxonomy` (taxonomy
type, description, parent, count). Both are created/deleted together.

The `count` column is maintained manually: incremented when a term is assigned to
a post, decremented when removed or when the post is deleted.

#### `routers/media.py`

Upload flow:
1. MIME type is validated against an allow-list (`image/*`, `video/*`, `audio/*`,
   `application/pdf`).
2. File is streamed in 1 MB chunks with a 50 MB total limit.
3. The original filename is sanitized (non-alphanumeric characters replaced with `_`).
4. A UUID-based filename is generated to prevent collisions and path traversal.
5. File is saved to `UPLOAD_DIR/YYYY/MM/uuid.ext` matching WordPress's upload structure.
6. For images, a 150×150 thumbnail is generated with Pillow.
7. A `wp_posts` row is created with `post_type = "attachment"` and the file URL as
   `guid`, plus `wp_postmeta` rows for `_wp_attached_file` and `_wp_file_size`.

On delete, the physical files (original + thumbnail) are removed from disk.

#### `routers/comments.py`

- `GET /api/comments?post_id=0` returns all comments (used by the admin panel).
- `GET /api/comments?post_id=123` returns comments for a specific post.
- `comment_approved` values follow WordPress conventions: `"1"` = approved,
  `"0"` = pending, `"spam"` = spam, `"trash"` = trash.
- Creating a comment updates the post's `comment_count` counter.

#### `routers/dashboard.py`

Returns aggregate counts via SQLAlchemy `func.count()` queries in a single
request: published/draft posts, published pages, approved/pending comments,
media count, category count, tag count, and the 5 most recent published posts.

#### `routers/users.py`

- `GET /api/users` — Admin only. Lists all users.
- `GET /api/users/me` — Returns the authenticated user's profile.
- `PUT /api/users/me` — Updates email, display name, URL, or password.
- `POST /api/users` — Admin only. Creates a new user with bcrypt-hashed password.

### 5.6 Schemas (Pydantic)

All request bodies and response shapes are defined as Pydantic v2 models in
`app/schemas/`. Key design decisions:

- Response models include computed/resolved fields (e.g., `PostOut` includes
  `categories: List[TermOut]` and `author: AuthorOut`) that are not direct
  database columns.
- `model_config = {"from_attributes": True}` enables constructing schemas from
  SQLAlchemy ORM objects.
- `PostListOut` wraps items with pagination metadata (`total`, `page`, `per_page`,
  `pages`).

### 5.7 File Uploads

Uploaded files are served as static files by FastAPI's `StaticFiles` mount:

```
/wp-content/uploads  →  backend/uploads/
```

The URL structure matches WordPress (`/wp-content/uploads/YYYY/MM/filename.ext`),
so any existing content references in post bodies continue to resolve correctly
if you previously pointed WordPress uploads at the same directory.

---

## 6. Frontend (React 19.2)

### 6.1 Tech Stack

| Library | Version | Purpose |
|---|---|---|
| React | 19.x | UI framework |
| React Router | 7.x | Client-side routing |
| TanStack Query | 5.x | Server state, caching, background refetching |
| Axios | 1.x | HTTP client |
| Zustand | 5.x | Client state (auth token + user) |
| TipTap | 2.x | WYSIWYG rich text editor |
| Tailwind CSS | 3.x | Utility-first styling |
| react-dropzone | 14.x | Drag-and-drop file upload |
| react-hot-toast | 2.x | Notifications |
| lucide-react | 0.x | Icons |
| date-fns | 4.x | Date formatting |
| Vite | 6.x | Build tool |

### 6.2 Routing

`src/App.tsx` defines the route tree using React Router v7:

```
/login                       → LoginPage (public)
/                            → DashboardPage (protected)
/posts                       → PostsList
/posts/new                   → PostEditor (create)
/posts/:id/edit              → PostEditor (edit)
/pages                       → PostsList (isPages=true)
/pages/new                   → PostEditor (create, page type)
/pages/:id/edit              → PostEditor (edit, page type)
/media                       → MediaLibrary
/categories                  → TermManager (taxonomy="categories")
/tags                        → TermManager (taxonomy="tags")
/comments                    → CommentsPage
/users                       → UsersPage
```

All routes except `/login` are wrapped in `<ProtectedRoute>`, which checks the
Zustand auth store. If no valid token exists, the user is redirected to `/login`.

Protected routes are also wrapped in `<AppLayout>` which renders the sidebar +
topbar shell, with page content in the `<Outlet />`.

### 6.3 Auth State

`src/store/authStore.ts` uses Zustand with localStorage persistence:

```typescript
interface AuthStore {
  token: string | null
  user: User | null
  setAuth: (token, user) => void
  logout: () => void
  isAuthenticated: () => boolean
}
```

On app load, the persisted token is read from `localStorage`. The
`isAuthenticated()` check does a lightweight JWT expiry check client-side before
routing decisions. The full server-side validation happens on every API call.

### 6.4 API Client Layer

`src/api/client.ts` is an Axios instance configured with:

- `baseURL: '/api'` — In dev, Vite proxies `/api` to `http://localhost:8000`.
  In production, Nginx proxies the same path to the backend container.
- **Request interceptor** — Reads the JWT from Zustand store and attaches it as
  `Authorization: Bearer <token>` on every outgoing request.
- **Response interceptor** — On HTTP 401, clears the auth store and redirects to
  `/login`.

Typed API modules (`auth.ts`, `posts.ts`, `taxonomy.ts`, `media.ts`,
`dashboard.ts`) wrap the Axios calls with specific TypeScript return types so all
API data is fully typed throughout the UI.

### 6.5 Pages & Components

#### `Login.tsx`
Simple centered form. Uses `useMutation` from TanStack Query to call
`authApi.login()`, then stores the token via `useAuthStore().setAuth()` and
navigates to `/`.

#### `Dashboard.tsx`
Uses `useQuery` to fetch `/api/dashboard/stats`. Renders 6 stat cards (posts,
pages, media, comments, categories, tags) and a "Recent Posts" table. Each stat
card links to the corresponding section.

#### `PostsList.tsx`
Reusable for both posts and pages (`isPages` prop). Features:
- Search input with debounce-via-state.
- Status dropdown filter.
- Sortable table with columns: title, author, categories (posts only), status, date.
- Pagination controls using `page` state.
- Inline delete with confirmation dialog.

#### `PostEditor.tsx`
Full create/edit experience:
- **Title field** — large, borderless input at the top.
- **Rich editor** — TipTap with a full toolbar: bold/italic/underline/strikethrough,
  H1–H3, lists, blockquote, code, text alignment, link insertion, image insertion
  (by URL), undo/redo.
- **Excerpt** — plain textarea.
- **Sidebar** — Status selector, URL slug field, featured image picker (opens
  media picker modal), category checkboxes, tag badges.
- **Featured image picker** — Modal that loads the media library filtered to
  `image/*` MIME types. Clicking a thumbnail selects it.
- **Save Draft** button always saves with `post_status: "draft"`.
- **Publish/Update** button saves with the currently selected status.

When editing an existing post, `useQuery` fetches the post and a `useEffect`
populates all form state fields once data arrives.

#### `MediaLibrary.tsx`
- `react-dropzone` drop zone at the top accepts images, video, audio, PDF.
- Uploads are streamed with progress reporting (progress bar shown during upload).
- Grid of thumbnails below. Non-image files show a type icon.
- Clicking a thumbnail opens a detail panel on the right showing: preview, file
  name, MIME type, file size, upload date, a "View file" link, and a "Delete" button.
- Pagination for large libraries.

#### `TermManager.tsx`
Split-panel layout: create form on the left, list table on the right. Inline
editing: clicking the edit icon in a row transforms the name and description cells
into text inputs; confirm or cancel with check/X buttons.

#### `CommentsPage.tsx`
Lists all comments from all posts (admin view). Each comment shows the author
avatar (initial letter), name, email, content, approval status badge, and date.
Approve/unapprove and delete are available per comment.

#### `RichEditor.tsx`
Standalone TipTap wrapper component. Accepts `content` (HTML string) and
`onChange` (callback receiving updated HTML). Toolbar buttons use `editor.isActive()`
to show the active state. The placeholder extension shows greyed hint text when
the editor is empty.

#### `Layout.tsx`
Renders a dark sidebar (`bg-gray-900`) with navigation links and user info, plus a
white topbar. On mobile, the sidebar is hidden and revealed by a hamburger button
as a slide-over overlay. The `<Outlet />` content renders in the main area.

---

## 7. REST API Reference

All endpoints require `Authorization: Bearer <token>` except `POST /api/auth/login`
and `POST /api/auth/token`. Optional fields in request bodies can be omitted.

All dates are ISO 8601 strings. All IDs are integers.

### Authentication

```
POST /api/auth/login
Body: { "username": "admin", "password": "secret" }
Returns: { "access_token": "...", "token_type": "bearer", "user": { ... } }

POST /api/auth/token
Body: username=admin&password=secret  (form data)
Returns: same as above
```

### Dashboard

```
GET /api/dashboard/stats
Returns: {
  posts: { published: int, draft: int },
  pages: { published: int },
  comments: { approved: int, pending: int },
  media: int,
  categories: int,
  tags: int,
  recent_posts: [{ ID, post_title, post_date, post_status }]
}
```

### Posts

```
GET  /api/posts?page=1&per_page=20&status=publish&search=hello
GET  /api/posts/{id}
POST /api/posts               (editor+)
PUT  /api/posts/{id}          (editor+)
DELETE /api/posts/{id}        (editor+)
```

Post body fields:
```json
{
  "post_title": "My Post",
  "post_content": "<p>HTML content</p>",
  "post_excerpt": "Short summary",
  "post_status": "draft|publish|private|pending",
  "post_name": "url-slug",
  "comment_status": "open|closed",
  "category_ids": [1, 2],
  "tag_ids": [3],
  "featured_image_id": 42
}
```

### Pages

Same as posts but at `/api/pages`. Pages do not use category/tag assignments.

### Categories

```
GET    /api/categories?search=...
GET    /api/categories/{term_taxonomy_id}
POST   /api/categories   body: { "name": "Tech", "description": "", "parent": 0 }
PUT    /api/categories/{term_taxonomy_id}
DELETE /api/categories/{term_taxonomy_id}
```

### Tags

Same as categories but at `/api/tags`. Tags have no `parent` field.

### Media

```
GET    /api/media?page=1&per_page=20&mime_type=image
GET    /api/media/{id}
POST   /api/media              (multipart/form-data, field name: "file")
PUT    /api/media/{id}   body: { "post_title": "...", "alt_text": "...", "caption": "..." }
DELETE /api/media/{id}
```

### Comments

```
GET    /api/comments?post_id=0&page=1&per_page=20&approved_only=false
POST   /api/comments   body: { "comment_post_ID": 1, "comment_content": "..." }
PUT    /api/comments/{id}   body: { "comment_approved": "1", "comment_content": "..." }
DELETE /api/comments/{id}   (editor+)
```

### Users

```
GET  /api/users         (admin only)
POST /api/users         (admin only)  body: { "user_login": "...", "password": "...", "user_email": "..." }
GET  /api/users/me
PUT  /api/users/me      body: { "display_name": "...", "user_email": "...", "password": "..." }
```

### Health

```
GET /api/health
Returns: { "status": "ok" }
```

---

## 8. Data Flow

### Login flow

```
frontend                    backend                  database
  │                            │                         │
  │  POST /api/auth/login      │                         │
  │──────────────────────────▶ │                         │
  │                            │  SELECT * FROM wp_users │
  │                            │  WHERE user_login=?     │
  │                            │ ───────────────────────▶│
  │                            │◀─────────────────────── │
  │                            │  verify phpass/bcrypt   │
  │                            │  create_access_token()  │
  │◀────────────────────────── │                         │
  │  { access_token, user }    │                         │
  │  store in Zustand + LS     │                         │
```

### Create post flow

```
frontend                    backend                  database
  │                            │                         │
  │  POST /api/posts           │                         │
  │  Authorization: Bearer ... │                         │
  │──────────────────────────▶ │                         │
  │                            │  decode JWT → user ID   │
  │                            │  INSERT INTO wp_posts   │
  │                            │ ───────────────────────▶│
  │                            │  INSERT wp_term_rels    │
  │                            │  UPDATE wp_term_tax     │
  │                            │    (increment counts)   │
  │                            │  INSERT wp_postmeta     │
  │                            │    (_thumbnail_id)      │
  │                            │◀─────────────────────── │
  │◀────────────────────────── │                         │
  │  PostOut (with categories, │                         │
  │   tags, author, image url) │                         │
```

---

## 9. Role & Permission Model

Roles are stored in `wp_usermeta` as a serialised PHP array (or JSON) under the
key `wp_capabilities`. Example value: `{"administrator": true}`.

The `WPUser.capabilities` property parses this into a Python dict. Permission
checks happen in `app/dependencies.py`:

| Endpoint type | Required capability |
|---|---|
| Read (GET) | Any valid JWT |
| Create/Update/Delete post, page, term, media, comment | `administrator` OR `editor` |
| Manage users, create users | `administrator` only |

---

## 10. WordPress Compatibility

This project is designed to be a **write-compatible** replacement for WordPress's
admin interface. The database schema is never altered. Here is what stays compatible:

| Feature | Compatibility |
|---|---|
| Post structure | Full — `wp_posts` schema unchanged |
| User accounts | Full — existing users log in with current passwords |
| Categories & tags | Full — `wp_terms` + `wp_term_taxonomy` maintained correctly |
| Post-category relationships | Full — counts kept in sync |
| Featured images | Full — stored as `_thumbnail_id` postmeta |
| Media library | Full — attachments stored in `wp_posts` with `post_type=attachment` |
| GUID format | Full — `/?p=ID` pattern maintained |
| Comments | Full — standard `wp_comments` schema |
| Options | Read-only access available via `WPOption` model |
| Custom post types | Readable via raw DB queries; not exposed via API by default |
| Multisite | Not supported |
| Plugins | Not applicable (PHP removed) |

---

## 11. Mobile / Flutter Readiness

The API was designed from day one to support mobile clients:

- **Authentication**: Standard `Authorization: Bearer <jwt>` header.
  In Flutter, use the `Dio` package with an interceptor:
  ```dart
  dio.interceptors.add(InterceptorsWrapper(
    onRequest: (options, handler) {
      options.headers['Authorization'] = 'Bearer $token';
      handler.next(options);
    },
  ));
  ```
- **JSON only**: All requests and responses are `application/json` (except file
  uploads which use `multipart/form-data`).
- **CORS**: The `CORS_ORIGINS` setting in `.env` accepts any origin, so a Flutter
  web build or a local dev server can be added easily.
- **No cookies, no sessions**: Stateless — works with any HTTP client on any platform.
- All date fields are ISO 8601 strings, which Dart's `DateTime.parse()` handles natively.

---

## 12. Deployment

### Development

```bash
# Terminal 1 — backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env    # fill in your DB credentials
uvicorn app.main:app --reload --port 8000

# Terminal 2 — frontend
cd frontend
npm install
npm run dev             # http://localhost:5173
```

Vite proxies `/api/*` and `/wp-content/*` to the backend via `vite.config.ts`,
so no CORS issues during development.

### Production (Docker Compose)

```bash
cp backend/.env.example backend/.env
# edit backend/.env

docker compose up --build -d
```

Services:
- **backend** — FastAPI on port 8000, uploads mounted at `./backend/uploads`.
- **frontend** — Nginx on port 3000. Proxies `/api` and `/wp-content` to the
  backend container; serves the built React SPA for all other paths.

To point the frontend at a different backend URL (e.g., separate servers), edit
`frontend/nginx.conf` and rebuild the image.

### Connecting to the existing WordPress database

If WordPress is running on a different server or inside its own Docker network,
set `DB_HOST` in `backend/.env` to the correct host/IP. Ensure the MySQL user has
`SELECT`, `INSERT`, `UPDATE`, `DELETE` privileges on the WordPress database.

---

## 13. Security Considerations

| Concern | Mitigation |
|---|---|
| SQL injection | SQLAlchemy ORM with parameterised queries throughout |
| XSS in post content | Content stored as-is; sanitisation should be applied at the static site generator render layer, not the admin portal |
| CSRF | Not applicable — JWT bearer tokens (not cookies) are used |
| Password storage | Existing: phpass (WordPress compat). New: bcrypt via passlib |
| Brute-force login | Rate limiting can be added via `slowapi` (already in `requirements.txt`); not wired up by default |
| File upload abuse | MIME-type allow-list, 50 MB size cap, UUID filename prevents path traversal |
| Unauthorised access | All non-auth endpoints require a valid, non-expired JWT |
| Privilege escalation | Role checks use capability flags from the DB; cannot be elevated via API |
| Secret key leakage | `JWT_SECRET_KEY` and DB password are only in `.env` (gitignored) |
| CORS | Explicit allow-list via `CORS_ORIGINS`; not `*` |

---

## 14. Future Extensibility

| Feature | Notes |
|---|---|
| Rate limiting | `slowapi` is already in `requirements.txt`. Add `@limiter.limit("5/minute")` decorators to auth endpoints. |
| Refresh tokens | Add a `POST /api/auth/refresh` endpoint and a short-lived access token + long-lived refresh token pair |
| Custom post types | Add a `post_type` query parameter filter to `/api/posts` list endpoint |
| Full-text search | Replace `ILIKE` with MySQL `FULLTEXT` index via `MATCH ... AGAINST` |
| Image resizing | Extend the upload handler to generate multiple Pillow thumbnails (WordPress image size variants) |
| Flutter app | Create a new `mobile/` directory using the same API client. Reuse the API contracts defined in `frontend/src/types/index.ts` |
| Scheduled publishing | Add a background task (APScheduler or Celery) that auto-publishes posts with `post_status = "future"` when `post_date` is reached |
| Audit log | Add a `wp_actionlogs` table + ORM model to record create/update/delete events with user ID, timestamp, and before/after diff |
| Two-factor auth | Add a TOTP step to the login flow using `pyotp`; store the TOTP secret in `wp_usermeta` |
| WebSocket notifications | Add a `/ws/notifications` endpoint for real-time comment/pending-post alerts in the admin portal |
