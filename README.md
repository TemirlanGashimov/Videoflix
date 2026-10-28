# Videoflix Backend

Videoflix is a Django REST API backend for a video streaming application. It provides account registration, activation, login, and password recovery, as well as an authenticated video catalog and HLS playback endpoints. Uploaded videos can be converted into HLS renditions in the background using Redis Queue (RQ) and FFmpeg.

## Contents

- [Features](#features)
- [Prerequisites](#prerequisites)
- [Quickstart](#quickstart)
- [Configuration](#configuration)
- [API overview](#api-overview)
- [Project structure](#project-structure)
- [Tests](#tests)
- [Notes](#notes)
- [Contributing](#contributing)
- [License](#license)

## Features

- Django REST Framework API
- JWT authentication using HTTP-only cookies
- Account activation and password-reset flows
- PostgreSQL database and Redis-backed caching and background jobs
- HLS conversion to 480p, 720p, and 1080p using FFmpeg
- Django admin for managing video records

## Prerequisites

- Docker Desktop (or Docker Engine) with Docker Compose
- Git, if you are cloning the repository

The Docker image installs the Python dependencies and FFmpeg. PostgreSQL and Redis are provided as Compose services.

## Quickstart

Run these commands from the repository root:

1. Create a local environment file:

   ```powershell
   Copy-Item .env.template .env
   ```

2. Edit `.env`. Set unique values for `SECRET_KEY`, `DB_NAME`, `DB_USER`, and `DB_PASSWORD`. Keep the Compose service host values `DB_HOST=db` and `REDIS_HOST=redis`.

3. Build and start the services:

   ```sh
   docker compose up --build
   ```

The API is available at `http://localhost:8000/`. The Django admin is at `http://localhost:8000/admin/`. The backend container runs static-file collection and database migrations at startup, starts an RQ worker, and starts the web server.

To stop the services, press `Ctrl+C`; to remove the containers while keeping persisted data, run:

```sh
docker compose down
```

## Configuration

`.env.template` lists the environment variables for local configuration. The main settings are:

| Variable | Purpose |
| --- | --- |
| `SECRET_KEY` | Django secret key |
| `DEBUG` | Present in the template, but `core.settings` currently sets debug mode to `True` directly |
| `ALLOWED_HOSTS` | Comma-separated Django allowed hosts |
| `CSRF_TRUSTED_ORIGINS` | Comma-separated trusted origins |
| `DB_NAME`, `DB_USER`, `DB_PASSWORD` | PostgreSQL database and credentials |
| `DB_HOST`, `DB_PORT` | PostgreSQL connection |
| `REDIS_HOST`, `REDIS_PORT`, `REDIS_DB` | Redis connection for RQ |
| `REDIS_LOCATION` | Redis URL used by Django's cache |
| `DJANGO_SUPERUSER_USERNAME`, `DJANGO_SUPERUSER_PASSWORD`, `DJANGO_SUPERUSER_EMAIL` | Admin account values used during container startup |

Use secure, private values for secrets and passwords. Do not commit `.env`. The settings in this project are development-oriented; configure Django's production security settings before deploying publicly.

## API overview

All API routes are under `/api/`. Authentication-protected routes use the JWT cookies set by the login endpoint.

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/api/csrf/` | Get a CSRF token for protected requests |
| `POST` | `/api/register/` | Register an account (`username`, `email`, `password`, `confirmed_password`) |
| `GET` | `/api/activate/{uidb64}/{token}/` | Activate an account |
| `POST` | `/api/login/` | Log in with `email` and `password` |
| `POST` | `/api/logout/` | Invalidate the refresh token and clear auth cookies |
| `POST` | `/api/token/refresh/` | Refresh the access token |
| `POST` | `/api/password_reset/` | Request a password-reset email using `email` |
| `POST` | `/api/password_confirm/{uidb64}/{token}/` | Set a new password |
| `GET` | `/api/auth-test/` | Check authentication and return the current user's email |
| `GET` | `/api/video/` | List videos (authenticated) |
| `GET` | `/api/video/{movie_id}/{resolution}/index.m3u8` | Get an HLS playlist (authenticated) |
| `GET` | `/api/video/{movie_id}/{resolution}/{segment}/` | Get an HLS segment (authenticated) |

Supported HLS resolutions are `480p`, `720p`, and `1080p`. Login, logout, and token refresh require CSRF protection; clients should first request `/api/csrf/` and send the returned token with those requests. Registration and password confirmation require matching password fields.

Create video entries in the Django admin. When a new video record is saved with a video file, the backend queues HLS conversion; generated playlists and segments are served through the HLS endpoints above.

## Project structure

```text
.
├── auth_app/       # Account and authentication API
├── core/           # Django settings and root URL configuration
├── video_app/      # Video model, catalog, and HLS processing
├── backend.Dockerfile
├── docker-compose.yml
├── manage.py
└── requirements.txt
```

## Tests

Run the Django test suite inside the running web container:

```sh
docker compose exec web python manage.py test
```

The current `auth_app` and `video_app` test modules are scaffolds and do not yet contain substantive test cases.

## Notes

- Although `.env.template` lists SMTP-related variables, `core.settings` does not currently map them to Django's email settings. Configure and verify email delivery before relying on account activation or password-reset emails.
- Uploaded media and generated HLS files are stored in the `videoflix_media` Docker volume.
- The repository does not currently include a `LICENSE` file.

## Contributing

Contributions are welcome. Open an issue to discuss a proposed change, then submit a pull request with a clear description and relevant tests.

## License

No license has been specified yet. Until a license is added, the repository should not be assumed to grant permission to reuse, modify, or distribute its code.
