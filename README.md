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
| `requirements-vercel.txt` | Deps para Vercel |
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

## Deploy

La app puede ir a Vercel; la base tiene que estar en un MySQL externo.

1. Importa `bdcompleta.sql` en ese MySQL y abre acceso remoto.
2. Conecta el repo en Vercel.
3. Carga las variables de `.env.example` en Environment Variables.
4. Si el build pesa mucho, usa: `pip install -r requirements-vercel.txt`.

