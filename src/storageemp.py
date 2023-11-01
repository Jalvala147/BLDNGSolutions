from flask_wtf.csrf import CSRFProtect
from flask_mysqldb import MySQL
from flask import render_template, session, redirect, flash, g
from flask_login import LoginManager, login_user, login_required, current_user
from flask_login import logout_user
from flask import Blueprint
from flask import request
from flask import Flask, url_for
from flask import redirect
from functools import wraps


app = Flask(__name__)
storageemp = Flask(__name__)
mysql = MySQL()

storageemp = Blueprint('storageemp', __name__)

csrf = CSRFProtect()

# Decorador para almacén (tipoUsuario = 2 y areaUsuario = 3 o tipoUsuario = 1 y areaUsuario = 1)
def storage_required(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if not current_user.is_authenticated:
            flash("Debes iniciar sesión para acceder a esta página.")
            return redirect(url_for('loginemp'))
        elif not (current_user.tipoUsuario == 2 and current_user.areaUsuario == 3) and not (current_user.tipoUsuario == 1 and current_user.areaUsuario == 1):
            flash("Acceso no autorizado. Debes ser un empleado de almacén para acceder a esta página.")
            return redirect(url_for('loginemp'))
        return func(*args, **kwargs)

    return decorated_view

#Manejador de logout para empleados de almacén
@storageemp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('startpage'))

#Página de inicio de empleados de almacén
@storageemp.route('/storage_home')
@storage_required
def storage_home():
    # Código necesario para la página "storage/storageHome.jinja"
    return render_template('storage/storageHome.jinja')

#--------------------Historial de las Máquinas-----------------------------
@storageemp.route('/storage/stoHistory')
@storage_required
def stoHistory():
    cursor = mysql.connection.cursor()
    cursor.execute("""
        SELECT machines.id_Machine, store.uid, machines.model, store.datecurrent, store.status
        FROM store
        INNER JOIN machinesid ON store.uid = machinesid.uid_Machine
        INNER JOIN machines ON machinesid.id_Machine = machines.id_Machine
    """)
    machines_data = cursor.fetchall()
    # Close the cursor
    cursor.close()
    # Render the template with the data
    return render_template('/storage/stoHistory.jinja', machines_data=machines_data)



@storageemp.route('/storage/machineHistory/<int:machine_id>')
@storage_required
def machineHistory(machine_id):
    # toma uid, brand, model, del id asociado
    cursor = mysql.connection.cursor()
    cursor.execute("""
        SELECT machinesid.uid_Machine, machines.model, machines.brand
        FROM machinesid
        INNER JOIN machines ON machinesid.id_Machine = machines.id_Machine
        WHERE machinesid.id_Machine = %s
    """, (machine_id,))
    machine_data = cursor.fetchone()
    cursor.close()

    if machine_data:
        uid = machine_data[0]
        model = machine_data[1]
        brand = machine_data[2]

        # Retrieve machine history based on the UID
        cursor = mysql.connection.cursor()
        query = """
        SELECT timestamp, new_status
        FROM machinehistory
        WHERE uid = %s AND (new_status = 1 OR new_status = 0)
        ORDER BY timestamp
        """
        cursor.execute(query, (uid,))
        machine_history_data = cursor.fetchall()
        cursor.close()

        # Separate the entry and exit dates
        entry_dates = [entry[0] for entry in machine_history_data if entry[1] == 1]
        exit_dates = [exit[0] for exit in machine_history_data if exit[1] == 0]

        # Render the template with the machine history data, model, and brand
        return render_template('/storage/machineHistory.jinja', machine_id=machine_id, model=model, brand=brand, entry_dates=entry_dates, exit_dates=exit_dates)
    else:
        # Handle the case where no matching machine was found
        return "Machine not found"


#---------------Mantenimiento Almacén aviso-------------
@storageemp.route('/storage/stoMaintenance')
@storage_required
def stoMaintenance():
    # crear el cursor
    cursor = mysql.connection.cursor()
    
    # buscar los datos de la tabla 'machines'
    cursor.execute("SELECT id_Machine, model FROM machines")
    machines_data = cursor.fetchall()
    
    # cerrar el cursor
    cursor.close()
    
    # renderizar la plantilla con los datos
    return render_template('/storage/stoMaintenance.jinja', machines_data=machines_data)


@storageemp.route('/storage/preventive/<int:id_machine>', methods=['POST'])
@storage_required
def preventive(id_machine):
    if request.method == 'POST':
        
        # Update the maintenanceNotice field to 0 (preventive)
        cursor = mysql.connection.cursor()
        cursor.execute("UPDATE machines SET maintenanceNotice = 0 WHERE id_Machine = %s", (id_machine,))
        mysql.connection.commit()
        cursor.close()
        
        return redirect(url_for('storageemp.stoMaintenance'))  # Redirect to the maintenance page

@storageemp.route('/storage/corrective/<int:id_machine>', methods=['POST'])
@storage_required
def corrective(id_machine):
    if request.method == 'POST':
        
        # Update the maintenanceNotice field to 1 (corrective)
        cursor = mysql.connection.cursor()
        cursor.execute("UPDATE machines SET maintenanceNotice = 1 WHERE id_Machine = %s", (id_machine,))
        mysql.connection.commit()
        cursor.close()
        
        return redirect(url_for('storageemp.stoMaintenance'))  # Redirect to the maintenance page



