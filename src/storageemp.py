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
    return redirect(url_for('startpage'))


#--------------------Historial de las Máquinas-----------------------------
@storageemp.route('/storage/stoHistory')
def stoHistory():
    cursor = mysql.connection.cursor()

    # Fetch data from the 'machines' table
    cursor.execute("SELECT id_Machine, model, brand, status FROM machines")
    machines_data = cursor.fetchall()

    # Close the cursor
    cursor.close()

    # Render the template with the data
    return render_template('/storage/stoHistory.jinja', machines_data=machines_data)
    

@storageemp.route('/storage/machineHistory/<int:machine_id>')
def machineHistory(machine_id):
    # Obtener los datos del historial de la máquina con el ID proporcionado
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT id_History, id_Machine, entry_date, entry_time, exit_date, exit_time FROM machineHistory WHERE id_Machine=%s", (machine_id,))
    machine_history_data = cursor.fetchall()
    cursor.close()

    # Renderizar la plantilla con los datos del historial de la máquina
    return render_template('/storage/machineHistory.jinja', machine_id=machine_id, machine_history_data=machine_history_data)

#---------------Mantenimiento Almacén aviso-------------
@storageemp.route('/storage/stoMaintenance')
def stoMaintenance():
    cursor = mysql.connection.cursor()
    
    cursor.execute("SELECT id_Machine, model FROM machines")
    machines_data = cursor.fetchall()
    
    cursor.close()
    
    return render_template('/storage/stoMaintenance.jinja', machines_data=machines_data)
#------------------------Almacén de las maquinas-------------------------------
@storageemp.route('/storage/stoMachines')
def stoMachines():
    # Assuming you have already configured your database connection
    cursor = mysql.connection.cursor()

    # Fetch data from the 'machines' table
    cursor.execute("SELECT id_Machine, model, brand, type, status, currentUser FROM machines")
    machines_data = cursor.fetchall()

    # Close the cursor
    cursor.close()

    # Render the template with the data
    return render_template('/storage/stoMachines.jinja', machines_data=machines_data)

@csrf.exempt
@storageemp.route('/storage/update_machine/<int:machine_id>', methods=['GET', 'POST'])
def update_machine(machine_id):
    cursor = mysql.connection.cursor()

    if request.method == 'POST':
        # Get the updated data from the form
        model = request.form['model']
        brand = request.form['brand']
        type = request.form['type']
        status = request.form['status']
        currentUser = request.form['currentUser']

        # Update the machine record in the database
        cursor.execute(
            "UPDATE machines SET model=%s, brand=%s, type=%s, status=%s, currentUser=%s WHERE id_Machine=%s",
            (model, brand, type, status, currentUser, machine_id)
        )

        # Commit the changes
        mysql.connection.commit()
        cursor.close()

        # Redirect back to the machine list page
        return redirect(url_for('storageemp.stoMachines'))

    # If it's a GET request, fetch the machine data for the form pre-population
    cursor.execute("SELECT id_Machine, model, brand, type, status, currentUser FROM machines WHERE id_Machine=%s", (machine_id,))
    machine_data = cursor.fetchone()
    cursor.close()

    # Render the update form with the machine data
    return render_template('/storage/update_machine.jinja', machine_data=machine_data)

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


@csrf.exempt
@storageemp.route('/storage/add_machine', methods=['GET', 'POST'])
def add_machine():
    if request.method == 'POST':
        # Obtener los datos de la máquina del formulario
        model = request.form['model']
        brand = request.form['brand']
        machine_type = request.form['type']
        status = request.form['status']
        current_user = request.form['currentUser']

        # Verificar si el ID de usuario proporcionado existe en la tabla 'users'
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT id FROM user WHERE id=%s", (current_user,))
        user_exists = cursor.fetchone()

        if not user_exists:
            flash("El cliente no existe. Por favor, proporcione un ID de cliente válido.", "danger")
            return render_template('storage/add_machine.jinja')

        # El ID de usuario existe, proceder con agregar la máquina
        query = "INSERT INTO machines (model, brand, type, status, currentUser) VALUES (%s, %s, %s, %s, %s)"
        values = (model, brand, machine_type, status, current_user)

        try:
            cursor.execute(query, values)
            mysql.connection.commit()
            flash("Registro agregado exitosamente.", "success")
            return redirect(url_for('storageemp.stoMachines'))
        except Exception as e:
            flash("Error al agregar el registro: " + str(e), "danger")
            mysql.connection.rollback()
        finally:
            cursor.close()

    return render_template('storage/add_machine.jinja')
