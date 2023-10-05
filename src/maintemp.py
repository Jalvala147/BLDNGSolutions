from flask_mysqldb import MySQL
from flask import render_template, session, redirect, flash
from flask import Blueprint
from flask import request
from flask import Flask, url_for
from flask_login import current_user
from datetime import datetime, timedelta
app = Flask(__name__)
mysql = MySQL()
from functools import wraps

maintemp = Blueprint('maintemp', __name__)

# Decorador para mantenimiento (tipoUsuario = 2 y areaUsuario = 5 o tipoUsuario = 1 y areaUsuario = 1)
def maintenance_required(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if not current_user.is_authenticated:
            flash("Debes iniciar sesión para acceder a esta página.")
            return redirect(url_for('loginemp'))
        elif not (current_user.tipoUsuario == 2 and current_user.areaUsuario == 5) and not (current_user.tipoUsuario == 1 and current_user.areaUsuario == 1):
            flash("Acceso no autorizado. Debes ser un empleado de mantenimiento para acceder a esta página.")
            return redirect(url_for('loginemp'))
        return func(*args, **kwargs)
    return decorated_view

@maintemp.route('/maintenance_home')
def maintenance_home():
    # Código necesario para la página "maintenance/mantHome.jinja"
    return render_template('maintenance/mantHome.jinja')

#--------------------rutas mantenimiento-----------------------

@maintemp.route('/maintenance/mantHome')   
@maintenance_required
def mantHome():
    return render_template('/maintenance/mantHome.jinja')

#listado de las maquinas con boton para ver historial de mantenimiento
@maintemp.route('/maintenance/mantMachines')   
@maintenance_required
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
@maintenance_required
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

    # Consulta para obtener la marca y el modelo de la máquina
    cursor.execute("SELECT brand, model FROM machines WHERE id_Machine = %s", (machine_id,))
    machine_info = cursor.fetchone()
    brand, model = machine_info if machine_info else ("Desconocido", "Desconocido")
    
    cursor.close()

    return render_template('maintenance/mantHistory.jinja',
                       machine_id=machine_id,
                       preventive_dates=preventive_dates,
                       corrective_dates=corrective_dates,
                       brand=brand,
                       model=model)

#-----------------------Reportes generados por clientes-----------------------

@maintemp.route('/maintenance/mantReports')   
@maintenance_required
def mantReports():
    cursor = mysql.connection.cursor()

    cursor.execute("""
        SELECT u.fullname, m.brand, m.model, r.date, r.description, r.Failure_status
        FROM reports r
        JOIN user u ON r.id_userReporting = u.id
        JOIN machines m ON r.id_Machine = m.id_machine
        WHERE r.Failure_status = 0
    """)
    reports_data = cursor.fetchall()
    cursor.close()
    return render_template('/maintenance/mantReports.jinja', reports_data=reports_data)


@maintemp.route('/maintenance/completedMantReports')   
@maintenance_required
def completedReports():
    cursor = mysql.connection.cursor()

    cursor.execute("""
        SELECT u.fullname, m.brand, m.model, r.date, r.description, r.Failure_status
        FROM reports r
        JOIN user u ON r.id_userReporting = u.id
        JOIN machines m ON r.id_Machine = m.id_machine
        WHERE r.Failure_status = 1
    """)
    reports_data = cursor.fetchall()
    cursor.close()
    return render_template('/maintenance/completedMantReports.jinja', reports_data=reports_data)

#------------------------Marcar que mantenimiento necesitan las maquinas-----------------------

@maintemp.route('/maintenance/mantMaintenance')
@maintenance_required
def mantMaintenance():
    cursor = mysql.connection.cursor()

    # Consulta SQL para obtener los datos de todas las máquinas
    cursor.execute("SELECT id_Machine, brand, model FROM machines")
    machines_data = cursor.fetchall()

    # Consulta SQL para calcular los días restantes solo si hay registros en preventivemaintenance
    cursor.execute("SELECT mh.id_Machine, DATEDIFF(pm.scheduled_date, CURRENT_DATE()) AS days_remaining "
                   "FROM maintenancehistory mh "
                   "LEFT JOIN preventivemaintenance pm ON mh.id = pm.id_Maintenance")
    maintenance_data = cursor.fetchall()

    # Cerrar el cursor
    cursor.close()

    # Crear un diccionario para mapear id_Machine a días restantes
    machine_to_days = {row[0]: row[1] for row in maintenance_data if row[1] is not None}

    # Combinar los datos de las máquinas y los días restantes
    combined_data = []
    for machine in machines_data:
        id_machine = machine[0]
        days_remaining = machine_to_days.get(id_machine, None)
        combined_data.append((machine[0], machine[1], machine[2], days_remaining))

    return render_template('maintenance/mantMaintenance.jinja', machines_data=combined_data)

#---------Mantenimiento correctivo
@maintemp.route('/maintenance/corrective/<int:id_machine>', methods=['POST'])
@maintenance_required
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

        # Modificar la tabla "reports" estableciendo "Failure_status" en 1
        cursor.execute("UPDATE reports SET Failure_status = 1 WHERE id_Machine = %s", 
                       (id_machine,))
        mysql.connection.commit()
        
        #Modificar la tabla "machines" estableciendo maintenanceNotice en Null, indicando ya se corrigio el problema
        cursor.execute("UPDATE machines SET maintenanceNotice = NULL WHERE id_Machine = %s",
                       (id_machine,))
        mysql.connection.commit()
        
        cursor.close()
        
        return redirect(url_for('maintemp.mantMaintenance'))  # Redirigir a la página de mantenimiento

#---------Mantenimiento preventivo
@maintemp.route('/maintenance/preventive/<int:id_machine>', methods=['POST'])
@maintenance_required
def preventive(id_machine):
    if request.method == 'POST':
        days = int(request.form['days'])  # Obtiene el número de días desde el formulario
        current_date = datetime.now()  # Fecha actual
        scheduled_date = current_date + timedelta(days=days)  # Fecha programada
        
        # Crear un nuevo registro en la tabla maintenancehistory
        cursor = mysql.connection.cursor()
        cursor.execute("INSERT INTO maintenancehistory (id_Machine) VALUES (%s)", (id_machine,))
        mysql.connection.commit()
        
        # Obtener el id recién creado
        new_id_maintenance = cursor.lastrowid
        
        # Insertar el registro en la tabla preventivemaintenance con el nuevo id_Maintenance
        cursor.execute("INSERT INTO preventivemaintenance (id_Maintenance, date, scheduled_date) VALUES (%s, %s, %s)",
                       (new_id_maintenance, current_date, scheduled_date))
        mysql.connection.commit()
        
        #Modificar la tabla "machines" estableciendo maintenanceNotice en Null, indicando ya programó mantenimiento preventivo
        cursor.execute("UPDATE machines SET maintenanceNotice = NULL WHERE id_Machine = %s",
                       (id_machine,))
        mysql.connection.commit()
        
        cursor.close()

    return redirect(url_for('maintemp.mantMaintenance'))  # Redirigir a la página de mantenimiento

@maintemp.route('/maintenance/storageRequests')
@maintenance_required
def storageRequests():
    cur = mysql.connection.cursor()

    # Realizar la consulta a la tabla machines
    cur.execute("SELECT id_Machine, model, brand, maintenanceNotice FROM machines")
    machines_data = cur.fetchall()

    return render_template('maintenance/storageRequests.jinja', machines_data=machines_data)