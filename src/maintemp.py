from flask_mysqldb import MySQL
from flask import render_template, session, redirect, flash
from flask import Blueprint
from flask import request
from flask import Flask
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
    
    return render_template('maintenance/mantHistory.jinja', machine_id=machine_id)

#--------------------------------------------------------------------------

@maintemp.route('/maintenance/mantReports')   
def mantReports():
    return render_template('/maintenance/mantReports.jinja')

@maintemp.route('/maintenance/mantHome')   
def mantHome():
    return render_template('/maintenance/mantHome.jinja')

@maintemp.route('/maintenance/mantMaintenance')
def mantMaintenance():
    return render_template('/maintenance/mantMaintenance.jinja')