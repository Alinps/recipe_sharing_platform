# Recipe Sharing Platform API

A Django REST API for sharing recipes, managing user profiles, saving favorites (wishlist), and getting cooking assistance through a chatbot endpoint.

## Overview

This project provides a token-authenticated backend for a recipe sharing application.  
It includes:
- User signup, login, logout, and password change
- Recipe create, list, detail, update, delete, and search
- Profile management with image upload
- Wishlist add/remove and user wishlist retrieval
- Health check endpoint
- Request logging and global rate limiting middleware

## Tech Stack

- Python
- Django 5
- Django REST Framework
- Token Authentication (`rest_framework.authtoken`)
- PostgreSQL support via `dj-database-url` and `psycopg2-binary`
- Cloudinary (image storage)
- WhiteNoise (static files)
- Gunicorn (deployment server)

## Project Structure

```text
.
├── app/
│   ├── models.py
│   ├── serializers.py
│   ├── urls.py
│   ├── views.py
│   └── utils/pagination.py
├── recipe_sharing_platform/
│   ├── settings.py
│   ├── urls.py
│   ├── middlewares/
│   │   ├── logging_middleware.py
│   │   └── rate_limit.py
│   └── wsgi.py
├── manage.py
└── requirements.txt
```

## Quick Start

### 1. Create and activate a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

Create a `.env` file (or export vars in your shell):

```env
SECRET_KEY=your-secret-key
DEBUG=True
DATABASE_URL=postgresql://user:password@host:port/dbname
ALLOWED_HOSTS=127.0.0.1,localhost
CORS_ALLOWED_ORIGINS=http://127.0.0.1:3000,http://localhost:3000
CSRF_TRUSTED_ORIGINS=http://127.0.0.1:3000,http://localhost:3000

CLOUDINARY_CLOUD_NAME=your-cloud-name
CLOUDINARY_API_KEY=your-api-key
CLOUDINARY_API_SECRET=your-api-secret
```

### 4. Apply migrations

```bash
python3 manage.py migrate
```

### 5. Create admin user (optional)

```bash
python3 manage.py createsuperuser
```

### 6. Run the development server

```bash
python3 manage.py runserver
```

## Authentication

The API uses DRF token authentication.

- Obtain token: `POST /login_user/`
- Use token header for protected routes:

```http
Authorization: Token <your_token>
```

## API Endpoints

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/signup/` | No | Register a new user |
| POST | `/login_user/` | No | Login and receive token |
| POST | `/logout/` | Yes | Logout (token invalidation) |
| POST | `/create/` | Yes | Create a recipe |
| GET | `/list/` | Yes | List recipes (supports pagination/search) |
| GET | `/recipedetails/<id>` | Yes | Get recipe details |
| DELETE | `/delete/<id>` | Yes | Delete recipe (owner only) |
| GET | `/search/?qtitle=<query>` | Yes | Search by recipe title |
| PUT | `/update/` | Yes | Update recipe fields |
| POST | `/password_change/` | Yes | Change account password |
| POST | `/chat/` | Yes | Cooking assistant chatbot |
| GET | `/profile/<user_id>/` | Yes | Get public user profile + recipes |
| GET | `/profile/<user_id>/wishlist/` | Yes | Get user wishlist recipes |
| POST | `/wishlist/toggle/` | Yes | Add/remove recipe in wishlist |
| GET, PATCH | `/profile/edit/` | Yes | View/update own profile |
| GET | `/health_check/` | No | Service health endpoint |

## Pagination

`/list/` uses limit-offset pagination:
- Default limit: `25`
- Max limit: `100`

Query parameters:
- `limit`
- `offset`
- `search` (title/ingredients filter)

## Logging and Rate Limiting

- Request/response logging middleware is enabled for API observability.
- Application logs are written to rotating file logs (`app.log` with backups).
- Global rate limit middleware:
  - Authenticated users: `100` requests per minute
  - Anonymous users (IP based): `30` requests per minute

## Production Notes

- Static files are served with WhiteNoise.
- Recommended Gunicorn command:

```bash
gunicorn recipe_sharing_platform.wsgi:application
```

## Current Test Status

`app/tests.py` is present but currently minimal. Add API and serializer tests before production deployment.
