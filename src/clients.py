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
#import stripe
import math
import json


app = Flask(__name__)
mysql = MySQL()
mail = Mail(app)


clients = Blueprint('clients', __name__)

csrf = CSRFProtect()

app.config['STRIPE_PUBLIC_KEY'] = 'pk_test_51Ns9uVB0WRECsvw4RKybB3WRFOviaJea7AiDaHYrGoPLt08xWU7fS5Q8Dfyr6clI9SimSIsSNZclseD4Oq5Vsjur00L5NDp3cm'
app.config['STRIPE_SECRET_KEY'] = 'sk_test_51Ns9uVB0WRECsvw4UN0P1pswEObrLOzD1XrNGDTFol3jUKfwJmctLxLBGvC356AScv0w4J86D0k6inGHFlLhj6nz00653AbSdX'

@app.route('/logout')
def logout():
    logout_user()
    session.pop('username', None)
    return redirect(url_for('startpage'))

#------------------------------------------------------------------------------------
@clients.route('/logout')
@login_required  # Asegura que el usuario esté autenticado para acceder a la ruta
def logout():
    logout_user()  # Cierra la sesión del usuario actual
    return redirect(url_for('login'))  # Redirecciona al inicio de sesión o a la página principal

#--------------------rutas clientes-----------------------
@clients.route('/clientsHome')
@login_required
def clientsHome():
    return render_template('/clientuser/clientsHome.jinja')

#--------------------------------------------
@clients.route('/payments', methods=['GET', 'POST'])
def payments():
    user_id = current_user.id

    # Consulta las órdenes pendientes para el usuario actual
    cur = mysql.connection.cursor()
    cur.execute("SELECT id, total FROM orders WHERE clientUser_id = %s AND status = 1", (user_id,))
    orders = cur.fetchall()
    cur.close()

    return render_template('clientuser/payments.jinja', user_id=user_id, orders=orders)
    

#----Hacer un reporte a maquina--------
@clients.route('/clientuser/makereport', methods=['GET', 'POST'])
def makereport():
    if request.method == 'POST':
        # Obtén el ID de la máquina seleccionada del formulario
        machine_id = request.form.get('machine_id')
        # Obtén la descripción de la falla del formulario
        description = request.form.get('description')

        # Inserta los datos en la tabla 'reports' en la base de datos
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO reports (id_userReporting, id_machine, description) VALUES (%s, %s, %s)",
                    (current_user.id, machine_id, description))
        mysql.connection.commit()
        cur.close()

        flash('El reporte se ha enviado correctamente.', 'success')

        # Redirige a la página de inicio o realiza alguna otra acción
        return redirect(url_for('clients.makereport'))  

    # Obtener todos los 'order_id' de la tabla 'orders' donde 'clientUser_id' coincide con 'current_user.id'
    cur = mysql.connection.cursor()
    cur.execute("""
    SELECT id
    FROM orders
    WHERE clientUser_id = %s
    """, (current_user.id,))
    order_ids = [row[0] for row in cur.fetchall()]
    cur.close()

    # Obtén las máquinas únicas correspondientes a los 'order_id'
    cur = mysql.connection.cursor()
    cur.execute("""
    SELECT DISTINCT m.id_Machine, UPPER(m.model), UPPER(m.brand)
    FROM machines m
    JOIN machineorders mo ON m.id_Machine = mo.machine_id
    WHERE mo.order_id IN %s
    """, (tuple(order_ids),))
    machine_info = {row[0]: f"{row[2]} - {row[1]}" for row in cur.fetchall()}
    cur.close()

    return render_template('/clientuser/makereport.jinja', machine_info=machine_info)




#------------------------Subida de archivos necesarios--------------------------
@csrf.exempt
@clients.route('/docs', methods=['GET', 'POST'])
@login_required
def docs():
    # Obtener el ID del usuario actualmente autenticado
    user_id = current_user.id

    if request.method == 'POST':
        file = request.files['file']
        if file:
            # Leer el contenido del archivo
            file_data = file.read()

            # Obtener el nombre del archivo
            filename = file.filename

            # Guardar el contenido y el nombre del archivo en la base de datos
            cur = mysql.connection.cursor()
            cur.execute("INSERT INTO files (user_id, filename, file_data, status) VALUES (%s, %s, %s, %s)",
                        (user_id, filename, file_data, 0))  # Establece el estado como 1 para "Valido"
            mysql.connection.commit()
            cur.close()

            flash('Archivo cargado correctamente ✔️')
            return redirect(url_for('clients.docs'))

    # Realizar la consulta para obtener los documentos del usuario con el ID proporcionado
    cur = mysql.connection.cursor()
    cur.execute("SELECT id, filename, status FROM files WHERE user_id = %s", (user_id,))
    documents = cur.fetchall()
    cur.close()

    # Obtener el tamaño máximo permitido en bytes
    cur = mysql.connection.cursor()
    cur.execute("SHOW VARIABLES LIKE 'max_allowed_packet'")
    result = cur.fetchone()
    max_size_bytes = int(result[1])
    cur.close()

    # Calcular el tamaño máximo en KB
    max_size_kb = math.ceil(max_size_bytes / 1024)

    return render_template('/clientuser/docs.jinja', max_size_kb=max_size_kb, user_id=user_id, documents=documents)   

