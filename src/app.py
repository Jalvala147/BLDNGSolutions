#Importaciones
import os
import sys
from pathlib import Path

_SRC_DIR = Path(__file__).resolve().parent
_ROOT_DIR = _SRC_DIR.parent
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

# Load local .env if present (no-op on Vercel when vars are set in the dashboard)
_env_path = _ROOT_DIR / '.env'
if _env_path.is_file():
    for _line in _env_path.read_text(encoding='utf-8').splitlines():
        _line = _line.strip()
        if not _line or _line.startswith('#') or '=' not in _line:
            continue
        _k, _v = _line.split('=', 1)
        os.environ.setdefault(_k.strip(), _v.strip())

# Prefer pure-Python MySQL driver on serverless (Vercel); fall back to mysqlclient locally.
try:
    import pymysql
    pymysql.install_as_MySQLdb()
except ImportError:
    pass

from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_mysqldb import MySQL
from flask_mail import Mail, Message
from flask import render_template_string
from flask_wtf.csrf import CSRFProtect
from flask_login import LoginManager, login_user, logout_user
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from utils.passwords import generate_password_hash, check_password_hash
from salesemp import salesemp, sales_required
from clients import clients
from maintemp import maintemp, maintenance_required
from storageemp import storageemp, storage_required
from shipemp import shipemp, shipping_required
from admin import admin
from config import config
import re

_static_dir = _SRC_DIR / 'static'
app = Flask(
    __name__,
    template_folder=str(_SRC_DIR / 'templates'),
    static_folder=str(_static_dir) if _static_dir.is_dir() else None,
    static_url_path='/static',
)
_env = os.environ.get('FLASK_ENV', os.environ.get('VERCEL_ENV', 'development'))
_config_name = 'production' if _env in ('production', 'prod') or os.environ.get('VERCEL') else 'development'
app.config.from_object(config[_config_name])
if not app.config.get('SECRET_KEY'):
    # Empty SECRET_KEY used to raise and crash the whole Vercel Function.
    # Prefer setting SECRET_KEY in the dashboard; this keeps the app booting.
    fallback = os.environ.get('VERCEL_DEPLOYMENT_ID') or 'dev-only-insecure-secret-key'
    app.config['SECRET_KEY'] = fallback
    print('WARNING: SECRET_KEY is not set; using a deploy fallback. Set SECRET_KEY in Vercel env.')

# Vercel terminates TLS; honor X-Forwarded-* so cookies and url_for(_external=True) use https.
if os.environ.get('VERCEL') or _config_name == 'production':
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

# MySQL (env vars override defaults from config)
app.config['MYSQL_HOST'] = os.environ.get('MYSQL_HOST', app.config.get('MYSQL_HOST', 'localhost'))
app.config['MYSQL_USER'] = os.environ.get('MYSQL_USER', app.config.get('MYSQL_USER', ''))
app.config['MYSQL_PASSWORD'] = os.environ.get('MYSQL_PASSWORD', app.config.get('MYSQL_PASSWORD', ''))
app.config['MYSQL_DB'] = os.environ.get('MYSQL_DB', app.config.get('MYSQL_DB', 'bdcompleta'))
app.config['MYSQL_CHARSET'] = os.environ.get('MYSQL_CHARSET', 'utf8mb4')
app.config['MYSQL_CONNECT_TIMEOUT'] = int(os.environ.get('MYSQL_CONNECT_TIMEOUT', '10'))
if os.environ.get('MYSQL_PORT', '').strip():
    app.config['MYSQL_PORT'] = int(os.environ['MYSQL_PORT'])
if os.environ.get('MYSQL_SSL', '').lower() in ('1', 'true', 'yes'):
    ssl_opts = {}
    if os.environ.get('MYSQL_SSL_CA'):
        ssl_opts['ca'] = os.environ['MYSQL_SSL_CA']
    # PyMySQL: empty ssl dict enables TLS (required by TiDB Cloud).
    app.config['MYSQL_CUSTOM_OPTIONS'] = {'ssl': ssl_opts}

