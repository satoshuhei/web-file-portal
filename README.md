# Web File Portal

Read-only web portal to access existing shared folders without SMB.

## Setup
1. Create and activate a virtual environment.
2. Install dependencies.
3. Copy `.env.example` to `.env` and adjust values.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip
python -m pip install -r requirements.txt
```

## Run
```powershell
python manage.py runserver
```

## Sample data
```powershell
python manage.py seed_sample_data
```

This command creates sample tenants, file entries, and audit logs, and writes sample
files under `APP_LOCAL_STORAGE_ROOT`.

## Notes
- Do not commit `.env`.
- Use `.env.example` as the template for local configuration.