@clients.route('/delete_document/<int:document_id>', methods=['GET', 'POST'])
@login_required
def delete_document(document_id):
    # Verificar si el documento existe y pertenece al usuario actual
    cur = mysql.connection.cursor()
    cur.execute("SELECT id, filename FROM files WHERE id = %s AND user_id = %s", (document_id, current_user.id))
    document = cur.fetchone()

    if document:
        # Eliminar el documento de la base de datos
        cur.execute("DELETE FROM files WHERE id = %s", (document_id,))
        mysql.connection.commit()
        cur.close()

        flash('Documento eliminado correctamente ✔️')
    else:
        flash('Documento no encontrado o no tienes permiso para eliminarlo ❌', 'error')

    return redirect(url_for('clients.docs'))



@clients.route('/orders')
def orders():

    user_id = current_user.id
    cur = mysql.connection.cursor()
    #tomamos id la fecha y total de los pedidos del usuario actual
    cur.execute("SELECT id, order_date, total FROM orders WHERE clientUser_id = %s", (user_id,))
    orders_data = cur.fetchall()
    cur.close()

    # Renderizar la plantilla con los datos obtenidos
    return render_template('/clientuser/orders.jinja', orders_data=orders_data)

@clients.route('/orders/info/<int:id_order>')
def information(id_order):

    cur = mysql.connection.cursor()
    # Consulta SQL para obtener los datos de la tabla machineorders relacionados con el pedido
    cur.execute("SELECT machine_id, weeks, price FROM machineorders WHERE order_id = %s", (id_order,))
    order_items = cur.fetchall()

    # Consulta para obtener los detalles del pedido desde la tabla orders, incluyendo la dirección de envío concatenada y el método de pago
    cur.execute("""
    SELECT o.total, u.fullname AS client_name, o.rfc, CONCAT(o.address, ', ', o.postalCode) AS delivery_address, o.paymentMethod AS payment_method
    FROM orders o
    INNER JOIN user u ON o.clientUser_id = u.id
    WHERE o.id = %s
    """, (id_order,))
    
    order_info = cur.fetchone()
    total = order_info[0] if order_info else 0
    client_name = order_info[1] if order_info else ""
    rfc = order_info[2] if order_info else ""
    delivery_address = order_info[3] if order_info else ""
    payment_method = order_info[4] if order_info else ""

    # Consulta para obtener los nombres de las máquinas
    machine_names = []
    for order_item in order_items:
        machine_id = order_item[0]
        cur.execute("SELECT brand, model FROM machines WHERE id_Machine = %s", (machine_id,))
        machine_data = cur.fetchone()
        if machine_data:
            machine_name = f"{machine_data[0]} {machine_data[1]}"
            machine_names.append(machine_name)
        else:
            machine_names.append("N/A")

    # Cierra el cursor
    cur.close()

    return render_template('/clientuser/information.jinja', id_order=id_order, order_items=order_items, total=total, client_name=client_name, rfc=rfc, delivery_address=delivery_address, payment_method=payment_method, machine_names=machine_names)


#-----------------------------------------------------------


@clients.route('/clientuser/statusprogress')
def statusprogress():
    user_id = current_user.id

    # Consulta SQL para obtener los IDs, verifiedDocs y paymentMade de órdenes relacionadas con el usuario actual
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT id, verifiedDocs, paymentMade, shipmentMade FROM orders WHERE clientUser_id = %s AND status = 1", (user_id,))
    
    # Recopilamos los resultados de la consulta en una lista de diccionarios
    orders_data = [{'id': row[0], 'verifiedDocs': row[1], 'paymentMade': row[2], 'shipmentMade' : row[3]} for row in cursor.fetchall()]
    
    cursor.close()

    return render_template('/clientuser/statusprogress.jinja', orders_data=orders_data)

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


# -------------Peticion de productos/Place order------------------------
@clients.route('/clientuser/place_order', methods=['POST'])
@login_required
def place_order():
    if request.method == 'POST':
        client_user_id = request.form['clientUser_id']
        cart_machine_ids_str = request.form['cart_machine_ids']
        cart_total = request.form['cart_total']
        cart_weeks_str = request.form['cart_weeks']

        #Bloque de pruebas de recepcion de informacion desde el form input type hidden de products.jinja
        print(f'client_user_id: {client_user_id}')
        print(f'cart_machine_ids_str: {cart_machine_ids_str}') 
        print(f'cart_total: {cart_total}')
        print(f'cart_weeks: {cart_weeks_str}')

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



