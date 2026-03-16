# WP-Replacement — Self-hosted Blog Admin Portal

A secure, modern replacement for the WordPress admin interface. The backend speaks
directly to your **existing WordPress MySQL database** — no data migration needed.

```
┌─────────────────────────────────────────────────────┐
│   React 19 Admin Portal  (port 5173 / 3000)         │
│   • Posts  • Pages  • Media  • Categories  • Tags   │
│   • Comments  • Users  • Dashboard                  │
└─────────────────────┬───────────────────────────────┘
                      │  REST API (JSON + JWT)
┌─────────────────────▼───────────────────────────────┐
│   FastAPI Backend  (port 8000)                      │
│   • WP-compatible phpass auth                       │
│   • SQLAlchemy → existing WordPress MySQL DB        │
│   • File uploads served as static files             │
└─────────────────────────────────────────────────────┘
         │
         ▼ uses existing tables: wp_posts, wp_users,
           wp_terms, wp_term_taxonomy, wp_postmeta,
           wp_comments, wp_options, wp_usermeta
```

---

## Quick Start

### 1. Configure the backend

```bash
cp backend/.env.example backend/.env
# Edit backend/.env — fill in your MySQL credentials
```

### 2. Run with Docker Compose

```bash
docker compose up --build
```

- Admin portal → http://localhost:3000
- API docs     → http://localhost:8000/api/docs

### 3. Run in development mode

**Backend:**
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # edit .env
uvicorn app.main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev          # → http://localhost:5173
```

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/auth/login` | JSON login, returns JWT |
| POST | `/api/auth/token` | OAuth2 form login |
| GET | `/api/dashboard/stats` | Dashboard statistics |
| GET/POST | `/api/posts` | List / create posts |
| GET/PUT/DELETE | `/api/posts/{id}` | Get / update / delete post |
| GET/POST | `/api/pages` | List / create pages |
| GET/PUT/DELETE | `/api/pages/{id}` | Get / update / delete page |
| GET/POST | `/api/categories` | List / create categories |
| PUT/DELETE | `/api/categories/{id}` | Update / delete category |
| GET/POST | `/api/tags` | List / create tags |
| PUT/DELETE | `/api/tags/{id}` | Update / delete tag |
| GET/POST | `/api/media` | List / upload media |
| PUT/DELETE | `/api/media/{id}` | Update / delete media |
| GET/POST | `/api/comments` | List / create comments |
| PUT/DELETE | `/api/comments/{id}` | Update / delete comment |
| GET | `/api/users` | List users (admin only) |
| GET/PUT | `/api/users/me` | Get / update current user |
| GET | `/api/health` | Health check |

Full interactive docs: **http://localhost:8000/api/docs**

---

## Architecture Notes

- **Authentication**: Verifies existing WordPress `$P$` phpass hashes natively.
  New passwords are stored as bcrypt (`$2b$`). Both formats work transparently.
- **WordPress table prefix**: Configurable via `WP_TABLE_PREFIX` in `.env` (default `wp_`).
- **Media uploads**: Files are saved in `backend/uploads/YYYY/MM/` matching the
  WordPress uploads structure. Served at `/wp-content/uploads/`.
- **Flutter / Mobile**: The API only uses JWT bearer tokens and JSON — full
  compatibility with any HTTP client including Dio in Flutter.
- **Static site generator**: Your existing static site generator continues to
  read from the same WordPress MySQL DB unchanged. **https://github.com/wanleung/wp-static**

---

## Security

- All write endpoints require JWT authentication.
- Role-based access: `administrator` and `editor` roles can create/edit/delete.
  Regular users can read only.
- File uploads are validated by MIME type and limited to 50 MB.
- No PHP, no WordPress attack surface.

---

## Author

**Wan Leung Wong** — <me at wanleung dot com> — <https://github.com/wanleung>

---

## License

Copyright (C) 2026 Wan Leung Wong <http://www.wanleung.com>

This program is free software: you can redistribute it and/or modify it under
the terms of the **GNU General Public License version 3 or later** as published
by the Free Software Foundation.

This program is distributed in the hope that it will be useful, but **without
any warranty**; without even the implied warranty of merchantability or fitness
for a particular purpose. See the [LICENSE](LICENSE) file for the full text.
