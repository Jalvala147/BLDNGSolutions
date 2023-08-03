from flask_wtf.csrf import CSRFProtect
from flask_mysqldb import MySQL
from flask import render_template, session, redirect, flash, g
from flask_login import login_user, login_required, current_user
from flask_login import logout_user
from flask import Blueprint
from flask import request, jsonify
from flask import Flask, url_for
from flask import redirect
import math

app = Flask(__name__)
mysql = MySQL()


clients = Blueprint('clients', __name__)

csrf = CSRFProtect()


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('startpage'))

#--------------------rutas clientes-----------------------
@clients.route('/clientsHome')
@login_required
def clientsHome():
    return render_template('/clientuser/clientsHome.jinja')

@csrf.exempt
@clients.route('/docs', methods=['GET', 'POST'])
@login_required
def docs():
    # Obtener el tamaño máximo permitido en bytes
    cur = mysql.connection.cursor()
    cur.execute("SHOW VARIABLES LIKE 'max_allowed_packet'")
    result = cur.fetchone()
    max_size_bytes = int(result[1])
    cur.close()

    # Calcular el tamaño máximo en KB
    max_size_kb = math.ceil(max_size_bytes / 1024)

    if request.method == 'POST':
        file = request.files['file']
        if file:
            # Leer el contenido del archivo
            file_data = file.read()

            # Obtener el nombre del archivo
            filename = file.filename

            # Obtener el ID del usuario actualmente autenticado
            user_id = current_user.id

            # Guardar el contenido y el nombre del archivo en la base de datos
            cur = mysql.connection.cursor()
            cur.execute("INSERT INTO files (user_id, filename, file_data) VALUES (%s, %s, %s)",
                        (user_id, filename, file_data))
            mysql.connection.commit()
            cur.close()

            flash('Archivo cargado correctamente ✔️')
            return redirect(url_for('clients.docs'))

    return render_template('/clientuser/docs.jinja', max_size_kb=max_size_kb)
    
@clients.route('/information')   
def information():
    return render_template('/clientuser/information.jinja')
    
@clients.route('/payments')   
def payments():
    return render_template('/clientuser/payments.jinja')
    
@clients.route('/clientuser/statusprogress')   
def statusprogress():
    return render_template('/clientuser/statusprogress.jinja')



@clients.route('/logout')
@login_required  # Asegura que el usuario esté autenticado para acceder a la ruta
def logout():
    logout_user()  # Cierra la sesión del usuario actual
    return redirect(url_for('login'))  # Redirecciona al inicio de sesión o a la página principal

@clients.route('/clientuser/products')   
def products():
    user_id = current_user.id
    return render_template('/clientuser/products.jinja', user_id=user_id)




@clients.route('/clientuser/place_order', methods=['POST'])
@login_required
def place_order():
    if request.method == 'POST':
        client_user_id = request.form['clientUser_id']
        machine_price = request.form['machine_price']

        # Insert the order into the "machinesorders" table
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO machinesorders (clientUser_id, price) VALUES ( %s, %s)",
                    (client_user_id, machine_price))
        mysql.connection.commit()
        cur.close()

        flash('Pedido realizado con éxito')
        return redirect(url_for('clients.products'))

    return redirect(url_for('clients.products'))