#Blueprints de las otras areas
app.register_blueprint(salesemp)
app.register_blueprint(clients)
app.register_blueprint(maintemp)
app.register_blueprint(storageemp)
app.register_blueprint(shipemp)
app.register_blueprint(admin)

# Models:
from models.ModelUser import ModelUser

# Entities:
from models.entities.User import User


csrf = CSRFProtect()

mysql = MySQL(app)

login_manager_app = LoginManager(app)

@login_manager_app.user_loader
def load_user(id):
    return ModelUser.get_by_id(mysql, id)


def _password_reset_serializer():
    return URLSafeTimedSerializer(app.config['SECRET_KEY'], salt='password-reset')

#configuracion para el envio de correos
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', app.config.get('MAIL_SERVER', 'smtp.googlemail.com'))
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', app.config.get('MAIL_PORT', 587)))
app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'true').lower() in ('1', 'true', 'yes')
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME', app.config.get('MAIL_USERNAME', ''))
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD', app.config.get('MAIL_PASSWORD', ''))

mail = Mail(app)


#rutas para el proceso de logout de los usuarios
@app.route('/logout', methods=['POST', 'GET'])
def logout():
    logout_user()
    session.clear()
    return redirect(url_for('startpage'))

@app.route('/logoutemp', methods=['POST', 'GET'])
def logoutemp():
    logout_user()
    session.clear()
    return redirect(url_for('loginemp'))

@app.route('/logoutadm', methods=['POST', 'GET'])
def logoutadm():
    logout_user()
    session.clear()
    return redirect(url_for('startpage'))



#--------------------Pagina de inicio------------------

#---------------Ruta por defecto /-------------------------

@app.route('/')
def index():
    return redirect(url_for('startpage'))

@app.route('/startpage')
def startpage():
    return render_template('startpage.jinja')

@app.route('/healthz')
def healthz():
    return {
        'status': 'ok',
        'secret_key_configured': bool(os.environ.get('SECRET_KEY')),
        'mysql_host_configured': bool(os.environ.get('MYSQL_HOST')),
        'mysql_port': app.config.get('MYSQL_PORT'),
        'mysql_ssl': bool(app.config.get('MYSQL_CUSTOM_OPTIONS')),
    }, 200

#------------Listado de los productos(maquinas)---------------------
@app.route('/productsList')   
def productsList():

    cur = mysql.connection.cursor() 
    cur.execute("SELECT id, name, image, price, id_Machine FROM products")
    product_data = cur.fetchall()

    # Crear una lista para almacenar los productos como dicconarios
    products = [] 
    for product in product_data: #itera sobre los datos de los productos obtenidos
        product_dict = { #crear un diccionario para cada producto con id, name, image y price
            'id': product[0],
            'name': product[1],
            'image': product[2],
            'price': product[3],
            'id_Machine' : product[4]
        }
        products.append(product_dict) #agrega el diccionario del producto a la lista de productos

    cur.close()
    
    return render_template('startpage/productsList.jinja', products=products)

@app.route('/contact')
def contact():
    return render_template(
        'startpage/contact.jinja',
        google_maps_api_key=os.environ.get('GOOGLE_MAPS_API_KEY_CONTACT', ''),
    )

@app.route('/aboutUs')
def aboutUs():
    return render_template('startpage/aboutUs.jinja')

#-----------------Query para crear un nuevo usuario de tipo cliente----------------

# Funcion para verificar las politicas del nombre de usuario
def verificar_nombre_usuario(username):
    if len(username) < 6 or len(username) > 15:
        return "El nombre de usuario debe tener entre 6 y 15 caracteres."
    if not any(char.isupper() for char in username):
        return "El nombre de usuario debe contener al menos una mayúscula."
    if not username.isalnum():
        return "El nombre de usuario solo debe contener caracteres alfanuméricos."
    if not any(char.isdigit() for char in username):
        return "El nombre de usuario debe contener al menos un número."
    return None

