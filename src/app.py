from flask import Flask, render_template, request, redirect, url_for, flash
from flask_mysqldb import MySQL
from flask_wtf.csrf import CSRFProtect
from flask_login import LoginManager, login_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash




from config import config

# Models:
from models.ModelUser import ModelUser

# Entities:
from models.entities.User import User

app = Flask(__name__)


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


#---------------------------------------------------


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

    return render_template('signup.html')


#---------------Ruta por defecto /-------------------------

@app.route('/')
def index():
    return redirect(url_for('startpage'))

#----------------------------Login para clientes, tipo de usuario 3-----------------------------------------------

@app.route('/loginclient', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User(0, request.form['username'], request.form['password'])
        logged_user = ModelUser.login(mysql, user)
        if logged_user is not None:
            cur = mysql.connection.cursor()
            cur.execute("SELECT tipousuario FROM user WHERE id=%s", (logged_user.id,))
            tipoUsuario = cur.fetchone()[0]
            cur.close()

            if tipoUsuario == 3:
                login_user(logged_user)
                return redirect(url_for('clientsHome'))

            flash("Invalid user type...")
            return render_template('auth/loginclient.html')

        flash("User not found...")
        return render_template('auth/loginclient.html')

    return render_template('auth/loginclient.html')

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
                return render_template('auth/loginadm.html')
        else:
            flash("User not found...")
            return render_template('auth/loginadm.html')
        
    else:
        return render_template('auth/loginadm.html')


#---------------------------------Login para empleados, tipo de usuario 2----------------------------------------------
@app.route('/loginemp', methods=['GET', 'POST'])
def loginemp():
    if request.method == 'POST':
        #print(request.form['username'])
        #print(request.form['password'])
        user = User(0, request.form['username'], request.form['password'])
        logged_user = ModelUser.login(mysql, user)
        if logged_user != None:
            if logged_user.password:
                login_user(logged_user)
                return redirect(url_for('home'))
            else:
                flash("Invalid password...")
                return render_template('auth/loginemp.html')
        else:
            flash("User not found...")
            return render_template('auth/loginemp.html')
        
    else:
        return render_template('auth/loginemp.html')

#---------------Rutas para logout, paginas protegidas, pagina de start y home -----------------------------------
    
@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('startpage'))

@app.route('/startpage')
def startpage():
    return render_template('startpage.html')

@app.route('/home')   
def home():
    return render_template('home.html')

@app.route('/protected')
@login_required
def protected():
    return "<h1>Esta es una vista protegida, solo para usuarios autenticados.</h1>"


#-----------------Rutas para listar empleados de ventas ---------------------

@app.route('/administration/employeesales')
def employeesales():
        
    cur = mysql.connection.cursor()

    cur.execute("SELECT id, username, fullname, email FROM user WHERE tipousuario = 2 AND areaUsuario = 2")

    users = cur.fetchall()

    cur.close()

    return render_template('/administration/employeesales.html', users=users)

#-----------------Rutas para listar empleados de almacén ---------------------


@app.route('/administration/employeestorage')
def employeestorage():
        
    cur = mysql.connection.cursor()

    cur.execute("SELECT id, username, fullname, email FROM user WHERE tipousuario = 2 AND areaUsuario = 3")

    users = cur.fetchall()

    cur.close()

    return render_template('/administration/employeestorage.html', users=users)

#-----------------Rutas para listar empleados de mantenimiento ---------------------

@app.route('/administration/employeemanteinance')
def employeemanteinance():
        
    cur = mysql.connection.cursor()

    cur.execute("SELECT id, username, fullname, email FROM user WHERE tipousuario = 2 AND areaUsuario = 5")

    users = cur.fetchall()

    cur.close()

    return render_template('/administration/employeemanteinance.html', users=users)

#-----------------Rutas para listar empleados de envios ---------------------

@app.route('/administration/employeeshippings')
def employeeshippings():
        
    cur = mysql.connection.cursor()

    cur.execute("SELECT id, username, fullname, email FROM user WHERE tipousuario = 2 AND areaUsuario = 6")

    users = cur.fetchall()

    cur.close()

    return render_template('/administration/employeeshippings.html', users=users)



#-----------------Rutas para paginas de Administradores---------------------------
@app.route('/administration/administrationindex')   
def administrationindex():
    return render_template('/administration/administrationindex.html')

@app.route('/administration/employeelist')   
def employeelist():
    return render_template('/administration/employeelist.html')


#----------------------Rutas para error 401 y 404--------------------

def status_401(error):
    return redirect(url_for('login'))


def status_404(error):
    return "<h1>Página no encontrada</h1>", 404

if __name__ == '__main__':
    app.config.from_object(config['development'])
    csrf.init_app(app)
    app.register_error_handler(401, status_401)
    app.register_error_handler(404, status_404)
    app.run()
    
     
#--------------------rutas clientes-----------------------
@app.route('/clientsHome')
def clientsHome():
    return render_template('/clientuser/clientsHome.html')

@app.route('/documentsuser')   
def documentsuser():
    return render_template('/clientuser/documentsuser.html')
    
@app.route('/information')   
def information():
    return render_template('/clientuser/information.html')
    
@app.route('/payments')   
def payments():
    return render_template('/clientuser/payments.html')
    
@app.route('/statusprogress')   
def statusprogress():
    return render_template('/clientuser/statusprogress.html')

#--------------------rutas mantenimiento-----------------------
@app.route('/mantHistory')
def mantHistory():
    return render_template('maintenance/mantHistory.html')

@app.route('/mantMachines')   
def mantMachines():
    return render_template('/maintenance/mantMachines.html')
    
@app.route('/mantManteinance')   
def mantManteinance():
    return render_template('/maintenance/mantManteinance.html')
    
@app.route('/mantReports')   
def mantReports():
    return render_template('/maintenance/mantReports.html')

#--------------------rutas ventas-----------------------
@app.route('/clientsList')
def clientsList():
    return render_template('/sales/clientsList.html')

@app.route('/newRequest')   
def newRequest():
    return render_template('/sales/newRequest.html')
    
@app.route('/prospects')   
def prospects():
    return render_template('/sales/prospects.html')
    
@app.route('/rents')   
def rents():
    return render_template('/sales/rents.html')

@app.route('/sales')   
def sales():
    return render_template('/sales/sales.html')

@app.route('/salesHome')   
def salesHome():
    return render_template('/sales/salesHome.html')

#--------------------rutas envios-----------------------
@app.route('/orders')
def orders():
    return render_template('/shipping/orders.html')

#--------------------rutas almacén-----------------------
@app.route('/history')
def history():
    return render_template('/storage/history.html')

@app.route('/machines')   
def machines():
    return render_template('/storage/machines.html')
    
@app.route('/maintenance')   
def prospects():
    return render_template('/storage/maintenance.html')




    

    
    
    
