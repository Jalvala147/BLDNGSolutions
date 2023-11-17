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
from datetime import datetime, timedelta
import calendar
import locale
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objs as go
import plotly.express as px
import plotly.subplots as sp
from plotly.subplots import make_subplots
from plotly.offline import plot
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split

from datetime import datetime
from dateutil.relativedelta import relativedelta


admin = Flask(__name__)
mysql = MySQL()

csrf = CSRFProtect()

admin = Blueprint('admin', __name__)

locale.setlocale(locale.LC_TIME, 'es_ES.utf8') #indicamos a locale que se está usando el sistema en español

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
@admin_required
def adminHome():
    try:
        cursor = mysql.connection.cursor()

        # Query con JOIN y condición WHERE para filtrar por bonus igual a 1
        query = "SELECT u.fullname, u.areaUsuario, p.bonus, p.datetime, p.id_bonus FROM payroll p JOIN user u ON p.employee_id = u.id WHERE p.bonus = 1"
        cursor.execute(query)
        data = cursor.fetchall()
        cursor.close()

        return render_template('administration/administrationindex.jinja', data=data)
    except Exception as e:
        return str(e), 500
    
@admin.route('/update_bonus/<int:bonus_id>', methods=['POST'])
@admin_required
def update_bonus(bonus_id):
    try:
        cursor = mysql.connection.cursor()
        query = "UPDATE payroll SET bonus = 0 WHERE id_bonus = %s"
        cursor.execute(query, (bonus_id,))
        mysql.connection.commit()
        cursor.close()
        return redirect(url_for('admin.adminHome'))
    except Exception as e:
        return str(e), 500


#renderiza la Plantilla que muestra las areas de la empresa y dentro de ellas, sus empleados
@admin.route('/administration/employeelist')
@admin_required
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
    cur = mysql.connection.cursor()

    cur.execute("SELECT DISTINCT DATE_FORMAT(date_time, '%Y-%m') AS month FROM access_records")
    months = cur.fetchall()

    selected_month = request.args.get('month') 

    selected_period = request.args.get('period') 

    sql = """
    SELECT access_records.date_time, access_records.status, user.areaUsuario
    FROM user
    LEFT JOIN access_records ON user.id = access_records.fingerprint_id
    WHERE user.id = %s
    """
    if selected_month:
        if selected_period == 'mes':
            sql += " AND DATE_FORMAT(access_records.date_time, '%Y-%m') = %s"
        elif selected_period == 'quincena1':
            sql += " AND DAY(access_records.date_time) <= 15 AND DATE_FORMAT(access_records.date_time, '%Y-%m') = %s"
        elif selected_period == 'quincena2':
            sql += " AND DAY(access_records.date_time) > 15 AND DATE_FORMAT(access_records.date_time, '%Y-%m') = %s"
        cur.execute(sql, (id, selected_month))
    else:
        cur.execute(sql, (id,))

    access_records = cur.fetchall()
    cur.close()

    return render_template(
        'administration/empAccessControl/accessHistory.jinja', 
        id=id, 
        name=name, 
        access_records=access_records, 
        months=months, 
        selected_month=selected_month, 
        selected_period=selected_period
    )



# Función para calcular la puntualidad
def calcular_puntualidad(access_records):
    hora_entrada_esperada = datetime.strptime("08:00:00", "%H:%M:%S")
    hora_entrada_inicial = hora_entrada_esperada - timedelta(minutes=30)
    hora_entrada_limite = hora_entrada_esperada + timedelta(minutes=15)

    resultados_puntualidad = []

    for access in access_records:
        fecha_hora_registro = access[0] 

        # Aseguramos de que la fecha no afecte la comparación, considerando solo la hora
        hora_registro = fecha_hora_registro.time()

        if hora_entrada_inicial.time() <= hora_registro <= hora_entrada_limite.time():
            puntualidad = "A tiempo"
        else:
            puntualidad = "Tarde"

        resultados_puntualidad.append({"fecha_hora": fecha_hora_registro, "puntualidad": puntualidad})

    return resultados_puntualidad



def obtener_access_records(empleado_id):
    cur = mysql.connection.cursor()

    # Consulta para obtener los registros de acceso del empleado con el id proporcionado
    sql = """
    SELECT date_time, status
    FROM access_records
    WHERE fingerprint_id = %s AND status = 1
    ORDER BY date_time
    """
    cur.execute(sql, (empleado_id,))

    access_records = cur.fetchall()
    cur.close()

    return access_records


