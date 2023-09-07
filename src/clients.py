from flask_wtf.csrf import CSRFProtect
from flask_mysqldb import MySQL
from flask_mail import Mail, Message
from flask import render_template, session, redirect, flash, g
from flask_login import login_user, login_required, current_user
from flask_login import logout_user
from flask import Blueprint
from flask import request, jsonify
from flask import Flask, url_for
from flask import redirect
import math
import json

app = Flask(__name__)
mysql = MySQL()
mail = Mail(app)


clients = Blueprint('clients', __name__)

csrf = CSRFProtect()


@app.route('/logout')
def logout():
    logout_user()
    session.pop('username', None)
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



#------------Listado de los productos(maquinas)---------------------
@clients.route('/clientuser/products')   
def products():
    user_id = current_user.id

    cur = mysql.connection.cursor() 
    cur.execute("SELECT id, name, image, price, id_Machine FROM products")
    product_data = cur.fetchall()

    # Crear una lista para almacenar los productos como dicconarios
    products = [] 
    for product in product_data: #itera sobre los datos de los productos obtenidos
        product_dict = { #crear un diccionario para cada producto con id, name, image y price
            'id': product[0],
            'name': product[1],
            'image': product[2],
            'price': product[3],
            'id_Machine' : product[4]
        }
        products.append(product_dict) #agrega el diccionario del producto a la lista de productos

    cur.close()
    
    return render_template('/clientuser/products.jinja', user_id=user_id, products=products)




# @clients.route('/clientuser/place_order', methods=['POST'])
# @login_required
# def place_order():
#     if request.method == 'POST':
#         machine_ids = request.form.getlist('cart_machine_ids')
#         client_user_id = request.form['clientUser_id']
#         #purchase_option = request.form['purchase_option']

#         print("Machine id:", machine_ids)
#         print("user id:", client_user_id)

#         for machine_id in machine_ids:
#             # Insertar cada pedido en la tabla "pedidos"
#             cur = mysql.connection.cursor()
#             cur.execute("INSERT INTO machinesorders (machine_id, clientUser_id) VALUES (%s, %s)",
#                         (machine_id, client_user_id ))
#             mysql.connection.commit()
#             cur.close()

#         flash('Pedidos realizados con éxito')
#         return redirect(url_for('clients.products'))

#     return redirect(url_for('clients.products'))


# clients.py
@clients.route('/clientuser/place_order', methods=['POST'])
@login_required
def place_order():
    if request.method == 'POST':
        client_user_id = request.form['clientUser_id']
        cart_machine_ids_str = request.form['cart_machine_ids']
        cart_total = request.form['cart_total']
        cart_weeks_str = request.form['cart_weeks']

        # Convertir la cadena JSON en un diccionario
        cart_weeks = json.loads(cart_weeks_str)

        # Insertar el pedido en la tabla "orders"
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO orders (clientUser_id, total) VALUES (%s, %s)", (client_user_id, cart_total))
        mysql.connection.commit()

        # Obtener el ID del pedido recién insertado
        order_id = cur.lastrowid

        # Obtener la lista de IDs de las máquinas y convertirla en una lista
        cart_machine_ids = cart_machine_ids_str.split(',')

        # Insertar las máquinas relacionadas en la tabla "machineorders"
        for machine_id in cart_machine_ids:
            machine_data = cart_weeks.get(machine_id)
            weeks = machine_data['weeks']
            price = machine_data['price']
            cur.execute("INSERT INTO machineorders (order_id, machine_id, weeks, price) VALUES (%s, %s, %s, %s)",
                        (order_id, machine_id, weeks, price))
            mysql.connection.commit()

        cur.close()

        return redirect(url_for('clients.products'))

    return redirect(url_for('clients.products'))



#----Hacer un reporte a maquina--------
@clients.route('/clientuser/makereport')   
def makereport():
    return render_template('/clientuser/makereport.jinja')
 

