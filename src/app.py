from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_mysqldb import MySQL
from flask_mail import Mail, Message
import smtplib
import itsdangerous
from flask_wtf.csrf import CSRFProtect
from flask_login import LoginManager, login_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from salesemp import salesemp
from clients import clients
import re
from maintemp import maintemp
from storageemp import storageemp
from shipemp import shipemp
from admin import admin

app = Flask(__name__)

#app.run(host="127.0.0.1", debug=True, port=5000)

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

@csrf.exempt
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        # Recibir los datos del formulario
        username = request.form['username']
        password = generate_password_hash(request.form['password'], method='sha256')
        fullname = request.form['fullname']
        email = request.form['email']
        tipoUsuario = 3
        areaUsuario = 4
        
        
        # Crear un cursor
        cur = mysql.connection.cursor()
        
        # Ejecutar una consulta SQL para insertar los datos en la tabla de usuarios
        cur.execute("INSERT INTO user (username, password, fullname, email, tipoUsuario, areaUsuario) VALUES (%s, %s, %s, %s, %s, %s)", (username, password, fullname, email, tipoUsuario, areaUsuario))
        
        # Commitear los cambios en la base de datos
        mysql.connection.commit()
        
        # Cerrar el cursor
        cur.close()

        return "Usuario registrado con éxito."

    return render_template('signup.jinja')


#---------------Ruta por defecto /-------------------------

@app.route('/')
def index():
    return redirect(url_for('startpage'))

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
        #print(request.form['username'])
        #print(request.form['password'])
        user = User(0, request.form['username'], request.form['password'])
        logged_user = ModelUser.login(mysql, user)
        if logged_user != None:
            if logged_user.password:
                login_user(logged_user)
                return redirect(url_for('administrationindex'))
            else:
                flash("Invalid password...")
                return render_template('auth/loginadm.jinja')
        else:
            flash("User not found...")
            return render_template('auth/loginadm.jinja')
        
    else:
        return render_template('auth/loginadm.jinja')


#---------------------------------Login para empleados, tipo de usuario 2----------------------------------------------


@app.route('/loginemp', methods=['GET', 'POST'])
def loginemp():
    if request.method == 'POST':
        user = User(0, request.form['username'], request.form['password'])
        logged_user = ModelUser.login(mysql, user)
        
        if logged_user is not None:
            cur = mysql.connection.cursor()
            cur.execute("SELECT tipousuario FROM user WHERE id=%s", (logged_user.id,))
            tipoUsuario = cur.fetchone()[0]
            cur.execute("SELECT areaUsuario FROM user WHERE id=%s", (logged_user.id,))
            idArea = cur.fetchone()[0]
            cur.close()

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

        flash("User not found...")
        return render_template('auth/loginemp.jinja')

    return render_template('auth/loginemp.jinja')

@app.route('/sales_emp_area')
def sales_emp_area():
    # Código necesario para la página "salesEmpArea/salesHome.jinja"
    return render_template('salesEmpArea/salesHome.jinja')

@app.route('/storage_home')
def storage_home():
    # Código necesario para la página "storage/storageHome.jinja"
    return render_template('storage/storageHome.jinja')

@app.route('/maintenance_home')
def maintenance_home():
    # Código necesario para la página "maintenance/mantHome.jinja"
    return render_template('maintenance/mantHome.jinja')

@app.route('/shipping_home')
def shipping_home():
    # Código necesario para la página "shipping/shipHome.jinja"
    return render_template('shipping/shipHome.jinja')



