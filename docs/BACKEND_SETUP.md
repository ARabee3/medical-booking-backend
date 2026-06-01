# Backend Setup Guide

**For:** Ahmed, Abdulazim, Gerges, Mokhtar  
**Prerequisites:** Python 3.11+, PostgreSQL 15+, Git

---

## 1. Clone the Repository

```bash
git clone https://github.com/ARabee3/medical-booking-backend.git
cd medical-booking-backend
```

---

## 2. Create a Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate   # Linux/macOS
# .venv\Scripts\activate   # Windows
```

---

## 3. Install Dependencies

```bash
make install
# OR manually:
pip install -r requirements/local.txt
```

---

## 4. Configure Environment Variables

```bash
cp .env.example .env
```

Edit `.env` and set your PostgreSQL credentials:

```bash
SECRET_KEY=your-secret-key-here-change-me
DEBUG=True
DB_NAME=medical_booking
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=localhost
DB_PORT=5432
```

---

## 5. Create the Database

```bash
# If you have PostgreSQL installed locally:
createdb medical_booking

# Or use psql:
psql -U postgres -c "CREATE DATABASE medical_booking;"
```

---

## 6. Run Migrations

```bash
make migrate
# OR:
python manage.py migrate
```

---

## 7. Create a Superuser

```bash
make superuser
# OR:
python manage.py createsuperuser
```

Follow the prompts. Use email as the username.

---

## 8. Run the Development Server

```bash
make run
# OR:
python manage.py runserver
```

The API will be available at: `http://127.0.0.1:8000/api/`

---

## 9. Verify Setup

Open your browser or use curl:

```bash
# Health check (Django admin)
curl http://127.0.0.1:8000/admin/

# Token endpoint (should return 400 with missing fields, proving DRF is running)
curl -X POST http://127.0.0.1:8000/api/token/ \
  -H "Content-Type: application/json" \
  -d '{}'
```

---

## 10. Run Tests

```bash
make pytest
# OR:
pytest
```

You should see all tests pass (or zero tests if no tests written yet).

---

## 11. Common Commands

| Command | Description |
|---------|-------------|
| `make run` | Start development server |
| `make test` | Run Django tests |
| `make pytest` | Run pytest suite |
| `make migrate` | Apply migrations |
| `make makemigrations` | Create new migrations |
| `make superuser` | Create admin user |
| `make shell` | Open Django shell |
| `make lint` | Run flake8 |
| `make format` | Run Black formatter |
| `make seed` | Seed demo data (when implemented) |

---

## 12. IDE Setup (VS Code)

Recommended extensions:
- Python (Microsoft)
- Pylance (Microsoft)
- Django (batisteo)

Configure `.vscode/settings.json`:

```json
{
  "python.defaultInterpreterPath": "./.venv/bin/python",
  "python.linting.enabled": true,
  "python.formatting.provider": "black",
  "editor.formatOnSave": true
}
```

---

## 13. Troubleshooting

### Error: `ModuleNotFoundError: No module named 'dotenv'`
**Fix:** Run `make install` or `pip install -r requirements/local.txt`

### Error: `django.db.utils.OperationalError: FATAL: database "medical_booking" does not exist`
**Fix:** Run `createdb medical_booking` or check your `.env` DB_NAME value.

### Error: `Permission denied` on PostgreSQL
**Fix:** Ensure your DB user has CREATEDB privilege, or create the database as the postgres superuser.

### Error: `secret key must be set`
**Fix:** Ensure `.env` exists and has a `SECRET_KEY` value.

---

## 14. Git Workflow

See `docs/GIT_WORKFLOW.md` for full details.

Quick start:
```bash
git checkout develop
git pull origin develop
git checkout -b feature/<your-name>-<short-desc>
# ... work ...
git push -u origin feature/<your-name>-<short-desc>
# Open PR to develop
```
