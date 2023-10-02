from flask_wtf.csrf import CSRFProtect
from flask_mysqldb import MySQL
from flask import render_template, session, redirect, flash, g
from flask_login import LoginManager, login_user, login_required, current_user
from flask_login import logout_user
from flask import Blueprint
from flask import request
from flask import Flask, url_for
from flask import redirect


app = Flask(__name__)
storageemp = Flask(__name__)
mysql = MySQL()

storageemp = Blueprint('storageemp', __name__)

csrf = CSRFProtect()

@storageemp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('startpage'))

@app.route('/logout')
def logout():
    logout_user()
    session.pop('username', None)
    return redirect(url_for('startpage'))


@storageemp.route('/storage_home')
def storage_home():
    # Código necesario para la página "storage/storageHome.jinja"
    return render_template('storage/storageHome.jinja')

#--------------------Historial de las Máquinas-----------------------------
@storageemp.route('/storage/stoHistory')
def stoHistory():
    
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT id, uid, model, datecurrent, status FROM store")
    machines_data = cursor.fetchall()

    # Close the cursor
    cursor.close()

    # Render the template with the data
    return render_template('/storage/stoHistory.jinja', machines_data=machines_data)
    

@storageemp.route('/storage/machineHistory/<int:machine_id>')
def machineHistory(machine_id):
    # Obtener los datos del historial de la máquina con el ID proporcionado
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT id_History, id_Machine, entry_date, entry_time, exit_date, exit_time FROM machinehistory WHERE id_Machine=%s", (machine_id,))
    machine_history_data = cursor.fetchall()
    cursor.close()

    # Renderizar la plantilla con los datos del historial de la máquina
    return render_template('/storage/machineHistory.jinja', machine_id=machine_id, machine_history_data=machine_history_data)

#---------------Mantenimiento Almacén aviso-------------
@storageemp.route('/storage/stoMaintenance')
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
def preventive(id_machine):
    if request.method == 'POST':
        
        # Update the maintenanceNotice field to 0 (preventive)
        cursor = mysql.connection.cursor()
        cursor.execute("UPDATE machines SET maintenanceNotice = 0 WHERE id_Machine = %s", (id_machine,))
        mysql.connection.commit()
        cursor.close()
        
        return redirect(url_for('storageemp.stoMaintenance'))  # Redirect to the maintenance page

@storageemp.route('/storage/corrective/<int:id_machine>', methods=['POST'])
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
@csrf.exempt
@storageemp.route('/storage/update_machine/<int:machine_id>', methods=['GET', 'POST'])
def update_machine(machine_id):
    cursor = mysql.connection.cursor()

    # Fetch the existing machine data
    cursor.execute("SELECT * FROM machines WHERE id_Machine=%s", (machine_id,))
    machine_data = cursor.fetchone()

    if request.method == 'POST':
        # Get the updated data from the form
        model = request.form['model']
        brand = request.form['brand']
        type = request.form['type']

        # Update the machine record in the database
        cursor.execute(
            "UPDATE machines SET model=%s, brand=%s, type=%s WHERE id_Machine=%s",
            (model, brand, type, machine_id)
        )

        # Commit the changes to the database
        mysql.connection.commit()

        # Redirect to the 'stoMachines' route after updating
        return redirect(url_for('storageemp.stoMachines'))

    cursor.close()

    return render_template('storage/update_machine.jinja', machine_data=machine_data)

#--------------------Eliminar una maquina-----------------✅
@csrf.exempt
@storageemp.route('/storage/delete_machine/<int:machine_id>', methods=['POST'])
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
@csrf.exempt
@storageemp.route('/storage/add_machine', methods=['GET', 'POST'])
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