#------------------------Almacén: Listado de las maquinas---------------------
@storageemp.route('/storage/stoMachines')
@storage_required
def stoMachines():
    # crear el cursor
    cursor = mysql.connection.cursor()

    # buscar los datos de la tabla 'machines'
    cursor.execute("SELECT id_Machine, model, brand, type FROM machines")
    machines_data = cursor.fetchall()

    # cerrar el cursor
    cursor.close()

    # renderizar la plantilla con los datos
    return render_template('/storage/stoMachines.jinja', machines_data=machines_data)


#----------------------Actualizar una maquina------------------------✅
@storageemp.route('/storage/update_machine/<int:machine_id>', methods=['GET', 'POST'])
@storage_required
def update_machine(machine_id):
    cursor = mysql.connection.cursor()

    # Fetch the existing machine data
    cursor.execute("SELECT machines.id_Machine, machinesid.uid_Machine, machines.model, machines.brand, machines.type FROM machines LEFT JOIN machinesid ON machines.id_Machine = machinesid.id_Machine WHERE machines.id_Machine=%s", (machine_id,))
    machine_data = cursor.fetchone()

    if request.method == 'POST':
        # Get the updated data from the form
        model = request.form['model']
        brand = request.form['brand']
        type = request.form['type']
        uid = request.form['uid']

        # Check if a record with the given 'machine_id' exists in 'machinesid'
        cursor.execute("SELECT * FROM machinesid WHERE id_Machine=%s", (machine_id,))
        existing_machine = cursor.fetchone()

        if existing_machine:
            # If the record exists, update it
            cursor.execute(
                "UPDATE machinesid SET uid_Machine=%s WHERE id_Machine=%s",
                (uid, machine_id)
            )
        else:
            # If the record doesn't exist, insert a new one
            cursor.execute(
                "INSERT INTO machinesid (id_Machine, uid_Machine) VALUES (%s, %s)",
                (machine_id, uid)
            )

        # Update the machine record in the 'machines' table
        cursor.execute(
            "UPDATE machines SET model=%s, brand=%s, type=%s WHERE id_Machine=%s",
            (model, brand, type, machine_id)
        )

        # Commit the changes to the database
        mysql.connection.commit()

        # Redirect to the 'stoMachines' route after updating
        return redirect(url_for('storageemp.stoMachines'))

    cursor.close()

    if machine_data is None:
        # Handle the case when no data is found, you can redirect to an error page or provide a message to the user.
        return "No se encontraron datos para la máquina con ID {}".format(machine_id)

    return render_template('storage/update_machine.jinja', machine_data=machine_data)


#--------------------Eliminar una maquina-----------------✅
@storageemp.route('/storage/delete_machine/<int:machine_id>', methods=['POST'])
@storage_required
def delete_machine(machine_id):
    cursor = mysql.connection.cursor()

    # Delete the machine record from the database
    cursor.execute("DELETE FROM machines WHERE id_Machine=%s", (machine_id,))

    # Commit the changes
    mysql.connection.commit()
    cursor.close()

    # Redirect back to the machine list page
    return redirect(url_for('storageemp.stoMachines'))

#--------------Agregar una nueva maquina------------✅
@storageemp.route('/storage/add_machine', methods=['GET', 'POST'])
@storage_required
def add_machine():
    if request.method == 'POST':
        # Obtener los datos de la máquina del formulario
        model = request.form['model']
        brand = request.form['brand']
        machine_type = request.form['type']

        # Crear una conexión y cursor para la base de datos
        cursor = mysql.connection.cursor()

        # Definir la consulta SQL para insertar la máquina
        query = "INSERT INTO machines (model, brand, type) VALUES (%s, %s, %s)"
        values = (model, brand, machine_type)

        # Ejecutar la consulta SQL con los valores proporcionados
        cursor.execute(query, values)

        # Confirmar la transacción en la base de datos
        mysql.connection.commit()

        # Cerrar el cursor y la conexión
        cursor.close()
        return redirect(url_for('storageemp.stoMachines'))
    return render_template('storage/add_machine.jinja')

#------------Listado de las ordenes que estan listas para salir del almacen y ser enviadas
@storageemp.route('/storage/readyMachines')
@storage_required
def readyMachines():
    try:
        # Realiza la consulta SQL con JOIN y condiciones, ordenando por número de pedido
        cursor = mysql.connection.cursor()
        query = """
        SELECT orders.id AS numero_pedido, machines.id_Machine, machines.model, machines.brand
        FROM machineorders
        JOIN machines ON machineorders.machine_id = machines.id_Machine
        JOIN orders ON machineorders.order_id = orders.id
        WHERE orders.paymentMade = 1 AND orders.verifiedDocs = 1 AND shipmentMade = 0
        ORDER BY numero_pedido ASC
        """
        cursor.execute(query)
        machines = cursor.fetchall()
        cursor.close()

        # Renderiza la plantilla y pasa los resultados a la misma
        return render_template('storage/readyMachines.jinja', machines=machines)
    except Exception as e:
        # Manejo de errores
        return "Error al obtener las órdenes listas para enviar: " + str(e)



