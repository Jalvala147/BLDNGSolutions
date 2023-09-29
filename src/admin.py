from flask_mysqldb import MySQL
from flask import render_template, session, redirect, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Blueprint
from flask import url_for
from flask_wtf.csrf import CSRFProtect
from flask import request
from flask import Flask
from flask_login import login_required
#import pandas as pd

import numpy as np
import matplotlib.pyplot as plt
from io import BytesIO
import base64


from sklearn.linear_model import LinearRegression

import plotly.graph_objs as go
import plotly.offline as opy

import plotly.express as px
import pandas as pd
import numpy as np

admin = Flask(__name__)
mysql = MySQL()

csrf = CSRFProtect()

admin = Blueprint('admin', __name__)


#--------------------rutas administracion-----------------------
@admin.route('/administration/administrationindex')
def adminHome():
    return render_template('administration/administrationindex.jinja')


@admin.route('/administration/employeelist')
def employeelist():
    return render_template('administration/employeelist.jinja')


#---------------Control de accesos----------------------------------

@admin.route('/administration/accesscontrol')
def accesscontrol():
    return render_template('administration/empAccessControl/accessControl.jinja')





#-------------------------------------------------

@admin.route('/administration/projectionsResults')
def projectionsResults():

    return render_template('administration/stats/projectionsResults.jinja')


@admin.route('/administration/profitsProjections') #esto es solo un ejemplo sobre la regresion lineal
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
def lossResults():
    return render_template('administration/stats/lossResults.jinja')

@admin.route('/administration/lossProjections')
def lossProjections():
    return render_template('administration/stats/lossProjections.jinja')


@admin.route('/administration/profitabilityProjections')
def profitabilityProjections():
    return render_template('administration/stats/profitabilityProjections.jinja')


@admin.route('/administration/profitabilityResults')
def profitabilityResults():
    return render_template('administration/stats/profitabilityResults.jinja')




#-----------------------------------------------------
#--------CRUD EMPLEADOS MANTENIMIENTO-----------------
#-----------------------------------------------------

# Vista para listar todos los empleados mantenimiento
@admin.route('/administration/maintListEmp')
def maintListEmp():
    cur = mysql.connection.cursor()
    cur.execute("SELECT id, username, fullname, email FROM user WHERE tipousuario = 2 AND areaUsuario = 5")
    users = cur.fetchall()
    cur.close()
    return render_template('administration/maintListEmp.jinja', users=users)


# Vista para agregar un empleado
@csrf.exempt
@admin.route('/administration/maintAddEmp', methods=['GET', 'POST'])
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
        
        return "Empleado de mantenimiento registrado con éxito."

    return render_template('administration/maintAddEmp.jinja')


# Vista para eliminar un empleado
@admin.route('/administration/maintDeleteEmp/<int:id>', methods=['GET','POST', 'DELETE'])
def maintDeleteEmp(id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM user WHERE id = %s", [id])
    mysql.connection.commit()
    cur.close()
    return redirect(url_for('admin.maintListEmp'))


# Vista para actualizar un empleado
@admin.route('/administration/maintUpdateEmp/<int:id>', methods=['GET', 'POST'])
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
def salesListEmp():
    cur = mysql.connection.cursor()
    cur.execute("SELECT id, username, fullname, email FROM user WHERE tipousuario = 2 AND areaUsuario = 2")
    users = cur.fetchall()
    cur.close()
    return render_template('administration/salesListEmp.jinja', users=users)


# Vista para agregar un empleado
@csrf.exempt
@admin.route('/administration/salesAddEmp', methods=['GET', 'POST'])
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
        
        return "Empleado de ventas registrado con éxito."

    return render_template('administration/salesAddEmp.jinja')


# Vista para eliminar un empleado
@admin.route('/administration/salesDeleteEmp/<int:id>', methods=['GET','POST', 'DELETE'])
def salesDeleteEmp(id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM user WHERE id = %s", [id])
    mysql.connection.commit()
    cur.close()
    return redirect(url_for('admin.salesListEmp'))


# Vista para actualizar un empleado
@admin.route('/administration/salesUpdateEmp/<int:id>', methods=['GET', 'POST'])
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
def storListEmp():
    cur = mysql.connection.cursor()
    cur.execute("SELECT id, username, fullname, email FROM user WHERE tipousuario = 2 AND areaUsuario = 3")
    users = cur.fetchall()
    cur.close()
    return render_template('administration/storListEmp.jinja', users=users)


# Vista para agregar un empleado
@csrf.exempt
@login_required
@admin.route('/administration/storAddEmp', methods=['GET', 'POST'])
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
        
        return "Empleado de almacén registrado con éxito."

    return render_template('administration/storAddEmp.jinja')



# Vista para eliminar un empleado
@admin.route('/administration/storDeleteEmp/<int:id>', methods=['GET','POST', 'DELETE'])
def storDeleteEmp(id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM user WHERE id = %s", [id])
    mysql.connection.commit()
    cur.close()
    return redirect(url_for('admin.storListEmp'))


# Vista para actualizar un empleado
@csrf.exempt
@admin.route('/administration/storUpdateEmp/<int:id>', methods=['GET', 'POST'])
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
def shipListEmp():
    cur = mysql.connection.cursor()
    cur.execute("SELECT id, username, fullname, email FROM user WHERE tipousuario = 2 AND areaUsuario = 6")
    users = cur.fetchall()
    cur.close()
    return render_template('administration/shipListEmp.jinja', users=users)


# Vista para agregar un empleado
@csrf.exempt
@admin.route('/administration/shipAddEmp', methods=['GET', 'POST'])
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
def shipDeleteEmp(id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM user WHERE id = %s", [id])
    mysql.connection.commit()
    cur.close()
    return redirect(url_for('admin.shipListEmp'))


# Vista para actualizar un empleado
@admin.route('/administration/shipUpdateEmp/<int:id>', methods=['GET', 'POST'])
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