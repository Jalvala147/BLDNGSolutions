from flask import Flask, render_template, request, redirect, url_for, flash
from flask_mysqldb import MySQL
from flask_wtf.csrf import CSRFProtect
from flask_login import LoginManager, login_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
import os




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

#-----------------------------------------------------
#--------CRUD EMPLEADOS MANTENIMIENTO-----------------
#-----------------------------------------------------

# Vista para listar todos los empleados mantenimiento
@app.route('/administration/maintListEmp')
def maintListEmp():
    cur = mysql.connection.cursor()
    cur.execute("SELECT id, username, fullname, email FROM user WHERE tipousuario = 2 AND areaUsuario = 5")
    users = cur.fetchall()
    cur.close()
    return render_template('administration/maintListEmp.html', users=users)


# Vista para agregar un empleado
@csrf.exempt
@app.route('/administration/maintAddEmp', methods=['GET', 'POST'])
def maintAddEmp():
    if request.method == 'POST':
        username = request.form['username']
        fullname = request.form['fullname']
        email = request.form['email']
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO user (username, fullname, email, tipousuario, areaUsuario) VALUES (%s, %s, %s, %s, %s)", (username, fullname, email, 2, 5))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('maintListEmp'))
    return render_template('administration/maintAddEmp.html')


# Vista para eliminar un empleado
@app.route('/administration/maintDeleteEmp/<int:id>', methods=['GET','POST', 'DELETE'])
def maintDeleteEmp(id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM user WHERE id = %s", [id])
    mysql.connection.commit()
    cur.close()
    return redirect(url_for('maintListEmp'))


# Vista para actualizar un empleado
@app.route('/administration/maintUpdateEmp/<int:id>', methods=['GET', 'POST'])
def maintUpdateEmp(id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM user WHERE id = %s", [id])
    user = cur.fetchone()
    cur.close()
    if request.method == 'POST':
        username = request.form['username']
        fullname = request.form['fullname']
        email = request.form['email']
        cur = mysql.connection.cursor()
        cur.execute("UPDATE user SET username=%s, fullname=%s, email=%s WHERE id=%s", (username, fullname, email, id))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('maintListEmp'))
    return render_template('administration/maintUpdateEmp.html', user=user)

#-----------------------------------------------------
#--------CRUD EMPLEADOS VENTAS------------------------
#-----------------------------------------------------

# Vista para listar todos los empleados ventas
@app.route('/administration/salesListEmp')
def salesListEmp():
    cur = mysql.connection.cursor()
    cur.execute("SELECT id, username, fullname, email FROM user WHERE tipousuario = 2 AND areaUsuario = 2")
    users = cur.fetchall()
    cur.close()
    return render_template('administration/salesListEmp.html', users=users)


# Vista para agregar un empleado
@csrf.exempt
@app.route('/administration/salesAddEmp', methods=['GET', 'POST'])
def salesAddEmp():
    if request.method == 'POST':
        username = request.form['username']
        fullname = request.form['fullname']
        email = request.form['email']
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO user (username, fullname, email, tipousuario, areaUsuario) VALUES (%s, %s, %s, %s, %s)", (username, fullname, email, 2, 2))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('salesListEmp'))
    return render_template('administration/salesAddEmp.html')


# Vista para eliminar un empleado
@app.route('/administration/salesDeleteEmp/<int:id>', methods=['GET','POST', 'DELETE'])
def salesDeleteEmp(id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM user WHERE id = %s", [id])
    mysql.connection.commit()
    cur.close()
    return redirect(url_for('salesListEmp'))


# Vista para actualizar un empleado
@app.route('/administration/salesUpdateEmp/<int:id>', methods=['GET', 'POST'])
def salesUpdateEmp(id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM user WHERE id = %s", [id])
    user = cur.fetchone()
    cur.close()
    if request.method == 'POST':
        username = request.form['username']
        fullname = request.form['fullname']
        email = request.form['email']
        cur = mysql.connection.cursor()
        cur.execute("UPDATE user SET username=%s, fullname=%s, email=%s WHERE id=%s", (username, fullname, email, id))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('salesListEmp'))
    return render_template('administration/salesUpdateEmp.html', user=user)


#-----------------------------------------------
#--------CRUD EMPLEADOS Almacén-----------------
#-----------------------------------------------


# Vista para listar todos los empleados almacen
@app.route('/administration/storListEmp')
def storListEmp():
    cur = mysql.connection.cursor()
    cur.execute("SELECT id, username, fullname, email FROM user WHERE tipousuario = 2 AND areaUsuario = 3")
    users = cur.fetchall()
    cur.close()
    return render_template('administration/storListEmp.html', users=users)


# Vista para agregar un empleado
@csrf.exempt
@app.route('/administration/storAddEmp', methods=['GET', 'POST'])
def storAddEmp():
    if request.method == 'POST':
        username = request.form['username']
        fullname = request.form['fullname']
        email = request.form['email']
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO user (username, fullname, email, tipousuario, areaUsuario) VALUES (%s, %s, %s, %s, %s)", (username, fullname, email, 2, 3))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('storListEmp'))
    return render_template('administration/storAddEmp.html')


# Vista para eliminar un empleado
@app.route('/administration/storDeleteEmp/<int:id>', methods=['GET','POST', 'DELETE'])
def storDeleteEmp(id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM user WHERE id = %s", [id])
    mysql.connection.commit()
    cur.close()
    return redirect(url_for('storListEmp'))


# Vista para actualizar un empleado
@csrf.exempt
@app.route('/administration/storUpdateEmp/<int:id>', methods=['GET', 'POST'])
def storUpdateEmp(id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM user WHERE id = %s", [id])
    user = cur.fetchone()
    cur.close()
    if request.method == 'POST':
        username = request.form['username']
        fullname = request.form['fullname']
        email = request.form['email']
        cur = mysql.connection.cursor()
        cur.execute("UPDATE user SET username=%s, fullname=%s, email=%s WHERE id=%s", (username, fullname, email, id))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('storListEmp'))
    return render_template('administration/storUpdateEmp.html', user=user)


#-----------------------------------------------
#--------CRUD EMPLEADOS Envios-----------------
#-----------------------------------------------


# Vista para listar todos los empleados envios
@app.route('/administration/shipListEmp')
def shipListEmp():
    cur = mysql.connection.cursor()
    cur.execute("SELECT id, username, fullname, email FROM user WHERE tipousuario = 2 AND areaUsuario = 6")
    users = cur.fetchall()
    cur.close()
    return render_template('administration/shipListEmp.html', users=users)


# Vista para agregar un empleado
@csrf.exempt
@app.route('/administration/shipAddEmp', methods=['GET', 'POST'])
def shipAddEmp():
    if request.method == 'POST':
        username = request.form['username']
        fullname = request.form['fullname']
        email = request.form['email']
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO user (username, fullname, email, tipousuario, areaUsuario) VALUES (%s, %s, %s, %s, %s)", (username, fullname, email, 2, 6))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('shipListEmp'))
    return render_template('administration/shipAddEmp.html')


# Vista para eliminar un empleado
@app.route('/administration/shipDeleteEmp/<int:id>', methods=['GET','POST', 'DELETE'])
def shipDeleteEmp(id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM user WHERE id = %s", [id])
    mysql.connection.commit()
    cur.close()
    return redirect(url_for('shipListEmp'))


# Vista para actualizar un empleado
@app.route('/administration/shipUpdateEmp/<int:id>', methods=['GET', 'POST'])
def shipUpdateEmp(id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM user WHERE id = %s", [id])
    user = cur.fetchone()
    cur.close()
    if request.method == 'POST':
        username = request.form['username']
        fullname = request.form['fullname']
        email = request.form['email']
        cur = mysql.connection.cursor()
        cur.execute("UPDATE user SET username=%s, fullname=%s, email=%s WHERE id=%s", (username, fullname, email, id))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('shipListEmp'))
    return render_template('administration/shipUpdateEmp.html', user=user)



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

@app.route('/maintenance/mantHome')   
def mantHome():
    return render_template('/maintenance/mantHome.html')
#--------------------rutas ventas-----------------------
@app.route('/sales/clientsList')
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

@app.route('/sales/sales')   
def sales():
    return render_template('/sales/sales.html')

@app.route('/sales/salesHome')   
def salesHome():
    return render_template('/sales/salesHome')

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



    

    
    
    
