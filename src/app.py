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


#---------------------------------------------------




@app.route('/')
def index():
    return redirect(url_for('startpage'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User(0, request.form['username'], request.form['password'])
        logged_user = ModelUser.login(mysql, user)
        if logged_user != None:
            if logged_user.password:
                cur = mysql.connection.cursor()
                cur.execute("SELECT tipousuario FROM user WHERE id=%s", (logged_user.id,))
                tipoUsuario = cur.fetchone()[0]
                cur.close()
                
                login_user(logged_user)
                if tipoUsuario == 3:
                    return redirect(url_for('clients'))
                elif tipoUsuario == 1:
                    return redirect(url_for('home'))
                else:
                    flash("Tu tipo de usuario no te permite ingresar a esta pagina")
                    return redirect(url_for('login'))
            else:
                flash("Invalid password...")
                return render_template('auth/login.html')
        else:
            flash("User not found...")
            return render_template('auth/login.html')
        
    else:
        return render_template('auth/login.html')
    
    
    
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
                return redirect(url_for('home'))
            else:
                flash("Invalid password...")
                return render_template('auth/loginadm.html')
        else:
            flash("User not found...")
            return render_template('auth/loginadm.html')
        
    else:
        return render_template('auth/loginadm.html')
    
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
    
@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('startpage'))

@app.route('/clients')
def clients():
    return render_template('clientuser/clients.html')

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


#-----------------Rutas para listar clientes ---------------------

@app.route('/administration/employeesales')
def employeesales():
        
    cur = mysql.connection.cursor()

    cur.execute("SELECT id, username, fullname, email FROM user WHERE tipousuario = 2 AND areaUsuario = 2")

    users = cur.fetchall()

    cur.close()

    return render_template('/administration/employeesales.html', users=users)


@app.route('/administration/employeestorage')
def employeestorage():
        
    cur = mysql.connection.cursor()

    cur.execute("SELECT id, username, fullname, email FROM user WHERE tipousuario = 2 AND areaUsuario = 3")

    users = cur.fetchall()

    cur.close()

    return render_template('/administration/employeestorage.html', users=users)


@app.route('/administration/employeemanteinance')
def employeemanteinance():
        
    cur = mysql.connection.cursor()

    cur.execute("SELECT id, username, fullname, email FROM user WHERE tipousuario = 2 AND areaUsuario = 5")

    users = cur.fetchall()

    cur.close()

    return render_template('/administration/employeemanteinance.html', users=users)


@app.route('/administration/employeeshippings')
def employeeshippings():
        
    cur = mysql.connection.cursor()

    cur.execute("SELECT id, username, fullname, email FROM user WHERE tipousuario = 2 AND areaUsuario = 6")

    users = cur.fetchall()

    cur.close()

    return render_template('/administration/employeeshippings.html', users=users)


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
    

    
    
    
