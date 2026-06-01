# Deployment Notes

**Status:** Future checklist — not needed for development phase.

---

## Pre-Deployment Checklist

- [ ] `SECRET_KEY` is strong and stored in environment variables
- [ ] `DEBUG=False` in production
- [ ] `ALLOWED_HOSTS` includes the production domain
- [ ] PostgreSQL database is provisioned and accessible
- [ ] Static files configured with whitenoise
- [ ] CORS origins restricted to production frontend URL
- [ ] SSL/TLS configured (HTTPS only)
- [ ] `SECURE_SSL_REDIRECT=True`
- [ ] `SESSION_COOKIE_SECURE=True`
- [ ] `CSRF_COOKIE_SECURE=True`

---

## Environment Variables for Production

```bash
SECRET_KEY=<50-char-random-string>
DEBUG=False
ALLOWED_HOSTS=api.medicalbooking.com
DATABASE_URL=postgres://user:pass@host:5432/dbname
CORS_ALLOWED_ORIGINS=https://medicalbooking.com
```

---

## Deployment Options

### Option 1: VPS (DigitalOcean, Linode, AWS EC2)
- Ubuntu 22.04 LTS
- PostgreSQL 15
- Nginx reverse proxy
- Gunicorn WSGI server
- Supervisor or systemd for process management
- SSL via Let's Encrypt (Certbot)

### Option 2: PaaS (Heroku, Railway, Render)
- Push to Git
- Set environment variables in dashboard
- Platform handles build and deploy
- Add-ons: PostgreSQL, SSL

### Option 3: Docker (Future)
- `Dockerfile` for Django app
- `docker-compose.yml` for Django + PostgreSQL + Nginx
- `docker-compose.prod.yml` for production

---

## Nginx Configuration Template

```nginx
server {
    listen 80;
    server_name api.medicalbooking.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /static/ {
        alias /var/www/medical-booking/static/;
    }
}
```

---

## Gunicorn Service Template (systemd)

```ini
[Unit]
Description=Medical Booking Gunicorn Daemon
After=network.target

[Service]
User=deploy
Group=www-data
WorkingDirectory=/var/www/medical-booking-backend
ExecStart=/var/www/medical-booking-backend/.venv/bin/gunicorn --access-logfile - --workers 3 --bind unix:/run/gunicorn.sock config.wsgi:application

[Install]
WantedBy=multi-user.target
```

---

## Database Migrations in Production

```bash
# Always backup before migrating
pg_dump medical_booking > backup_$(date +%Y%m%d).sql

# Run migrations
python manage.py migrate
```

---

## SSL with Let's Encrypt

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d api.medicalbooking.com
```

---

## Monitoring (Future)

- Sentry for error tracking
- Django Logging to file/syslog
- Health check endpoint: `GET /api/health/`
