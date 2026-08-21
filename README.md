# BLDNGSolutions

App web para PyMEs de venta y renta de maquinaria de construcción.

Incluye área de clientes, ventas, almacén, mantenimiento, envíos y administración (empleados, accesos y estadísticas).

Hecha con Flask, MySQL y Jinja2.

## Requisitos

- Python 3.12
- MySQL o MariaDB

## Cómo levantarlo

```bash
git clone git@github.com:Jalvala147/BLDNGSolutions.git
cd BLDNGSolutions

python3 -m venv env
source env/bin/activate

pip install -r requirements.txt
cp .env.example .env
```

Arma la base e importa el dump (`bdcompleta.sql`, no está en el repo):

```bash
mysql -u root -p -e "CREATE DATABASE bdcompleta CHARACTER SET utf8mb4;"
mysql -u root -p bdcompleta < bdcompleta.sql
```

Completa `.env` con tu MySQL y un `SECRET_KEY`, luego:

```bash
python src/app.py
```

Abre `http://127.0.0.1:5000`.

## Mapa del proyecto

### Archivos clave

| Archivo | Para qué |
|---------|----------|
| `src/app.py` | Entrada Flask, login, rutas públicas |
| `src/config.py` | Config y lectura de env |
| `src/clients.py` | Área cliente |
| `src/salesemp.py` | Ventas |
| `src/storageemp.py` | Almacén |
| `src/maintemp.py` | Mantenimiento |
| `src/shipemp.py` | Envíos |
| `src/admin.py` | Administración |
| `src/models/` | Usuario y auth |
| `src/templates/` | Vistas Jinja por área |
| `src/static/` | CSS, JS e imágenes |
| `.env.example` | Variables de entorno |
| `requirements.txt` | Deps locales |
| `requirements-vercel.txt` | Deps del build en Vercel |
| `scripts/vercel_install.sh` | pip en Vercel (PyMySQL, sin mysqlclient) |
| `scripts/vercel_build.py` | Copia `src/static` a `public/static` (CDN) |
| `vercel.json` | Config de deploy |
| `migrations/` | Ajustes de schema |
| `bdcompleta.sql` | Dump de la base (local, no va al repo) |

### Áreas (templates)

| Carpeta | Área |
|---------|------|
| `templates/clientuser/` | Cliente |
| `templates/salesEmpArea/` | Ventas |
| `templates/storage/` | Almacén |
| `templates/maintenance/` | Mantenimiento |
| `templates/shipping/` | Envíos |
| `templates/administration/` | Admin |
| `templates/auth/` | Logins |
| `templates/startpage/` | Sitio público |

## Deploy en Vercel

Vercel corre Flask como una sola Function (`src/app.py`). **MySQL no puede ir en Vercel**: usa un MySQL/MariaDB alojado (PlanetScale, Railway, Aiven, RDS, un VPS, etc.) con acceso remoto.

Las IPs de salida de Vercel cambian. El host de MySQL tiene que aceptar conexiones externas (allowlist `0.0.0.0/0`, o un proveedor sin filtro por IP).

### 1. Base de datos

```bash
mysql -u USER -p -h HOST -e "CREATE DATABASE bdcompleta CHARACTER SET utf8mb4;"
mysql -u USER -p -h HOST bdcompleta < bdcompleta.sql
```

Si el proveedor exige TLS, más adelante pon `MYSQL_SSL=true`.

### 2. Proyecto en Vercel

1. [Importa el repo](https://vercel.com/new) (Framework Preset: Flask se detecta solo).
2. Root Directory: deja el raíz del repo.
3. No hace falta cambiar Install/Build: `vercel.json` ya usa `scripts/vercel_install.sh` y `scripts/vercel_build.py`.

### 3. Variables de entorno

En **Project → Settings → Environment Variables**, copia los nombres de `.env.example`. Mínimo para que arranque:

| Variable | Notas |
|----------|--------|
| `SECRET_KEY` | Obligatorio. `python -c "import secrets; print(secrets.token_hex(32))"` |
| `FLASK_ENV` | `production` |
| `MYSQL_HOST` | Host público del MySQL |
| `MYSQL_PORT` | `3306` salvo que el proveedor indique otro |
| `MYSQL_USER` / `MYSQL_PASSWORD` / `MYSQL_DB` | Credenciales |
| `MYSQL_SSL` | `true` si el host exige TLS |
| `MAIL_*` | Solo si usas recuperar contraseña |
| `GOOGLE_MAPS_*` / `STRIPE_*` | Opcionales |

Aplica las variables a Production (y Preview si quieres).

En **Settings → Functions**, elige una región cercana a la base (menos latencia).

### 4. Verificar

Tras el deploy, `https://TU-DOMINIO.vercel.app/healthz` debe responder `{"status":"ok"}`. Luego prueba `/startpage` y un login.

Si el Function log dice que no puede conectar a MySQL: host, puerto, firewall/allowlist, o `MYSQL_SSL`.

### CLI (opcional)

```bash
npm i -g vercel
vercel login
vercel
# producción:
vercel --prod
```

No subas `.env`. Vercel inyecta las variables del dashboard.

