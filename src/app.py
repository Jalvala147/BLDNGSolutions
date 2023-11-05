#Importaciones
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_mysqldb import MySQL
from flask_mail import Mail, Message
import secrets
from flask import render_template_string
from flask_wtf.csrf import CSRFProtect
from flask_login import LoginManager, login_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from salesemp import salesemp
from clients import clients
from maintemp import maintemp
from storageemp import storageemp
from shipemp import shipemp
from admin import admin
import re

app = Flask(__name__)

#app.run(host="0.0.0.0", debug=True, port=8000)
#Blueprints de las otras areas
app.register_blueprint(salesemp)
app.register_blueprint(clients)
app.register_blueprint(maintemp)
app.register_blueprint(storageemp)
app.register_blueprint(shipemp)
app.register_blueprint(admin)

login_manager = LoginManager(app)

from config import config

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

#Checar el archivo config.py tambien

# Configuración de la conexión a la base de datos MySQL
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = ''
app.config['MYSQL_DATABASE_DB'] = 'bdcompleta'

#configuracion para el envio de correos
app.config['MAIL_SERVER']='smtp.googlemail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'bldngsolutions.mail@gmail.com'
app.config['MAIL_PASSWORD'] = 'mxghnyfszbqlaicr'

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
    return render_template('startpage/contact.jinja')

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
    if len(password) < 8:
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
        password = generate_password_hash(request.form['password'], method='sha256')
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
        cur.execute("SELECT id, password, tipousuario FROM user WHERE username=%s", (username,))
        user_data = cur.fetchone()
        cur.close()

        if user_data is not None:
            user_id, hashed_password, tipoUsuario = user_data

            if check_password_hash(hashed_password, password):
                # Contraseña válida, puedes continuar con el inicio de sesión
                logged_user = User(user_id, username, password)
                if tipoUsuario == 3:
                    login_user(logged_user)
                    session['user_id'] = user_id  # Guardar el ID del usuario en la sesión
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
        cur.execute("SELECT id, password, tipousuario FROM user WHERE username=%s", (username,))
        user_data = cur.fetchone()
        cur.close()

        if user_data is not None:
            user_id, hashed_password, tipoUsuario = user_data

            if check_password_hash(hashed_password, password):
                # Contraseña válida, puedes continuar con el inicio de sesión
                logged_user = User(user_id, username, password)
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
                # Contraseña válida, puedes continuar con el inicio de sesión
                logged_user = User(user_id, username, password)

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
def sales_emp_area():
    return render_template('salesEmpArea/salesHome.jinja')

@app.route('/storage_home')
def storage_home():
    return render_template('storage/storageHome.jinja')

@app.route('/maintenance_home')
def maintenance_home():
    return render_template('maintenance/mantHome.jinja')

@app.route('/shipping_home')
def shipping_home():
    return render_template('shipping/shipHome.jinja')



#---------------------------------Ruta para recuperacion de contraseña----------------------------------------------

@app.route('/forgotpassword', methods=['GET', 'POST'])
def forgotpassword():
    cur = mysql.connection.cursor()

    reset_url = None

    if request.method == 'POST':
        # Obtener el correo electrónico ingresado en el formulario
        correo_destinatario = request.form.get('correo')

        # Validar el formato del correo electrónico usando una expresión regular
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

        if not re.match(pattern, correo_destinatario):
            flash('Error: Por favor, ingrese un correo electrónico válido.', 'error')
        else:
            # Buscar el correo en la base de datos
            cur.execute("SELECT * FROM user WHERE email = %s", (correo_destinatario,))
            user = cur.fetchone()


            if user:
                # Generar un token único
                token = secrets.token_hex(16)
            
                # Almacenar el token en la base de datos junto con el usuario
                cur.execute("UPDATE user SET reset_token = %s WHERE id = %s", (token, user[0]))
                mysql.connection.commit()

                # Generar la URL con el token usando url_for
                reset_url = url_for('changepassword', token=token, _external=True)

                # Renderizar la plantilla HTML con Jinja2
                html_content = render_template_string('''
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Recuperación de contraseña</title>
                    <style>
                        body {
                            font-family: Arial, sans-serif;
                            background-color: #f2f2f2;
                        }
                        .container {
                            max-width: 600px;
                            margin: 0 auto;
                            padding: 20px;
                            background-color: #ffffff;
                            border-radius: 5px;
                            box-shadow: 0px 0px 10px rgba(0, 0, 0, 0.1);
                        }
                        h1 {
                            color: #ff0000;
                        }
                        p {
                            color: #333333;
                            line-height: 1.6;
                        }
                        a {
                            color: #0000ff;
                            text-decoration: none;
                        }
                        a:hover {
                            text-decoration: underline;
                        }
                        .btn {
                            display: inline-block;
                            padding: 10px 20px;
                            background-color: #ff0000;
                            color: #ffffff;
                            text-decoration: none;
                            border-radius: 5px;
                        }
                        .btn:hover {
                            background-color: #0000ff;
                        }
                    </style>
                </head>
                <body>
                    <div class="container">
                        <h1>Recuperación de contraseña</h1>
                        <p>Se ha solicitado un cambio de contraseña para su cuenta de BuildingSolutions. Si usted no ha solicitado este cambio, por favor ignore este correo. Si desea cambiar su contraseña, por favor ingrese al siguiente <a href="{{ reset_url }}">enlace</a>.</p>
                        <p>¡Gracias!</p>
                        <a class="btn" href="{{ reset_url }}">Cambiar Contraseña</a>
                    </div>
                </body>
                </html>
                ''', reset_url=reset_url)

                # Enviar el correo con el contenido HTML renderizado
                msg = Message('Recuperación de contraseña', sender='bldngsolutions.mail@gmail.com', recipients=[correo_destinatario])
                msg.html = html_content
                mail.send(msg)

                # Mostrar mensaje flash en el mismo formulario
                flash('Correo enviado correctamente.', 'success')
            else:
                flash('Error: El correo electrónico no está registrado.', 'error')

    return render_template('auth/forgotpassword.jinja', reset_url=reset_url)


@app.route('/changepassword/<token>', methods=['GET', 'POST'])
def changepassword(token):
    cur = mysql.connection.cursor()
    
    if request.method == 'POST':
        nueva_contrasena = request.form.get('nueva_contrasena')
        confirmar_contrasena = request.form.get('confirmar_contrasena')

        # Verificar si el token es válido
        cur.execute("SELECT id, username FROM user WHERE reset_token = %s", (token,))
        user_data = cur.fetchone()

        if user_data is not None:
            user_id, username = user_data

            # Verificar la nueva contraseña usando la función verificar_contrasena
            error_message = verificar_contrasena(nueva_contrasena)

            if error_message is None:
                if nueva_contrasena == confirmar_contrasena:
                    # Hashear la nueva contraseña
                    hashed_password = generate_password_hash(nueva_contrasena, method='sha256')

                    # Actualizar la contraseña hasheada y borrar el token
                    cur.execute("UPDATE user SET password = %s, reset_token = NULL WHERE id = %s", (hashed_password, user_id))
                    mysql.connection.commit()

                    flash('Contraseña actualizada correctamente.', 'success')
                    return redirect('/loginclient')
                else:
                    flash('Error: Las contraseñas no coinciden.', 'error')
            else:
                flash('Error: ' + error_message, 'error')
        else:
            flash('Error: El token no es válido.', 'error')

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

if __name__ == '__main__':
    app.config.from_object(config['development'])
    csrf.init_app(app)
    app.register_error_handler(401, status_401)
    app.register_error_handler(404, status_404)
    app.run()
    