# Ruta para mostrar los resultados de puntualidad para un empleado específico
@admin.route('/administration/empAccessControl/employeeResults/<int:id>/<string:name>')
@admin_required
def employeeResults(id, name):
    access_records = obtener_access_records(id)  

    # Llama a la función para calcular la puntualidad
    resultados_puntualidad = calcular_puntualidad(access_records)

    # Consulta para obtener los meses disponibles en los registros de acceso
    cur = mysql.connection.cursor()
    cur.execute("SELECT DISTINCT DATE_FORMAT(date_time, '%Y-%m') AS month FROM access_records")
    months = cur.fetchall()
    cur.close()

    return render_template(
        'administration/empAccessControl/employeeResults.jinja', 
        id=id,
        name=name, 
        resultados_puntualidad=resultados_puntualidad, 
        months=months
    )

def obtener_exits_records(empleado_id):
    cur = mysql.connection.cursor()

    # Consulta para obtener los registros de salidas del empleado con el id proporcionado
    sql = """
    SELECT date_time, status
    FROM access_records
    WHERE fingerprint_id = %s AND status = 0
    ORDER BY date_time
    """
    cur.execute(sql, (empleado_id,))

    exits_records = cur.fetchall()
    cur.close()

    return exits_records

def calcular_horas_extra(exits_records):
    hora_salida_esperada = datetime.strptime("17:00:00", "%H:%M:%S")
    hora_salida_limite = hora_salida_esperada + timedelta(minutes=15)

    resultados_horas_extra = []

    for exit_record in exits_records:
        fecha_hora_salida = exit_record[0]

        hora_salida = fecha_hora_salida.time()

        if hora_salida <= hora_salida_esperada.time():
            if hora_salida < hora_salida_esperada.time():
                horas_extra = "Horas incompletas"
            else:
                horas_extra = "A tiempo"
        elif hora_salida > hora_salida_limite.time():
            horas_extra = "Horas extra"
        else:
            horas_extra = "A tiempo"

        resultados_horas_extra.append({"fecha_hora": fecha_hora_salida, "horas_extra": horas_extra})

    return resultados_horas_extra


# Ruta para mostrar los resultados de salidas para un empleado específico
@admin.route('/administration/empAccessControl/employeeResultsExits/<int:id>/<string:name>')
@admin_required
def employeeResultsExits(id, name):
    exits_records = obtener_exits_records(id) 

    resultados_horas_extra = calcular_horas_extra(exits_records)  # Calcula las horas extra basadas en los registros de salidas

    # Consulta para obtener los meses disponibles en los registros de acceso
    cur = mysql.connection.cursor()
    cur.execute("SELECT DISTINCT DATE_FORMAT(date_time, '%Y-%m') AS month FROM access_records")
    months = cur.fetchall()
    cur.close()

    return render_template(
        'administration/empAccessControl/employeeResultsExits.jinja',
        id=id, 
        name=name,
        resultados_horas_extra=resultados_horas_extra,
        months=months
    )

@admin.route('/punctualityBonus/<int:id>', methods=['POST'])
@admin_required
def punctualityBonus(id):
    try:
        # Conexión a la base de datos
        conn = mysql.connection
        cursor = conn.cursor()

        query = "INSERT INTO payroll (employee_id, bonus) VALUES (%s, 1)"
        cursor.execute(query, (id,))
        
        conn.commit()
        cursor.close()

        return '', 204  
    except Exception as e:
        return str(e), 500 
#---------------------------------------------------------------------------

@admin.route('/administration/projectionsResults')
@admin_required
def projectionsResults():

    return render_template('administration/stats/projectionsResults.jinja')


#----------------------------------------------------------------------------
#------------------Bloque de funciones para las ganancias--------------------
#----------------------------------------------------------------------------