# Funcion para verificar las politicas de contraseña
def verificar_contrasena(password):
    if not password or len(password) < 8:
        return "La contraseña debe tener al menos 8 caracteres."
    if not any(char.isupper() for char in password):
        return "La contraseña debe contener al menos una mayúscula."
    if not any(char in "!@#$%^&*()_+[]{}|;:'\"<>,.?/~`" for char in password):
        return "La contraseña debe contener al menos un caracter especial."
    return None

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    
    if request.method == 'POST':
        # Recibir la informacion del formulario de signup.jinja
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        fullname = request.form['fullname']
        email = request.form['email']
        tipoUsuario = 3
        areaUsuario = 4
        
        # Verificar las politicas de nombre de usuario
        username_error = verificar_nombre_usuario(username)
        if username_error:
            flash(username_error)
            return render_template('signup.jinja', username=username, fullname=fullname, email=email)
        
        # Verificar las politicas de contraseña
        password_error = verificar_contrasena(request.form['password'])
        if password_error:
            flash(password_error)
            return render_template('signup.jinja', username=username, fullname=fullname, email=email)

        # Verificar si el correo ya está en uso
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM user WHERE email = %s", (email,))
        existing_email = cur.fetchone()
        cur.execute("SELECT id FROM user WHERE username = %s", (username,))
        existing_username = cur.fetchone()
        cur.close()

        if existing_email:
            flash("El correo electrónico ya está en uso.")
            return render_template('signup.jinja', username=username, fullname=fullname, email=email)

        if existing_username:
            flash("El nombre de usuario ya está en uso.")
            return render_template('signup.jinja', username=username, fullname=fullname, email=email)
        
        
        cur = mysql.connection.cursor()
        # Query para insertar en la bd la informacion del nuevo usuario cliente
        cur.execute("INSERT INTO user (username, password, fullname, email, tipoUsuario, areaUsuario) VALUES (%s, %s, %s, %s, %s, %s)", (username, password, fullname, email, tipoUsuario, areaUsuario))

        # Se hace commit a la bd
        mysql.connection.commit()
        cur.close()

        flash("Usuario registrado con éxito.")
        return redirect(url_for('login'))  # Redirecciona al login de los clientes para iniciar sesion
    return render_template('signup.jinja')

