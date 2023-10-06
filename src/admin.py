from flask_mysqldb import MySQL
from flask import render_template, session, redirect, flash
from werkzeug.security import generate_password_hash
from flask import Blueprint
from flask import url_for
from flask_wtf.csrf import CSRFProtect
from flask import request
from flask import Flask
from flask_login import login_required, current_user
from functools import wraps

import matplotlib.pyplot as plt


from sklearn.linear_model import LinearRegression

import plotly.express as px
import pandas as pd
import numpy as np

admin = Flask(__name__)
mysql = MySQL()

csrf = CSRFProtect()

admin = Blueprint('admin', __name__)


#Decorador para que solo los administradores puedan acceder a sus rutas
def admin_required(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if not current_user.is_authenticated or current_user.tipoUsuario != 1:
            flash("Acceso no autorizado. Inicia sesión como administrador.")
            return redirect(url_for('loginadm'))  
        return func(*args, **kwargs)
    return decorated_view

#--------------------rutas administracion-----------------------
@admin.route('/administration/administrationindex')
def adminHome():
    return render_template('administration/administrationindex.jinja')


@admin.route('/administration/employeelist')
def employeelist():
    return render_template('administration/employeelist.jinja')


#---------------Control de accesos----------------------------------

@admin.route('/administration/accessControl')
@admin_required
def accesscontrol():
    cur = mysql.connection.cursor()
    cur.execute("SELECT id, username, fullname, email, areaUsuario FROM user WHERE tipousuario = 2")
    users = cur.fetchall()
    cur.close()
    return render_template('administration/empAccessControl/accessControl.jinja', users=users)


@admin.route('/administration/accessHistory/<int:id>/<string:name>')
@admin_required
def accessHistory(id, name):
    return render_template('administration/empAccessControl/accessHistory.jinja', id=id, name=name)


#-------------------------------------------------

@admin.route('/administration/projectionsResults')
@admin_required
def projectionsResults():

    return render_template('administration/stats/projectionsResults.jinja')


@admin.route('/administration/profitsProjections') #esto es solo un ejemplo sobre la regresion lineal
@admin_required
def profitsProjections():
    # Generar datos de ejemplo
    np.random.seed(0)
    X = 2 * np.random.rand(100, 1)
    y = 4 + 3 * X + np.random.rand(100, 1)

    # Crear un modelo de regresión lineal
    model = LinearRegression()
    model.fit(X, y)

    # Preparar datos para la gráfica
    df = pd.DataFrame({'X': X.squeeze(), 'y': y.squeeze()})
    df['y_pred'] = model.predict(X)

    # Crear una gráfica interactiva con Plotly Express
    fig = px.scatter(df, x='X', y='y', title='Precios unitarios')
    fig.add_scatter(x=df['X'], y=df['y_pred'], mode='lines', name='Proyección')

    # Convertir la figura de Plotly a HTML
    graph_html = fig.to_html(full_html=False)
    # Renderiza la plantilla Jinja2 con la gráfica incrustada
    return render_template('administration/stats/profitsProjections.jinja', graph_html=graph_html)


@admin.route('/administration/profitsResults', methods=['GET', 'POST'])
@admin_required
def profitsResults():
    try:
        # Establecer una conexión a la base de datos
        cur = mysql.connection.cursor()

        # Obtener todos los meses disponibles
        cur.execute("SELECT DISTINCT DATE_FORMAT(order_date, '%Y-%m') as month FROM orders")
        months = [row[0] for row in cur.fetchall()]

        ganancias_totales_mes = None

        if request.method == 'POST':
            # El usuario ha seleccionado un mes
            selected_month = request.form['month']

            # Consulta SQL para obtener las ganancias del mes seleccionado
            sql_query = """
                SELECT id, total as ganancias
                FROM orders
                WHERE verifiedDocs = 1 AND paymentMade = 1 AND shipmentMade = 1
                AND DATE_FORMAT(order_date, '%%Y-%%m') = %s
            """
            cur.execute(sql_query, [selected_month])
            ganancias = cur.fetchall()

            # Calcular la suma total de las ganancias para el mes seleccionado
            ganancias_totales_mes = sum(g[1] for g in ganancias)

            # Cerrar la conexión a la base de datos
            cur.close()

            # Crear un DataFrame de pandas con las ganancias
            df_ganancias = pd.DataFrame(ganancias, columns=['No. Orden', 'ganancias']).set_index('No. Orden')

            # Crear una gráfica de líneas para las ganancias
            fig_ganancias = px.line(df_ganancias, x=df_ganancias.index, y='ganancias', title='Ganancias de ' + selected_month)
            fig_ganancias.update_xaxes(
                tickmode = 'array',
                tickvals = df_ganancias.index,
                dtick = 1
            )
            
            # Convertir la figura de Plotly a HTML
            graph_html_ganancias = fig_ganancias.to_html(full_html=False)
        else:
            # No se ha seleccionado un mes, no mostrar ninguna gráfica
            graph_html_ganancias = None

        return render_template(
            'administration/stats/profitsResults.jinja',
            months=months,
            ganancias_totales_mes=ganancias_totales_mes,
            graph_html_ganancias=graph_html_ganancias
        )

    except Exception as e:
        return f"Error al calcular las ganancias: {str(e)}"


@admin.route('/administration/lossResults')
@admin_required
def lossResults():
    return render_template('administration/stats/lossResults.jinja')

@admin.route('/administration/lossProjections')
@admin_required
def lossProjections():
    return render_template('administration/stats/lossProjections.jinja')


@admin.route('/administration/profitabilityProjections')
@admin_required
def profitabilityProjections():
    return render_template('administration/stats/profitabilityProjections.jinja')


@admin.route('/administration/profitabilityResults')
@admin_required
def profitabilityResults():
    return render_template('administration/stats/profitabilityResults.jinja')




#-----------------------------------------------------
#--------CRUD EMPLEADOS MANTENIMIENTO-----------------
#-----------------------------------------------------

# Vista para listar todos los empleados mantenimiento
@admin.route('/administration/maintListEmp')
@admin_required
def maintListEmp():
    cur = mysql.connection.cursor()
    cur.execute("SELECT id, username, fullname, email FROM user WHERE tipousuario = 2 AND areaUsuario = 5")
    users = cur.fetchall()
    cur.close()
    return render_template('administration/maintListEmp.jinja', users=users)


# Vista para agregar un empleado✅
 
@admin.route('/administration/maintAddEmp', methods=['GET', 'POST'])
@admin_required
def maintAddEmp():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'], method='sha256')
        fullname = request.form['fullname']
        email = request.form['email']
        tipoUsuario = 2  # El valor 'tipoUsuario' se establece en 2 para empleados de mantenimiento
        areaUsuario = 5  # El valor 'areaUsuario' se establece en 5 para empleados de mantenimiento
        
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO user (username, password, fullname, email, tipousuario, areaUsuario) VALUES (%s, %s, %s, %s, %s, %s)", (username, password, fullname, email, tipoUsuario, areaUsuario))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('admin.maintListEmp'))
    return render_template('administration/maintAddEmp.jinja')


# Vista para eliminar un empleado✅
@admin.route('/administration/maintDeleteEmp/<int:id>', methods=['GET','POST', 'DELETE'])
@admin_required
def maintDeleteEmp(id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM user WHERE id = %s", [id])
    mysql.connection.commit()
    cur.close()
    return redirect(url_for('admin.maintListEmp'))


# Vista para actualizar un empleado✅
@admin.route('/administration/maintUpdateEmp/<int:id>', methods=['GET', 'POST'])
@admin_required
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
        return redirect(url_for('admin.maintListEmp'))
    return render_template('administration/maintUpdateEmp.jinja', user=user)

#-----------------------------------------------------
#--------CRUD EMPLEADOS VENTAS------------------------
#-----------------------------------------------------

# Vista para listar todos los empleados ventas
@admin.route('/administration/salesListEmp')
@admin_required
def salesListEmp():
    cur = mysql.connection.cursor()
    cur.execute("SELECT id, username, fullname, email FROM user WHERE tipousuario = 2 AND areaUsuario = 2")
    users = cur.fetchall()
    cur.close()
    return render_template('administration/salesListEmp.jinja', users=users)


# Vista para agregar un empleado
 
@admin.route('/administration/salesAddEmp', methods=['GET', 'POST'])
@admin_required
def salesAddEmp():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'], method='sha256')
        fullname = request.form['fullname']
        email = request.form['email']
        tipoUsuario = 2  # El valor 'tipoUsuario' se establece en 2 para empleados de ventas
        areaUsuario = 2  # El valor 'areaUsuario' se establece en 2 para empleados de ventas
        
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO user (username, password, fullname, email, tipousuario, areaUsuario) VALUES (%s, %s, %s, %s, %s, %s)", (username, password, fullname, email, tipoUsuario, areaUsuario))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('admin.salesListEmp'))
    return render_template('administration/salesAddEmp.jinja')


# Vista para eliminar un empleado
@admin.route('/administration/salesDeleteEmp/<int:id>', methods=['GET','POST', 'DELETE'])
@admin_required
def salesDeleteEmp(id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM user WHERE id = %s", [id])
    mysql.connection.commit()
    cur.close()
    return redirect(url_for('admin.salesListEmp'))


# Vista para actualizar un empleado
@admin.route('/administration/salesUpdateEmp/<int:id>', methods=['GET', 'POST'])
@admin_required
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
        return redirect(url_for('admin.salesListEmp'))
    return render_template('administration/salesUpdateEmp.jinja', user=user)


#-----------------------------------------------
#--------CRUD EMPLEADOS Almacén-----------------
#-----------------------------------------------


# Vista para listar todos los empleados almacen
@admin.route('/administration/storListEmp')
@admin_required
def storListEmp():
    cur = mysql.connection.cursor()
    cur.execute("SELECT id, username, fullname, email FROM user WHERE tipousuario = 2 AND areaUsuario = 3")
    users = cur.fetchall()
    cur.close()
    return render_template('administration/storListEmp.jinja', users=users)


# Vista para agregar un empleado
 
@admin.route('/administration/storAddEmp', methods=['GET', 'POST'])
@admin_required
def storAddEmp():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'], method='sha256')
        fullname = request.form['fullname']
        email = request.form['email']
        tipoUsuario = 2  # El valor 'tipoUsuario' se establece en 2 para empleados de almacén
        areaUsuario = 3  # El valor 'areaUsuario' se establece en 3 para empleados de almacén
        
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO user (username, password, fullname, email, tipousuario, areaUsuario) VALUES (%s, %s, %s, %s, %s, %s)", (username, password, fullname, email, tipoUsuario, areaUsuario))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('admin.storListEmp'))
    return render_template('administration/storAddEmp.jinja')



# Vista para eliminar un empleado
@admin.route('/administration/storDeleteEmp/<int:id>', methods=['GET','POST', 'DELETE'])
@admin_required
def storDeleteEmp(id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM user WHERE id = %s", [id])
    mysql.connection.commit()
    cur.close()
    return redirect(url_for('admin.storListEmp'))


# Vista para actualizar un empleado
 
@admin.route('/administration/storUpdateEmp/<int:id>', methods=['GET', 'POST'])
@admin_required
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
        return redirect(url_for('admin.storListEmp'))
    return render_template('administration/storUpdateEmp.jinja', user=user)


#-----------------------------------------------
#--------CRUD EMPLEADOS Envios-----------------
#-----------------------------------------------


# Vista para listar todos los empleados envios
@admin.route('/administration/shipListEmp')
@admin_required
def shipListEmp():
    cur = mysql.connection.cursor()
    cur.execute("SELECT id, username, fullname, email FROM user WHERE tipousuario = 2 AND areaUsuario = 6")
    users = cur.fetchall()
    cur.close()
    return render_template('administration/shipListEmp.jinja', users=users)


# Vista para agregar un empleado de envios✅
 
@admin.route('/administration/shipAddEmp', methods=['GET', 'POST'])
@admin_required
def shipAddEmp():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'], method='sha256')   
        fullname = request.form['fullname']
        email = request.form['email']
        tipoUsuario = 2  # El valor 'tipoUsuario' se establece en 2 para empleados de envios
        areaUsuario = 6  # El valor 'areaUsuario' se establece en 6 para empleados de envios

        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO user (username, password, fullname, email, tipousuario, areaUsuario) VALUES (%s, %s, %s, %s, %s, %s)", (username, password, fullname, email, tipoUsuario, areaUsuario))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('admin.shipListEmp'))
    return render_template('administration/shipAddEmp.jinja')


# Vista para eliminar un empleado
@admin.route('/administration/shipDeleteEmp/<int:id>', methods=['GET','POST', 'DELETE'])
@admin_required
def shipDeleteEmp(id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM user WHERE id = %s", [id])
    mysql.connection.commit()
    cur.close()
    return redirect(url_for('admin.shipListEmp'))


# Vista para actualizar un empleado✅
@admin.route('/administration/shipUpdateEmp/<int:id>', methods=['GET', 'POST'])
@admin_required
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
        return redirect(url_for('admin.shipListEmp'))
    return render_template('administration/shipUpdateEmp.jinja', user=user)

#--------------CRUD Prospectos-----------------------------------
# Vista para listar todos los prospectos
@admin.route('/administration/prospects')
# @admin_required
def prospects():
    cur = mysql.connection.cursor()
    cur.execute("SELECT id_Prospect, fullname, company, number, email FROM prospects WHERE contacted = 0")
    prospects = cur.fetchall()
    cur.close()
    return render_template('administration/prospects.jinja', prospects=prospects)

# Vista para agregar un prospecto
@admin.route('/administration/addProspect', methods=['GET', 'POST'])
@admin_required
def addProspect():
    if request.method == 'POST':
        # Recupera los datos del formulario
        fullname = request.form['fullname']
        company = request.form['company']  
        number = request.form['number']
        email = request.form['email']
        
        # Realiza la inserción en la tabla de prospects
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO prospects (fullname, company, number, email) VALUES (%s, %s, %s, %s)", (fullname, company, number, email))
        mysql.connection.commit()
        cur.close()
        
        return redirect(url_for('admin.prospects'))
    
    return render_template('administration/addProspect.jinja')

# Vista para actualizar un prospecto
@admin.route('/administration/updateProspect/<int:id>', methods=['GET', 'POST'])
@admin_required
def updateProspect(id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM prospects WHERE id_Prospect = %s", [id])
    prospect = cur.fetchone()
    cur.close()
    if request.method == 'POST':
        fullname = request.form['fullname']
        company = request.form['company'] 
        number = request.form['number']
        email = request.form['email']
        cur = mysql.connection.cursor()
        cur.execute("UPDATE prospects SET fullname=%s, company=%s, number=%s, email=%s WHERE id_Prospect=%s", (fullname, company, number, email, id))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('admin.prospects'))
    return render_template('administration/updateProspect.jinja', prospects=prospect)

# Vista para eliminar un prospecto
@admin.route('/administration/deleteProspect/<int:id>', methods=['GET', 'POST', 'DELETE'])
@admin_required
def deleteProspect(id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM prospects WHERE id_Prospect = %s", [id])
    mysql.connection.commit()
    cur.close()
    return redirect(url_for('admin.prospects'))
    
# Vista para listar todos los prospectos contactados
@admin.route('/administration/contactedProspectsList')
@admin_required
def contactedProspectsList():
    cur = mysql.connection.cursor()
    cur.execute("SELECT id_Prospect, fullname, company, number, email FROM prospects WHERE contacted = 1")
    prospects = cur.fetchall()
    cur.close()
    return render_template('administration/contactedProspects.jinja', prospects=prospects)

#----------------RUD Clientes--------------------------

# Vista para listar todos los clientes
@admin.route('/administration/clientsList')
@admin_required
def clientsList():
    cur = mysql.connection.cursor()
    cur.execute("SELECT id, username, fullname, email FROM user WHERE tipousuario = 3 AND areaUsuario = 4")
    users = cur.fetchall()
    cur.close()
    return render_template('administration/clients/clientsList.jinja', users=users)

# Vista para editar un cliente existente
@admin.route('/administration/editClient/<int:id>', methods=['GET', 'POST'])
@admin_required
def editClient(id):
    if request.method == 'POST':
        # Obtener los datos del formulario
        username = request.form['username']
        fullname = request.form['fullname']
        email = request.form['email']

        # Actualizar el cliente en la base de datos
        cur = mysql.connection.cursor()
        cur.execute("UPDATE user SET username = %s, fullname = %s, email = %s WHERE id = %s", (username, fullname, email, id))
        mysql.connection.commit()
        cur.close()

        # Redirigir a la página de listado de clientes después de editar el cliente
        return redirect(url_for('admin.clientsList'))
    else:
        # Obtener los detalles actuales del cliente de la base de datos
        cur = mysql.connection.cursor()
        cur.execute("SELECT id, username, fullname, email FROM user WHERE id = %s", [id])
        user_details = cur.fetchone()
        cur.close()

        # Mostrar el formulario de edición con los detalles actuales del cliente
        return render_template('administration/clients/editClient.jinja', user=user_details)
    
# Vista para eliminar un cliente
@admin.route('/administration/deleteClient/<int:id>', methods=['GET', 'POST', 'DELETE'])
@admin_required
def deleteClient(id):
        # Elimina los registros relacionados en la tabla 'files'
        cur = mysql.connection.cursor()
        cur.execute("DELETE FROM files WHERE user_id = %s", [id])
        mysql.connection.commit()
        
        # Luego, elimina al cliente de la tabla 'user'
        cur.execute("DELETE FROM user WHERE id = %s", [id])
        mysql.connection.commit()
        cur.close()
        
        # Redirige al listado de clientes después de la eliminación
        return redirect(url_for('admin.clientsList'))