#-------Ruta para mostrar las gráficas de los resultados de las ganancias----
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

            # Obtener el número del mes a partir de 'selected_month' (formato 'YYYY-MM')
            numero_mes = int(selected_month.split('-')[1])

            # Obtener el nombre del mes a partir del número del mes
            nombre_mes = calendar.month_name[numero_mes]

            # Crear una gráfica de puntos unidos por líneas para las ganancias
            fig_ganancias = go.Figure(data=go.Scatter(
                x=df_ganancias.index,   # Definir el eje x como 'No. Orden'
                y=df_ganancias['ganancias'],  # Definir el eje y como 'ganancias'
                mode='lines+markers'    # Indicar que deseas puntos unidos por líneas
            ))

            # Configurar etiquetas y título con el número de año y el nombre del mes en texto
            fig_ganancias.update_layout(
                xaxis_title='No. Orden',
                yaxis_title='$ Ganancias',
                title=f'Ganancias de {selected_month.split("-")[0]} - {nombre_mes}'  # Usar el año y el nombre del mes en el título
            )


            # Configurar los ticks del eje x como números enteros
            fig_ganancias.update_xaxes(
                tickvals=df_ganancias.index,  # Usar los valores de 'No. Orden' como ticks
                tickmode='array',             # Modo de ticks personalizados
                ticktext=[str(int(val)) for val in df_ganancias.index]  # Convertir los valores a enteros
            )

            # Formatear el eje y como valores de dinero para indicar que son pesos
            fig_ganancias.update_yaxes(
                tickformat='$,.2f',  # Formato de número con símbolo de pesos y decimales
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


#Variable de alcance superior
fig_ganancias  = None

# Ruta para mostrar gráficas de resultados para diferentes períodos
@admin.route('/administration/monthlyResults', methods=['GET', 'POST'])
@admin_required
def generateTimeGraphs():
    global fig_ganancias
    
    try:
        # Establecer una conexión a la base de datos
        cur = mysql.connection.cursor()

        end_date = datetime.now()

        selected_time_period = None

        if request.method == 'POST':
            time_period = request.form['time_period']

            # Determina el rango de fechas según el período seleccionado
            if time_period == 'last_month':
                start_date = end_date - timedelta(days=30)
                label = 'Último Mes'
            elif time_period == 'last_15_days':
                start_date = end_date - timedelta(days=15)
                label = 'Últimos 15 Días'
            elif time_period == 'last_3_months':
                start_date = end_date - timedelta(days=90)
                label = 'Últimos 3 Meses'
            elif time_period == 'last_6_months':
                start_date = end_date - timedelta(days=180)
                label = 'Últimos 6 Meses'
            elif time_period == 'last_year':
                start_date = end_date - timedelta(days=365)
                label = 'Ultimo Año'
            else:
                    return "Temporalidad no válida"
            

            # Consulta SQL para obtener las ganancias para el período seleccionado
            sql_query = """
                SELECT id, total as ganancias
                FROM orders
                WHERE verifiedDocs = 1 AND paymentMade = 1 AND shipmentMade = 1 AND type = 1
                AND order_date >= %s AND order_date <= %s
            """
            cur.execute(sql_query, [start_date, end_date])
            ganancias = cur.fetchall()

            # Calcular la suma total de las ganancias para el período seleccionado
            ganancias_totales = sum(g[1] for g in ganancias)

            # Crear un DataFrame de pandas con las ganancias
            df_ganancias = pd.DataFrame(ganancias, columns=['No. Orden', 'ganancias']).set_index('No. Orden')

            # Crear una gráfica de puntos unidos por líneas para las ganancias
            fig_ganancias = go.Figure(data=go.Scatter(
                x=df_ganancias.index,
                y=df_ganancias['ganancias'],
                mode='lines+markers'
            ))

            # Configurar etiquetas y título
            fig_ganancias.update_layout(
                xaxis_title='No. Orden',
                yaxis_title='$ Ganancias',
                title=f'Ganancias de {label}'
            )

            # Configurar los ticks del eje x como números enteros
            fig_ganancias.update_xaxes(
                tickvals=df_ganancias.index,
                tickmode='array',
                ticktext=[str(int(val)) for val in df_ganancias.index]
            )

            # Formatear el eje y como valores de dinero
            fig_ganancias.update_yaxes(
                tickformat='$,.2f',
            )

            # Convertir la figura de Plotly a HTML
            graph_html_ganancias = fig_ganancias.to_html(full_html=False)

            selected_time_period = {
                'label': label,
                'ganancias_totales': ganancias_totales,
                'graph_html_ganancias': graph_html_ganancias
            }

        return render_template(
            'administration/stats/monthlyResults.jinja',
            selected_time_period=selected_time_period
        )

    except Exception as e:
        return f"Error al calcular las ganancias: {str(e)}"


#Variable en alcance superior para que pueda ser accedida desde otras funciones
fig_projections = None

# Ruta para mostrar las proyecciones de ganancias con temporalidad seleccionada📈
@admin.route('/administration/profitsProjections', methods=['GET', 'POST'])
@admin_required
def profitsProjections():
    global fig_projections

    if request.method == 'POST':
        temporalidad = request.form.get('temporalidad')
        if temporalidad:
            try:
                # Establecer una conexión a la base de datos
                cur = mysql.connection.cursor()

                # Determina la fecha actual
                current_date = datetime.now()

                # Determina la fecha de inicio basada en la temporalidad seleccionada
                if temporalidad == '15_dias':
                    start_date = current_date - timedelta(days=15)
                    label = 'Próximos 15 Días'
                elif temporalidad == '1_mes':
                    start_date = current_date - timedelta(days=30)
                    label = 'Próximo Mes'
                elif temporalidad == '3_meses':
                    start_date = current_date - timedelta(days=90)
                    label = 'Próximos 3 Meses'
                elif temporalidad == '6_meses':
                    start_date = current_date - timedelta(days=180)
                    label = 'Próximos 6 Meses'
                elif temporalidad == '1_ano':
                    start_date = current_date - timedelta(days=365)
                    label = 'Próximo Año'
                else:
                    return "Temporalidad no válida"

                # Consulta SQL para obtener los datos históricos de ID de pedido y montos totales
                sql_query = """
                    SELECT id, total
                    FROM orders
                    WHERE verifiedDocs = 1 AND paymentMade = 1 AND shipmentMade = 1 AND type = 1
                    AND order_date >= %s AND order_date <= %s
                """
                cur.execute(sql_query, [start_date, current_date])
                data = cur.fetchall()

                # Crear un DataFrame de pandas con los ID de pedido y montos totales
                df = pd.DataFrame(data, columns=['id', 'ganancias'])

                # Guardar el número de muestras utilizadas en una variable
                num_samples = df.shape[0]

                # Separar las características (ID de pedido) y el objetivo (montos totales)
                X = df[['id']]
                y = df['ganancias']

                # Crear y entrenar un modelo de regresión lineal
                model = LinearRegression()
                model.fit(X, y)

                # Generar ID de pedido para los días futuros
                future_ids = pd.DataFrame({'id': range(df['id'].max() + 1, df['id'].max() + 50)})

                # Realizar la predicción de ganancias para los ID de pedido futuros
                projected_ganancias = model.predict(future_ids)

                # Sumar los primeros 'num_samples' valores de ganancias proyectadas
                sum_of_ganancias = sum(projected_ganancias[:num_samples])

                # Formatear la estimación a dos decimales
                estimacion = "{:.2f}".format(sum_of_ganancias)

                # Crear una gráfica de dispersión con la línea de regresión
                plt.figure(figsize=(10, 6))
                plt.scatter(X, y, label='Ganancias Pasadas')
                plt.plot(future_ids, projected_ganancias, color='red', label='Línea de Regresión, (proyeccion de ganancias)')
                plt.xlabel('ID de Pedido')
                plt.ylabel('Ganancias')
                plt.title(f'Proyeccion de resultados en {label} con Regresión Lineal')
                plt.legend()

                # Crear una gráfica de dispersión interactiva con la línea de regresión utilizando Plotly
                fig_projections  = px.scatter(df, x='id', y='ganancias', title=f'Proyeccion de resultados en {label} con Regresión Lineal')
                fig_projections .add_scatter(x=future_ids['id'], y=projected_ganancias, mode='lines', name='Línea de Regresión', line=dict(color='red'))

                # Generar HTML con la gráfica de Plotly
                graph_html = fig_projections .to_html(full_html=False)

                # Renderizar la plantilla con la proyección de ganancias
                return render_template(
                    'administration/stats/profitsProjections.jinja',
                    projected_ganancias=projected_ganancias[0],
                    graph_html=graph_html,
                    num_samples=num_samples,
                    sum_of_ganancias=sum_of_ganancias,
                    estimacion=estimacion, 
                    label=label
                )

            except Exception as e:
                return f"Error al realizar la predicción de ganancias: {str(e)}"

    return render_template('administration/stats/profitsProjections.jinja')



# Ruta para comparar las gráficas generadas en ambas funciones
@admin.route('/administration/compareGraphs', methods=['GET', 'POST'])
@admin_required
def compareGraphs():
    global fig_ganancias, fig_projections

    fig_ganancias = None  # Reiniciar las figuras en cada solicitud
    fig_projections = None

    if request.method == 'POST':
        # Obtiene el período de tiempo seleccionado desde el formulario
        temporalidad = request.form.get('temporalidad')

        try:
            # Genera la gráfica de ganancias si no está disponible
            if fig_ganancias is None:
                end_date = datetime.now()
                
                # Coloca aquí la generación de fig_ganancias
                cur = mysql.connection.cursor()
                
                # Determina el rango de fechas según el período seleccionado
                if temporalidad == '1_mes':
                    start_date = end_date - timedelta(days=30)
                    label = 'Último Mes'
                elif temporalidad == '15_dias':
                    start_date = end_date - timedelta(days=15)
                    label = 'Últimos 15 Días'
                elif temporalidad == '3_meses':
                    start_date = end_date - timedelta(days=90)
                    label = 'Últimos 3 Meses'
                elif temporalidad == '6_meses':
                    start_date = end_date - timedelta(days=180)
                    label = 'Últimos 6 Meses'
                elif temporalidad == '1_ano':
                    start_date = end_date - timedelta(days=365)
                    label = 'Ultimo Año'
                else:
                    return "Temporalidad no válida"
                
                # Consulta SQL para obtener las ganancias para el período seleccionado
                sql_query = """
                    SELECT id, total as ganancias
                    FROM orders
                    WHERE verifiedDocs = 1 AND paymentMade = 1 AND shipmentMade = 1 AND type = 1
                    AND order_date >= %s AND order_date <= %s
                """
                cur.execute(sql_query, [start_date, end_date])
                ganancias = cur.fetchall()

                # Calcular la suma total de las ganancias para el período seleccionado
                ganancias_totales = sum(g[1] for g in ganancias)

                # Crear un DataFrame de pandas con las ganancias
                df_ganancias = pd.DataFrame(ganancias, columns=['No. Orden', 'ganancias']).set_index('No. Orden')

                # Crear una gráfica de puntos unidos por líneas para las ganancias
                fig_ganancias = go.Figure(data=go.Scatter(
                    x=df_ganancias.index,
                    y=df_ganancias['ganancias'],
                    mode='lines+markers'
                ))

                # Configurar etiquetas y título
                fig_ganancias.update_layout(
                    xaxis_title='No. Orden',
                    yaxis_title='$ Ganancias',
                    title=f'Ganancias de {label}'
                )

                # Configurar los ticks del eje x como números enteros
                fig_ganancias.update_xaxes(
                    tickvals=df_ganancias.index,
                    tickmode='array',
                    ticktext=[str(int(val)) for val in df_ganancias.index]
                )

                # Formatear el eje y como valores de dinero
                fig_ganancias.update_yaxes(
                    tickformat='$,.2f',
                )

                # Convertir la figura de Plotly a HTML
                graph_html_ganancias = fig_ganancias.to_html(full_html=False)

                selected_time_period = {
                    'label': label,
                    'ganancias_totales': ganancias_totales,
                    'graph_html_ganancias': graph_html_ganancias
                }

            # Genera la gráfica de proyecciones si no está disponible
            if fig_projections is None:

                cur = mysql.connection.cursor()

                # Determina la fecha actual
                current_date = datetime.now()

                # Determina la fecha de inicio basada en la temporalidad seleccionada
                if temporalidad == '15_dias':
                    start_date = current_date - timedelta(days=15)
                    label = 'Próximos 15 Días'
                elif temporalidad == '1_mes':
                    start_date = current_date - timedelta(days=30)
                    label = 'Próximo Mes'
                elif temporalidad == '3_meses':
                    start_date = current_date - timedelta(days=90)
                    label = 'Próximos 3 Meses'
                elif temporalidad == '6_meses':
                    start_date = current_date - timedelta(days=180)
                    label = 'Próximos 6 Meses'
                elif temporalidad == '1_ano':
                    start_date = current_date - timedelta(days=365)
                    label = 'Próximo Año'
                else:
                    return "Temporalidad no válida"

                # Consulta SQL para obtener los datos históricos de ID de pedido y montos totales
                sql_query = """
                    SELECT id, total
                    FROM orders
                    WHERE verifiedDocs = 1 AND paymentMade = 1 AND shipmentMade = 1 AND type = 1
                    AND order_date >= %s AND order_date <= %s
                """
                cur.execute(sql_query, [start_date, current_date])
                data = cur.fetchall()

                # Crear un DataFrame de pandas con los ID de pedido y montos totales
                df = pd.DataFrame(data, columns=['id', 'ganancias'])

                # Guardar el número de muestras utilizadas en una variable
                num_samples = df.shape[0]

                # Separar las características (ID de pedido) y el objetivo (montos totales)
                X = df[['id']]
                y = df['ganancias']

                # Crear y entrenar un modelo de regresión lineal
                model = LinearRegression()
                model.fit(X, y)

                # Generar ID de pedido para los días futuros
                future_ids = pd.DataFrame({'id': range(df['id'].max() + 1, df['id'].max() + 50)})

                # Realizar la predicción de ganancias para los ID de pedido futuros
                projected_ganancias = model.predict(future_ids)

                # Sumar los primeros 'num_samples' valores de ganancias proyectadas
                sum_of_ganancias = sum(projected_ganancias[:num_samples])

                # Formatear la estimación a dos decimales
                estimacion = "{:.2f}".format(sum_of_ganancias)

                # Crear una gráfica de dispersión con la línea de regresión
                plt.figure(figsize=(10, 6))
                plt.scatter(X, y, label='Ganancias Pasadas')
                plt.plot(future_ids, projected_ganancias, color='red', label='Línea de Regresión, (proyeccion de ganancias)')
                plt.xlabel('ID de Pedido')
                plt.ylabel('Ganancias')
                plt.title(f'Proyeccion de resultados en {label} con Regresión Lineal')
                plt.legend()

                # Crear una gráfica de dispersión interactiva utilizando Plotly
                fig_projections = px.scatter(df, x='id', y='ganancias', title=f'Proyeccion de resultados en {label} con Regresión Lineal')

                # Configurar la traza de dispersión para que los puntos estén unidos por líneas
                fig_projections.update_traces(mode='lines+markers', line=dict(color='blue'))

                # Añadir la línea de regresión
                fig_projections.add_scatter(x=future_ids['id'], y=projected_ganancias, mode='lines', name='Línea de Regresión', line=dict(color='red'))


                # Generar HTML con la gráfica de Plotly
                graph_html = fig_projections.to_html(full_html=False)

                selected_time_period = {
                    'label': label,
                    'ganancias_totales': ganancias_totales,
                    'graph_html_ganancias': graph_html_ganancias
                }

            # Crear subplots para mostrar ambas gráficas en una sola figura
            subplot = make_subplots(rows=1, cols=2)

            # Añadir la gráfica de ganancias al primer subplot
            subplot.add_trace(fig_ganancias.data[0], row=1, col=1)

            # Añadir la gráfica de proyecciones al segundo subplot
            for trace in fig_projections.data:
                subplot.add_trace(trace, row=1, col=2)

            # Actualizar diseño y títulos
            subplot.update_layout(
                title_text="Comparación de Gráficas de Resultados y Proyecciones",
                xaxis_title="No. Orden",
                yaxis_title="$ Ganancias",
            )

            # Convertir el subplot en HTML
            graph_html_combined = plot(subplot, output_type='div')

            # Renderiza la plantilla compareGraphs.jinja con las gráficas combinadas
            return render_template(
                'administration/stats/compareGraphs.jinja',
                graph_html_combined=graph_html_combined
            )

        except Exception as e:
            return f"Error al comparar las gráficas: {str(e)}"
    
    # Si es una solicitud GET, simplemente muestra el formulario
    return render_template('administration/stats/compareGraphs.jinja')





#----------------------------------------------------------------------------
#-------------------Bloque de funciones para las pérdidas--------------------
#----------------------------------------------------------------------------

#-----------Ruta para mostrar los resultados de las perdidas-----------------
@admin.route('/administration/lossResults', methods=['GET', 'POST'])
@admin_required
def lossResults():
    try:
        # Establecer una conexión a la base de datos
        cur = mysql.connection.cursor()

        # Obtener todos los meses disponibles
        cur.execute("SELECT DISTINCT DATE_FORMAT(order_date, '%Y-%m') as month FROM orders")
        months = [row[0] for row in cur.fetchall()]

        perdidas_mes_anterior = 0
        perdidas_mes = 0

        if request.method == 'POST':
            # El usuario ha seleccionado un mes
            selected_month = request.form['month']

            # Consulta SQL para obtener las pérdidas del mes seleccionado
            sql_query = """
                SELECT id, total as perdidas
                FROM orders
                WHERE verifiedDocs = 1 AND paymentMade = 1 AND shipmentMade = 1
                AND DATE_FORMAT(order_date, '%%Y-%%m') = %s
            """
            cur.execute(sql_query, [selected_month])
            perdidas = cur.fetchall()

            # Calcular las pérdidas totales para el mes seleccionado
            perdidas_mes = sum(p[1] for p in perdidas)

            # Consulta SQL para obtener las pérdidas del mes anterior
            mes_anterior = (datetime.strptime(selected_month, '%Y-%m') - relativedelta(months=1)).strftime('%Y-%m')
            sql_query_anterior = """
                SELECT id, total as perdidas
                FROM orders
                WHERE verifiedDocs = 1 AND paymentMade = 1 AND shipmentMade = 1
                AND DATE_FORMAT(order_date, '%%Y-%%m') = %s
            """
            cur.execute(sql_query_anterior, [mes_anterior])
            perdidas_anterior = cur.fetchall()

            # Calcular las pérdidas totales para el mes anterior
            perdidas_mes_anterior = sum(p[1] for p in perdidas_anterior)

            # Cerrar la conexión a la base de datos
            cur.close()

            # Crear una gráfica de barras para mostrar las pérdidas del mes seleccionado y el mes anterior
            fig_perdidas = go.Figure()
            fig_perdidas.add_trace(go.Bar(
                x=[f'Mes actual ({selected_month})', f'Mes anterior ({mes_anterior})'],
                y=[perdidas_mes, perdidas_mes_anterior],
                text=[f'{perdidas_mes:.2f}', f'{perdidas_mes_anterior:.2f}'],
                textposition='auto',
                marker=dict(color=['blue', 'red']),
            ))

            # Configurar etiquetas y título
            fig_perdidas.update_layout(
                xaxis_title='Mes',
                yaxis_title='$ Pérdidas',
                title='Comparación de resultados'
            )

            # Formatear el eje y como valores de dinero para indicar que son pesos
            fig_perdidas.update_yaxes(
                tickformat='$,.2f',  # Formato de número con símbolo de pesos y decimales
            )

            # Convertir la figura de Plotly a HTML
            graph_html_perdidas = fig_perdidas.to_html(full_html=False)
        else:
            # No se ha seleccionado un mes, no mostrar ninguna gráfica
            graph_html_perdidas = None
        
        # Calcular la diferencia entre las pérdidas del mes actual y el mes anterior si ambos tienen valores
        diferencia_perdidas = None  # Inicializa la variable
        if perdidas_mes is not None and perdidas_mes_anterior is not None:
            diferencia_perdidas = perdidas_mes - perdidas_mes_anterior


        # Definir un mensaje descriptivo en función de la diferencia
        if diferencia_perdidas > 0:
            mensaje_perdida = f'Hubo una ganancia de ${abs(diferencia_perdidas):.2f} en comparación con el mes anterior.'
        elif diferencia_perdidas < 0:
            mensaje_perdida = f'Hubo una pérdida de ${abs(diferencia_perdidas):.2f} en comparación con el mes anterior.'
        else:
            mensaje_perdida = 'No hubo cambios en las pérdidas en comparación con el mes anterior.'

        return render_template(
        'administration/stats/lossResults.jinja',
        months=months,
        graph_html_perdidas=graph_html_perdidas,
        mensaje_perdida=mensaje_perdida
        )


    except Exception as e:
        return f"Error al calcular las pérdidas: {str(e)}"


#----------------------------------------------------------------------------
#------------------Bloque de funciones para rentabilidad---------------------
#----------------------------------------------------------------------------

#----Ruta para mostrar los resultados de la rentabilidad de la empresa-------
@admin.route('/administration/profitabilityResults', methods=['GET', 'POST'])
@admin_required
def profitabilityResults():
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT DISTINCT DATE_FORMAT(order_date, '%Y-%m') as month FROM orders")
        months = [row[0] for row in cur.fetchall()]

        rentabilidad_mes = None
        porcentaje_cambio = None

        if request.method == 'POST':
            selected_month = request.form.get('month')
            if selected_month:
                income_query = """
                    SELECT SUM(total) as income
                    FROM orders
                    WHERE verifiedDocs = 1 AND paymentMade = 1 AND shipmentMade = 1
                    AND DATE_FORMAT(order_date, '%%Y-%%m') = %s
                """
                cur.execute(income_query, [selected_month])
                income = cur.fetchone()[0]

                mes_anterior = (datetime.strptime(selected_month, '%Y-%m') - relativedelta(months=1)).strftime('%Y-%m')
                income_query_anterior = """
                    SELECT SUM(total) as income
                    FROM orders
                    WHERE verifiedDocs = 1 AND paymentMade = 1 AND shipmentMade = 1
                    AND DATE_FORMAT(order_date, '%%Y-%%m') = %s
                """
                cur.execute(income_query_anterior, [mes_anterior])
                income_anterior = cur.fetchone()[0]

                if income_anterior is not None:
                    rentabilidad_mes = income - income_anterior
                    porcentaje_cambio = ((income - income_anterior) / income_anterior) * 100
                else:
                    rentabilidad_mes = income
                    porcentaje_cambio = 0

                cur.close()

                labels = ['Mes actual', 'Mes anterior']
                values = [income, income_anterior]
                fig_rentabilidad = go.Figure(data=[go.Bar(x=labels, y=values)])

                numero_mes = int(selected_month.split('-')[1])
                nombre_mes = calendar.month_name[numero_mes]
                fig_rentabilidad.update_layout(
                    title=f'Rentabilidad de {nombre_mes} {selected_month.split("-")[0]}'
                )
                graph_html_rentabilidad = fig_rentabilidad.to_html(full_html=False)
            else:
                graph_html_rentabilidad = None

            selected_month = request.form.get('month')

            selected_month_datetime = datetime.strptime(selected_month, '%Y-%m')
            mes_anterior_datetime = selected_month_datetime - relativedelta(months=1)

            nombre_mes = calendar.month_name[selected_month_datetime.month]
            year_selected = selected_month_datetime.year

            nombre_mes_anterior = calendar.month_name[mes_anterior_datetime.month]
            year_anterior = mes_anterior_datetime.year

            return render_template(
                'administration/stats/profitabilityResults.jinja',
                months=months,
                selected_month=selected_month,
                nombre_mes=nombre_mes,
                year_selected=year_selected,
                nombre_mes_anterior=nombre_mes_anterior,
                year_anterior=year_anterior,
                porcentaje_cambio=porcentaje_cambio,
                rentabilidad_mes=rentabilidad_mes,
                graph_html_rentabilidad=graph_html_rentabilidad
            )
        else:
            return render_template(
                'administration/stats/profitabilityResults.jinja',
                months=months,
                graph_html_rentabilidad=None
            )

    except Exception as e:
        return f"Error al calcular la rentabilidad: {str(e)}"


# #Estimacion o proyecion de las perdidas a meses futuros, tomando los resultados de los meses previos, mediante la regresión lineal simple
# @admin.route('/administration/lossProjections', methods=['GET', 'POST'])
# @admin_required
# def lossProjections():
#     try:
#         # Establecer una conexión a la base de datos
#         cur = mysql.connection.cursor()

#         # Obtener todos los meses disponibles en la base de datos
#         cur.execute("SELECT DISTINCT DATE_FORMAT(order_date, '%Y-%m') as month FROM orders")
#         months = [row[0] for row in cur.fetchall()]

#         if request.method == 'POST':
#             # El usuario ha seleccionado meses futuros
#             selected_months = request.form.getlist('selected_months')

#             # Obtener datos históricos de pérdidas para los meses seleccionados
#             loss_data = []

#             for selected_month in selected_months:
#                 sql_query = """
#                     SELECT id, total as perdidas
#                     FROM orders
#                     WHERE verifiedDocs = 1 AND paymentMade = 1 AND shipmentMade = 1
#                     AND DATE_FORMAT(order_date, '%%Y-%%m') = %s
#                 """
#                 cur.execute(sql_query, [selected_month])
#                 perdidas = cur.fetchall()

#                 # Calcular las pérdidas totales para el mes seleccionado
#                 perdidas_mes = sum(p[1] for p in perdidas)

#                 loss_data.append({'month': selected_month, 'total_loss': perdidas_mes})

#             # Cerrar la conexión a la base de datos
#             cur.close()

#             # Crear un DataFrame de pandas con los datos de pérdidas
#             df_loss = pd.DataFrame(loss_data)

#             # Utilizar la regresión lineal simple para estimar las pérdidas futuras
#             X_train = df_loss.index.values.reshape(-1, 1)
#             y_train = df_loss['total_loss'].values

#             model = LinearRegression()
#             model.fit(X_train, y_train)

#             # Crear datos para la estimación de pérdidas
#             future_months = pd.date_range(start=df_loss['month'].max(), periods=6, freq='M')
#             X_future = np.array(range(len(df_loss), len(df_loss) + 6)).reshape(-1, 1)
#             estimated_losses = model.predict(X_future)

#             # Crear una gráfica de las estimaciones de pérdidas
#             fig_estimated_losses = go.Figure()
#             fig_estimated_losses.add_trace(go.Scatter(
#                 x=future_months,
#                 y=estimated_losses,
#                 mode='lines+markers',
#                 name='Estimaciones de Pérdidas'
#             ))

#             fig_estimated_losses.update_layout(
#                 xaxis_title='Mes',
#                 yaxis_title='$ Pérdidas',
#                 title='Estimación de Pérdidas Futuras'
#             )

#             # Convertir la figura de Plotly a HTML
#             graph_html_estimated_losses = fig_estimated_losses.to_html(full_html=False)
#         else:
#             # No se han seleccionado meses futuros
#             graph_html_estimated_losses = None

#         return render_template(
#             'administration/stats/lossProjections.jinja',
#             months=months,
#             graph_html_estimated_losses=graph_html_estimated_losses
#         )

#     except Exception as e:
#         return f"Error al realizar estimaciones de pérdidas: {str(e)}"
    

# @admin.route('/administration/profitabilityProjections')
# @admin_required
# def profitabilityProjections():
#     return render_template('administration/stats/profitabilityProjections.jinja')


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
    cur.execute("SELECT id, username, fullname, email, note FROM user WHERE tipousuario = 2 AND areaUsuario = 2")
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

#Actualizar notas
@admin.route('/update_note/<user_id>', methods=['POST'])
def update_note(user_id):
    if request.method == 'POST':
        new_note = request.form['note']
        cur = mysql.connection.cursor()
        cur.execute("UPDATE user SET note = %s WHERE id = %s", (new_note, user_id))
        mysql.connection.commit()
        cur.close()
        return '', 204  
    return '', 204


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