#----------------------------Login para clientes, tipo de usuario 3-----------------------------------------------
@app.route('/loginclient', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        cur = mysql.connection.cursor()
        cur.execute("SELECT id, password, tipousuario, areaUsuario FROM user WHERE username=%s", (username,))
        user_data = cur.fetchone()
        cur.close()

        if user_data is not None:
            user_id, hashed_password, tipoUsuario, areaUsuario = user_data

            if check_password_hash(hashed_password, password):
                logged_user = User(user_id, username, None, "", tipoUsuario, areaUsuario)
                if tipoUsuario == 3:
                    login_user(logged_user)
                    session['user_id'] = user_id
                    return redirect(url_for('clients.clientsHome'))

                flash("Invalid user type...")
                return render_template('auth/loginclient.jinja')

        flash("User not found or invalid credentials...")
        return render_template('auth/loginclient.jinja')

    return render_template('auth/loginclient.jinja')


#---------------------------------Login para administradores, tipo de usuario 1------------------------------------------
@app.route('/loginadm', methods=['GET', 'POST'])
def loginadm():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        #print(request.form['username'])
        #print(request.form['password'])
        
        cur = mysql.connection.cursor()
        cur.execute("SELECT id, password, tipousuario, areaUsuario FROM user WHERE username=%s", (username,))
        user_data = cur.fetchone()
        cur.close()

        if user_data is not None:
            user_id, hashed_password, tipoUsuario, areaUsuario = user_data

            if check_password_hash(hashed_password, password):
                logged_user = User(user_id, username, None, "", tipoUsuario, areaUsuario)
                if tipoUsuario == 1:
                    login_user(logged_user)
                    return redirect(url_for('admin.adminHome'))

                flash("Tipo de usuario no válido...")
                return render_template('auth/loginadm.jinja')

            else:
                flash("Contraseña no válida...")
                return render_template('auth/loginadm.jinja')

        flash("Administrador no encontrado...")
        return render_template('auth/loginadm.jinja')

    return render_template('auth/loginadm.jinja')


#---------------------------------Login para empleados, tipo de usuario 2----------------------------------------------

@app.route('/loginemp', methods=['GET', 'POST'])
def loginemp():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        cur = mysql.connection.cursor()
        cur.execute("SELECT id, password, tipousuario, areaUsuario FROM user WHERE username=%s", (username,))
        user_data = cur.fetchone()
        cur.close()
        
        if user_data is not None:
            user_id, hashed_password, tipoUsuario, idArea = user_data
            
            if check_password_hash(hashed_password, password):
                logged_user = User(user_id, username, None, "", tipoUsuario, idArea)

                if tipoUsuario == 2 and idArea == 2:  #redireccion para usuarios de ventas
                    login_user(logged_user)
                    session['user_id'] = logged_user.id  
                    return redirect(url_for('sales_emp_area'))
                
                elif tipoUsuario == 2 and idArea == 3: #redireccion para usuarios de almacen
                    login_user(logged_user)
                    session['user_id'] = logged_user.id  
                    return redirect(url_for('storage_home'))
                
                elif tipoUsuario == 2 and idArea == 5: #redireccion para usuarios de mantenimieto
                    login_user(logged_user)
                    session['user_id'] = logged_user.id  
                    return redirect(url_for('maintenance_home'))
                
                elif tipoUsuario == 2 and idArea == 6: #redireccion para usuarios de envios
                    login_user(logged_user)
                    session['user_id'] = logged_user.id  
                    return redirect(url_for('shipping_home'))
                
                else:
                    flash("Invalid user type or area...")
                    return render_template('auth/loginemp.jinja')

            else:
                flash("Contraseña no valida...")
                return render_template('auth/loginemp.jinja')

        flash("Usuario no encontrado...")
        return render_template('auth/loginemp.jinja')

    return render_template('auth/loginemp.jinja')

@app.route('/sales_emp_area')
@sales_required
def sales_emp_area():
    return render_template('salesEmpArea/salesHome.jinja')

@app.route('/storage_home')
@storage_required
def storage_home():
    return render_template('storage/storageHome.jinja')

@app.route('/maintenance_home')
@maintenance_required
def maintenance_home():
    return render_template('maintenance/mantHome.jinja')

@app.route('/shipping_home')
@shipping_required
def shipping_home():
    return render_template('shipping/shipHome.jinja')



#---------------------------------Ruta para recuperacion de contraseña----------------------------------------------

_RESET_TOKEN_MAX_AGE = 3600  # 1 hour
_RESET_GENERIC_MESSAGE = (
    'Si el correo está registrado, recibirás un enlace para restablecer tu contraseña.'
)

@app.route('/forgotpassword', methods=['GET', 'POST'])
def forgotpassword():
    if request.method == 'POST':
        correo_destinatario = (request.form.get('correo') or '').strip()
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

        if not re.match(pattern, correo_destinatario):
            flash('Error: Por favor, ingrese un correo electrónico válido.', 'error')
            return render_template('auth/forgotpassword.jinja')

        cur = mysql.connection.cursor()
        try:
            cur.execute("SELECT id FROM user WHERE email = %s", (correo_destinatario,))
            user = cur.fetchone()

            if user:
                token = _password_reset_serializer().dumps({'id': user[0]})
                cur.execute("UPDATE user SET reset_token = %s WHERE id = %s", (token, user[0]))
                mysql.connection.commit()

                reset_url = url_for('changepassword', token=token, _external=True)
                html_content = render_template_string('''
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Recuperación de contraseña</title>
                    <style>
                        body { font-family: Arial, sans-serif; background-color: #f2f2f2; }
                        .container {
                            max-width: 600px; margin: 0 auto; padding: 20px;
                            background-color: #ffffff; border-radius: 5px;
                            box-shadow: 0px 0px 10px rgba(0, 0, 0, 0.1);
                        }
                        h1 { color: #ff0000; }
                        p { color: #333333; line-height: 1.6; }
                        a { color: #0000ff; text-decoration: none; }
                        a:hover { text-decoration: underline; }
                        .btn {
                            display: inline-block; padding: 10px 20px;
                            background-color: #ff0000; color: #ffffff;
                            text-decoration: none; border-radius: 5px;
                        }
                    </style>
                </head>
                <body>
                    <div class="container">
                        <h1>Recuperación de contraseña</h1>
                        <p>Se ha solicitado un cambio de contraseña para su cuenta de BuildingSolutions. Si usted no ha solicitado este cambio, ignore este correo. Si desea cambiar su contraseña, use el siguiente <a href="{{ reset_url }}">enlace</a>.</p>
                        <p>El enlace caduca en una hora.</p>
                        <a class="btn" href="{{ reset_url }}">Cambiar Contraseña</a>
                    </div>
                </body>
                </html>
                ''', reset_url=reset_url)

                sender = app.config.get('MAIL_USERNAME') or 'bldngsolutions.mail@gmail.com'
                msg = Message('Recuperación de contraseña', sender=sender, recipients=[correo_destinatario])
                msg.html = html_content
                mail.send(msg)
        finally:
            cur.close()

        flash(_RESET_GENERIC_MESSAGE, 'success')

    return render_template('auth/forgotpassword.jinja')


@app.route('/changepassword/<token>', methods=['GET', 'POST'])
def changepassword(token):
    try:
        data = _password_reset_serializer().loads(token, max_age=_RESET_TOKEN_MAX_AGE)
        token_user_id = data.get('id')
    except SignatureExpired:
        flash('Error: El enlace de recuperación ha caducado. Solicita uno nuevo.', 'error')
        return redirect(url_for('forgotpassword'))
    except (BadSignature, TypeError, AttributeError):
        flash('Error: El token no es válido.', 'error')
        return redirect(url_for('forgotpassword'))

    cur = mysql.connection.cursor()
    try:
        cur.execute("SELECT id FROM user WHERE id = %s AND reset_token = %s", (token_user_id, token))
        user_data = cur.fetchone()

        if user_data is None:
            flash('Error: El token no es válido o ya fue utilizado.', 'error')
            return redirect(url_for('forgotpassword'))

        if request.method == 'POST':
            nueva_contrasena = request.form.get('nueva_contrasena')
            confirmar_contrasena = request.form.get('confirmar_contrasena')
            error_message = verificar_contrasena(nueva_contrasena)

            if error_message is not None:
                flash('Error: ' + error_message, 'error')
            elif nueva_contrasena != confirmar_contrasena:
                flash('Error: Las contraseñas no coinciden.', 'error')
            else:
                hashed_password = generate_password_hash(nueva_contrasena)
                cur.execute(
                    "UPDATE user SET password = %s, reset_token = NULL WHERE id = %s",
                    (hashed_password, token_user_id),
                )
                mysql.connection.commit()
                flash('Contraseña actualizada correctamente.', 'success')
                return redirect(url_for('login'))
    finally:
        cur.close()

    return render_template('changepassword.jinja')
#---------------Rutas para logout, paginas protegidas, pagina de start y home -----------------------------------


@app.route('/home')   
def home():
    return render_template('home.jinja')

#----------------------Rutas para error 401 y 404--------------------

def status_401(error):
    return redirect(url_for('login'))


def status_404(error):
    return "<h1>Página no encontrada error 404</h1><h2>También puede ser un problema con las rutas</h2>", 404


# Init extensions before app.run() — otherwise they never register when running locally
csrf.init_app(app)
app.register_error_handler(401, status_401)
app.register_error_handler(404, status_404)

# Alias some WSGI hosts look for
application = app

if __name__ == '__main__':
    app.run()