# Windows Server 2022 + IIS + Waitress Setup

This guide describes how to run the Django app behind IIS using Waitress as a reverse-proxied WSGI server.

## 1) Install Python and dependencies
1. Install Python 3.x on the server.
2. Place the repository on the server.
3. Create and activate a virtual environment, then install dependencies.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## 2) Configure environment variables
Create a `.env` file on the server and set production values.

- `DJANGO_SECRET_KEY`
- `DJANGO_DEBUG=false`
- `DJANGO_ALLOWED_HOSTS=your.domain,localhost,127.0.0.1`
- `APP_LOCAL_STORAGE_ROOT=...`

## 3) Test Waitress locally
Start Waitress and confirm the app loads.

```powershell
.\.venv\Scripts\python.exe -m waitress --listen=127.0.0.1:8001 config.wsgi:application
```

Verify:
- `http://127.0.0.1:8001/files/`

## 4) Run Waitress as a Windows service
Use `nssm` (recommended) to run Waitress as a service.

```powershell
nssm install WebFilePortalWaitress
```

Set the fields:
- Path: `C:\path\to\repo\.venv\Scripts\python.exe`
- Arguments: `-m waitress --listen=127.0.0.1:8001 config.wsgi:application`
- Startup directory: repository root

Start the service:

```powershell
nssm start WebFilePortalWaitress
```

## 5) Configure IIS reverse proxy
Install IIS features:
- Application Request Routing (ARR)
- URL Rewrite

In IIS Manager, enable ARR Proxy.

### URL Rewrite rule (example: /portal)
- Pattern: `^portal/(.*)`
- Action: `http://127.0.0.1:8001/$1`
- Append query string: ON

## 6) Static files
If IIS serves static files directly:

```powershell
python manage.py collectstatic
```

Expose the `staticfiles` directory via an IIS virtual directory.

## 7) Validate
- `https://your.domain/portal/files/`
- `https://your.domain/portal/healthz`
