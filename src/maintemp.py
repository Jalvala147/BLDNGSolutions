from flask_mysqldb import MySQL
from flask import render_template, session, redirect, flash
from flask import Blueprint
from flask import request
from flask import Flask, url_for
from datetime import datetime, timedelta
app = Flask(__name__)
mysql = MySQL()
import os

maintemp = Blueprint('maintemp', __name__)

@maintemp.route('/maintenance_home')
def maintenance_home():
    # Código necesario para la página "maintenance/mantHome.jinja"
    return render_template('maintenance/mantHome.jinja')

#--------------------rutas mantenimiento-----------------------

#listado de las maquinas con boton para ver historial de mantenimiento
@maintemp.route('/maintenance/mantMachines')   
def mantMachines():
    # crear el cursor
    cursor = mysql.connection.cursor()

    # buscar los datos de la tabla 'machines'
    cursor.execute("SELECT id_Machine, model, brand, type FROM machines")
    machines_data = cursor.fetchall()

    # cerrar el cursor
    cursor.close()
    return render_template('/maintenance/mantMachines.jinja', machines_data=machines_data)

#-----------------Historial de las maquinas------------------------
@maintemp.route('/maintenance/mantHistory/<int:machine_id>', methods=['GET', 'POST'])
def mantHistory(machine_id):
    # Crear el cursor
    cursor = mysql.connection.cursor()

    # Consulta para obtener las fechas de mantenimiento preventivo de la máquina
    cursor.execute("SELECT date FROM preventivemaintenance "
                   "WHERE id_Maintenance IN "
                   "(SELECT id FROM maintenancehistory WHERE id_Machine = %s)", (machine_id,))
    preventive_dates = cursor.fetchall()

    # Consulta para obtener las fechas de mantenimiento correctivo de la máquina
    cursor.execute("SELECT date FROM correctivemaintenance "
                   "WHERE id_Maintenance IN "
                   "(SELECT id FROM maintenancehistory WHERE id_Machine = %s)", (machine_id,))
    corrective_dates = cursor.fetchall()

    # Cerrar el cursor
    cursor.close()

    return render_template('maintenance/mantHistory.jinja',
                           machine_id=machine_id,
                           preventive_dates=preventive_dates,
                           corrective_dates=corrective_dates)


#--------------------------------------------------------------------------

@maintemp.route('/maintenance/mantReports')   
def mantReports():
    cursor = mysql.connection.cursor()

    # Modify the SQL query to join tables and select the necessary columns
    cursor.execute("""
        SELECT u.fullname, m.brand, m.model, r.date, r.description, r.Failure_status
        FROM reports r
        JOIN user u ON r.id_userReporting = u.id
        JOIN machines m ON r.id_Machine = m.id_machine
    """)

    reports_data = cursor.fetchall()

    cursor.close()
    return render_template('/maintenance/mantReports.jinja', reports_data=reports_data)



@maintemp.route('/maintenance/mantHome')   
def mantHome():
    return render_template('/maintenance/mantHome.jinja')


#------------------------Marcar que mantenimiento necesitan las maquinas-----------------------
@maintemp.route('/maintenance/mantMaintenance')
def mantMaintenance():
    cursor = mysql.connection.cursor()

    # buscar los datos de la tabla 'machines'
    cursor.execute("SELECT id_Machine, brand, model FROM machines")
    machines_data = cursor.fetchall()

    # cerrar el cursor
    cursor.close()

    return render_template('maintenance/mantMaintenance.jinja', machines_data=machines_data)

#---------Mantenimiento correctivo
@maintemp.route('/maintenance/corrective/<int:id_machine>', methods=['POST'])
def corrective(id_machine):
    if request.method == 'POST':
        
        # Crear un nuevo registro en la tabla maintenancehistory
        cursor = mysql.connection.cursor()
        cursor.execute("INSERT INTO maintenancehistory (id_Machine) VALUES (%s)", (id_machine,))
        mysql.connection.commit()
        
        # Obtener el id recién creado
        new_id_maintenance = cursor.lastrowid
        
        # Insertar el registro en la tabla correctivemaintenance con el nuevo id_Maintenance
        cursor.execute("INSERT INTO correctivemaintenance (id_Maintenance, date) VALUES (%s, CURRENT_TIMESTAMP)",
                       (new_id_maintenance,))
        mysql.connection.commit()
        
        cursor.close()
        
        return redirect(url_for('maintemp.mantMaintenance'))  # Redirigir a la página de mantenimiento

#----------Mantenimiento preventivo-----------------------------------------
@maintemp.route('/maintenance/preventive/<int:id_machine>', methods=['POST'])
def preventive(id_machine):
    if request.method == 'POST':
        # Conecta con la base de datos
        cursor = mysql.connection.cursor()

        # Crea un nuevo registro en la tabla maintenancehistory
        cursor.execute("INSERT INTO maintenancehistory (id_Machine) VALUES (%s)", (id_machine,))
        mysql.connection.commit()
        
        # Obtiene el ID recién creado
        new_id_maintenance = cursor.lastrowid
        
        # Inserta el registro en la tabla preventivemaintenance con el nuevo ID_Maintenance
        cursor.execute("INSERT INTO preventivemaintenance (id_Maintenance, date) VALUES (%s, CURRENT_TIMESTAMP)",
                       (new_id_maintenance,))
        mysql.connection.commit()
        
        # Cierra la conexión con la base de datos
        cursor.close()
        
        return redirect(url_for('maintemp.mantMaintenance'))  # Redirigir a la página de mantenimiento