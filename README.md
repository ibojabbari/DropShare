# DropShare

An AppSec-focused file-sharing and text-editing web application built with Django REST Framework and React. DropShare demonstrates how common application-security concerns affect everyday features: authentication, private uploads, user connections, sharing with connected users, and document editing on the browser.

> This is a demonstrative AppSec project. It applies real security patterns, but it is not presented as a complete enterprise file-storage platform

## What it does

- Creates accounts and signs users in with Django session authentication.
- Uploads private files and creates plain-text documents.
- Lets users create and accept connections before sharing files.
- Supports read-only and edit-level file shares.
- Lets owners revoke a share immediately.

## Stack

- **Backend:** Django REST Framework, PostgreSQL
- **Frontend:** React

## Security controls involved in the project

| Area | How DropShare addresses it |
| --- | --- |
| **Authentication** | Django's user-management API hashes passwords; Django password validators reject weak passwords; the session key is rotated on login to reduce **session fixation** risk. |
| **CSRF (Cross-Site Request Forgery)** | State-changing browser requests use Django CSRF protection. The React app obtains a token from the API and sends it in the `X-CSRFToken` header. |
| **CORS configuration** | Allowed origins and CSRF-trusted origins come from environment variables. Credentialed requests are permitted only for those exact origins. |
| **Authorization / IDOR** | A file UUID is never treated as permission. Protected file and document operations check that the requester is the owner or holds an explicit share, protecting against **IDOR (Insecure Direct Object Reference)**. |
| **Permission model** | Owners manage their files and shares. A recipient may read a shared document, while only an `edit` share may change it. Revocation deletes the authorization record, so later access checks fail. |
| **Information disclosure** | Unauthorized protected-resource lookups return `404 Not Found`, avoiding confirmation that another user's file exists. |
| **Private file storage** | There is no public media URL. Files are served only through authenticated, permission-checked download and preview endpoints. |
| **Path traversal** | Storage paths use generated UUIDs and original filenames are reduced to a basename, so client-provided paths such as `../../file` cannot control where a file is stored. |
| **Upload safety** | The backend enforces 10 MB per file and 100 MB per upload action. It rejects SVG plus executable and script-like uploads, and it detects common executable file signatures even when a filename is disguised. Image preview is allowlisted to PNG, JPEG, GIF, and WebP after simple signature checks |
| **Browser content safety** | Downloads use attachment responses with `X-Content-Type-Options: nosniff`. Preview responses use a same-origin resource policy. React escapes rendered text by default, and the app does not use `dangerouslySetInnerHTML` for user content. This reduces common **XSS (Cross-Site Scripting)** paths. |
| **Security headers** | `X-Content-Type-Options: nosniff`, a same-origin referrer policy, and `X-Frame-Options: DENY` are configured. `X-Frame-Options` mitigates **clickjacking**. |
| **Production HTTPS** | Production settings enable HTTPS redirects, secure CSRF/session cookies, HSTS, and proxy HTTPS handling. |
| **Rate limiting** | Login and registration use Django REST Framework scoped throttles to slow basic credential-guessing attempts. |

## Explicit application-security scope

These terms are named directly because they are common review topics. Some are mitigated by the design; others are out of scope because the feature that would create the risk does not exist yet.

| Topic | Current treatment | If the product grows |
| --- | --- | --- |
| **SQL injection** | Application database access uses Django ORM queries and model operations rather than application-written raw SQL, as it is the standard. | No change planned, database access will remain through the Django ORM. |
| **XXE (XML External Entity)** | The app does not parse XML documents, and SVG uploads are rejected. | If XML imports or processing is permitted, it would need a parser configured to prohibit external entities. |
| **Command injection** | The app does not run user-supplied commands or execute uploaded files. | If file conversion or antivirus scanning is added, those processes should run in isolated workers with safe argument handling. |
| **Path traversal** | Generated storage paths and basename normalization prevent client-controlled filesystem locations. | Object-storage adapters must preserve this rule. |
| **XSS** | React's normal rendering escapes text; user files are not rendered as HTML; no raw HTML injection API is used. | Rich text, Markdown, HTML, or SVG features need dedicated sanitization and review. |
| **Clickjacking** | `X-Frame-Options: DENY` blocks framing. | Add a Content Security Policy for stronger and more flexible browser controls. |

## Project architecture

The application separates security responsibilities into small Django apps:

| App | Responsibility |
| --- | --- |
| `accounts` | Registration, login, logout, and the current session |
| `connections` | Connection requests and acceptance |
| `permissions` | File shares plus reusable ownership/read/edit authorization checks |
| `workspace` | Files and plain-text documents; calls the permissions layer before exposing a resource |

Request flow:

```text
Browser → Django session authentication → API view
API view → serializer validates input → model or permission service
Permission service → owner/share check → response or 404
```

## Local setup

### Prerequisites

- Python 3 and pip
- Node.js and npm
- PostgreSQL running locally

### Backend

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python manage.py migrate
python manage.py runserver
```

Configure `.env` with a long random `SECRET_KEY` and PostgreSQL values for `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, and `DB_PORT`.

The development CORS and CSRF origin is preconfigured for Vite at `http://localhost:5173`.

### Frontend

```powershell
cd frontend
npm install
npm run dev
```

Open the URL printed by Vite. For deployment, configure a proxy or routing layer so frontend API requests reach Django.

## Tests

Run the backend checks:

```powershell
python manage.py test
python manage.py check
```

Run the frontend checks:

```powershell
cd frontend
npm run lint
npm test
npm run build
```

The backend tests cover account/session behavior, CSRF enforcement, private-file access, uploads, document permissions, connection acceptance, sharing restrictions, and share revocation. The frontend tests cover the authentication interface.

## Known limits and next steps

DropShare stores uploads on the local filesystem. That works for local development and a demonstrative project, but many cloud platforms have ephemeral disks. A real deployment should use private persistent object storage with backups, retention rules, encryption, and access logging.

Further production work would include:

- Malware scanning before files are broadly available or processed.
- Email verification and password-reset flows.
- MFA, account lockout, and stronger abuse detection.
- Centralized rate limiting for multiple server instances.
- A Content Security Policy and security reporting endpoint.
- Audit logging and monitoring of security-relevant events.

## This is a demonstrative project. However, if you expand on this project and plan to deploy it:

- Set `DJANGO_ENV=production` and use a long, random `SECRET_KEY`.
- Set `DEBUG=false` and supply the deployed hostname through `ALLOWED_HOSTS`.
- Set `CORS_ALLOWED_ORIGINS` and `CSRF_TRUSTED_ORIGINS` to exact HTTPS frontend origins.
- Store PostgreSQL credentials in the deployment platform's secret store.
- Confirm TLS, secure-cookie, HSTS, and proxy settings match the host.
- Replace local media storage before treating uploaded files as durable user data.