#---------------------------------Ruta para recuperacion de contraseña----------------------------------------------
@app.route('/forgotpassword', methods=['GET', 'POST'])
def forgotpassword():
    if request.method == 'POST':
        # Obtener el correo electrónico ingresado en el formulario
        correo_destinatario = request.form.get('correo')

        # Validar el formato del correo electrónico usando una expresión regular
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

        if not re.match(pattern, correo_destinatario):
            flash('Error: Por favor, ingrese un correo electrónico válido.', 'error')
        else:
            try:
                msg = Message('Recuperación de contraseña', sender='bldngsolutions.mail@gmail.com', recipients=[correo_destinatario])
                #msg.body = 'Se ha solicitado un cambio de contraseña para su cuenta de BuildingSolutions. Si usted no ha solicitado este cambio, por favor ignore este correo. Si desea cambiar su contraseña, por favor ingrese al siguiente link: https://emerging-touched-humpback.ngrok-free.app/changepassword'
                msg.html = '''
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
                        <p>Se ha solicitado un cambio de contraseña para su cuenta de BuildingSolutions. Si usted no ha solicitado este cambio, por favor ignore este correo. Si desea cambiar su contraseña, por favor ingrese al siguiente <a href="https://emerging-touched-humpback.ngrok-free.app/changepassword">enlace</a>.</p>
                        <p>¡Gracias!</p>
                        <a class="btn" href="https://emerging-touched-humpback.ngrok-free.app/changepassword">Cambiar Contraseña</a>
                    </div>
                </body>
                </html>
                '''               
                mail.send(msg)

                # Mostrar mensaje flash en el mismo formulario
                flash('Correo enviado correctamente.', 'success')
            except smtplib.SMTPRecipientsRefused as e:
                flash(f'Error: La dirección de correo electrónico "{correo_destinatario}" no es válida. Por favor, verifique la dirección e inténtelo nuevamente.', 'error')
            except Exception as e:
                flash(f'Error al enviar el correo electrónico: {str(e)}', 'error')

    return render_template('auth/forgotpassword.jinja')

@app.route('/changepassword', methods=['GET', 'POST'])
def changepassword():
    if request.method == 'POST':
        # Obtener el correo electrónico y la nueva contraseña ingresados en el formulario
        correo_destinatario = request.form.get('correo')
        nueva_contrasena = request.form.get('nueva_contrasena')
        confirmar_contrasena = request.form.get('confirmar_contrasena')

        # Aquí debes implementar la lógica para verificar que las contraseñas coincidan
        if nueva_contrasena != confirmar_contrasena:
            flash('Las contraseñas no coinciden.', 'error')
            return render_template('auth/changepassword.jinja') # Redirige al usuario al formulario de cambio de contraseña
        

        flash('Contraseña actualizada correctamente.', 'success')
        return redirect('/login')  # Redirige al usuario a la página de inicio de sesión después de cambiar la contraseña.

    return render_template('auth/changepassword.jinja')
#---------------Rutas para logout, paginas protegidas, pagina de start y home -----------------------------------


@app.route('/startpage')
def startpage():
    return render_template('startpage.jinja')

@app.route('/home')   
def home():
    return render_template('home.jinja')

@app.route('/protected')
@login_required
def protected():
    return "<h1>Esta es una vista protegida, solo para usuarios autenticados.</h1>"







#-----------------Rutas para paginas de Administradores---------------------------
@app.route('/administration/administrationindex')   
def administrationindex():
    return render_template('/administration/administrationindex.jinja')

@app.route('/administration/employeelist')   
def employeelist():
    return render_template('/administration/employeelist.jinja')


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
    
     
#--------------------rutas ventas-----------------------

@app.route('/sales_Home')
def salesHome():
    return render_template('salesEmpArea/salesHome.jinja')

@app.route('/salesEmpArea/clientsList')
def clientsList():
    return render_template('salesEmpArea/clientsList.jinja')

@app.route('/newRequest')   
def newRequest():
    return render_template('/sales/newRequest.jinja')
    
@app.route('/salesEmpArea/prospects')   
def prospects():
    return render_template('templates/sales/prospects.jinja')
    
@app.route('/rents')   
def rents():
    return render_template('/sales/rents.jinja')

@app.route('/sales/sales')   
def sales():
    return render_template('/sales/sales.jinja')

#--------------------rutas envios-----------------------
@app.route('/orders')
def orders():
    return render_template('/shipping/orders.jinja')



