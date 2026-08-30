# Wingsalsa MarketPlace

MVP local para publicar actividades deportivas de escuelas de Tarifa y recibir solicitudes de reserva sin registro.

## Puesta en marcha

```powershell
docker compose up -d db
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py seed_demo
.\.venv\Scripts\python.exe manage.py createsuperuser
.\.venv\Scripts\python.exe manage.py runserver
```

La web estará en `http://127.0.0.1:8000/`. El backoffice operativo diario está en `http://127.0.0.1:8000/gestion/` para gestionar reservas, escuelas y actividades. Django Admin permanece en `http://127.0.0.1:8000/admin/` para la administración técnica.

## Comprobaciones

```powershell
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py test
```

Con el servidor local abierto, la revisión del recorrido móvil se ejecuta con:

```powershell
.\.venv\Scripts\python.exe tests\browser_qa.py
```

Las variables disponibles están documentadas en `.env.example`. Por defecto el proyecto usa el PostgreSQL de `compose.yaml` en el puerto local `55432`.

## Railway

El proyecto incluye un `Dockerfile` reproducible y `railway.json` con el healthcheck y la política de reinicio. La imagen contiene los archivos estáticos y su arranque aplica migraciones, prepara los datos iniciales y ejecuta Gunicorn. La base de datos de producción se configura mediante las variables `PGDATABASE`, `PGUSER`, `PGPASSWORD`, `PGHOST` y `PGPORT` del servicio PostgreSQL.
