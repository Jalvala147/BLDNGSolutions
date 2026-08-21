from flask_wtf.csrf import CSRFProtect
from flask_mysqldb import MySQL
from flask_mail import Mail, Message
from flask import render_template, session, redirect, flash, g
from flask_login import login_user, login_required, current_user
from flask_login import logout_user
from flask import Blueprint
from flask import request, jsonify
from flask import Flask, url_for, send_file
from flask import redirect
from flask import make_response
from functools import wraps
import json
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfgen import canvas
from io import BytesIO
import os
from werkzeug.utils import secure_filename
# import stripe

app = Flask(__name__)
mysql = MySQL()
mail = Mail(app)

clients = Blueprint('clients', __name__)

csrf = CSRFProtect()


def client_required(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        # Verificar si el usuario está autenticado y tiene un tipo de usuario válido (1 o 3)
        if not current_user.is_authenticated or current_user.tipoUsuario not in [1, 3]:
            flash("Acceso no autorizado. Inicia sesión como cliente.")
            return redirect(url_for('login')) 
        return func(*args, **kwargs)
    return decorated_view

#------------------------------------------------------------------------------------
@clients.route('/logout')
@login_required  # Asegura que el usuario esté autenticado para acceder a la ruta
def logout():
    logout_user()  # Cierra la sesión del usuario actual
    return redirect(url_for('login'))  # Redirecciona al inicio de sesión o a la página principal

#--------------------rutas clientes-----------------------
@clients.route('/clientsHome')
@client_required
@login_required
def clientsHome():
    return render_template('/clientuser/clientsHome.jinja')

#--------------Ventana en la que se muestran los pedidos de cada usuario, asi como su total------------------
@clients.route('/payments', methods=['GET', 'POST'])
@client_required
@login_required
def payments():
    user_id = current_user.id

    # Consulta las órdenes pendientes para el usuario actual
    cur = mysql.connection.cursor()
    cur.execute("SELECT id, total FROM orders WHERE clientUser_id = %s AND status = 1", (user_id,))
    orders = cur.fetchall()
    cur.close()

    return render_template(
        'clientuser/payments.jinja',
        user_id=user_id,
        orders=orders,
        stripe_publishable_key=os.environ.get('STRIPE_PUBLISHABLE_KEY', ''),
        stripe_buy_button_id=os.environ.get('STRIPE_BUY_BUTTON_ID', ''),
    )

#---------------Funcion para generar una orden de pago en PDF------------------------------
def generar_pdf_orden_pago(bancoDestino, numeroCuenta, nombreTitular, monto, concepto, imagen_url):
    pdf_buffer = BytesIO()
    doc = SimpleDocTemplate(pdf_buffer, pagesize=letter)

    # Obtener la fecha y hora actual
    now = datetime.now()
    fecha_hora = now.strftime("%Y-%m-%d %H:%M:%S")

    # Crear una lista de elementos para el contenido del PDF
    elements = []

    # Agregar una imagen al PDF en la parte superior izquierda
    if imagen_url:
        image = Image(imagen_url)
        image.drawWidth = 60  # Ancho de la imagen
        image.drawHeight = 60  # Altura de la imagen
        elements.append(image)

    # Agregar un título al PDF
    title_style = getSampleStyleSheet()['Title']
    title_text = "Orden de Pago Generada<br/>BLDNGSolutions®"
    title = Paragraph(title_text, title_style)
    elements.append(title)

    # Crear una tabla para una presentación más organizada
    data = [['Banco de destino:', bancoDestino],
            ['Número de cuenta:', numeroCuenta],
            ['Nombre del titular:', nombreTitular],
            ['Monto a transferir:', f'${monto}'],
            ['Concepto:', concepto]]

    table = Table(data, colWidths=(120, 250))
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.gray),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('BACKGROUND', (0, 1), (-1, -1), colors.lightblue),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))

    # Agregar la tabla a los elementos
    elements.append(table)

    # Agregar la fecha y hora al PDF
    elements.append(Paragraph(f'Fecha y Hora de Descarga: {fecha_hora}', getSampleStyleSheet()['Normal']))

    # Construir el PDF
    doc.build(elements)

    pdf_buffer.seek(0)
    return pdf_buffer

#----Fucion para generar el PDF y descargarlo
@clients.route('/generar-orden-de-pago', methods=['POST'])
@client_required
@login_required
def generar_orden_de_pago():
    # Recopila los valores de los campos del formulario
    bancoDestino = request.form.get('banco_destino')
    numeroCuenta = request.form.get('numero_cuenta')
    nombreTitular = request.form.get('nombre_titular')
    monto = request.form.get('monto')
    concepto = request.form.get('concepto')

    # Define la URL de la imagen
    imagen_url = "https://github.com/Jalvala147/image/blob/main/logo.png?raw=true"

    # Genera el PDF en memoria
    pdf_data = generar_pdf_orden_pago(bancoDestino, numeroCuenta, nombreTitular, monto, concepto, imagen_url)

    # Envía el archivo PDF como respuesta para que se descargue
    return send_file(pdf_data, as_attachment=True, download_name='orden_pago.pdf', mimetype='application/pdf')


#-----------------------------Hacer un reporte a maquina--------------------------------
@clients.route('/clientuser/makereport', methods=['GET', 'POST'])
@client_required
@login_required
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

    machine_info = {}
    if order_ids:
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
@clients.route('/docs', methods=['GET', 'POST'])
@client_required
@login_required
def docs():
    # Obtener el ID del usuario actualmente autenticado
    user_id = current_user.id

    if request.method == 'POST':
        file = request.files['file']
        if file and file.filename:
            filename = secure_filename(file.filename)
            if not filename:
                flash('Nombre de archivo inválido ❌', 'error')
                return redirect(url_for('clients.docs'))

            allowed_extensions = {'.pdf', '.png', '.jpg', '.jpeg', '.doc', '.docx'}
            ext = os.path.splitext(filename)[1].lower()
            if ext not in allowed_extensions:
                flash('Tipo de archivo no permitido. Usa PDF, imagen u Office.', 'error')
                return redirect(url_for('clients.docs'))

            file_data = file.read()

            cur = mysql.connection.cursor()
            cur.execute("INSERT INTO files (user_id, filename, file_data, status) VALUES (%s, %s, %s, %s)",
                        (user_id, filename, file_data, 0))
            mysql.connection.commit()
            cur.close()

            flash('Archivo cargado correctamente ✔️')
            return redirect(url_for('clients.docs'))

    # Realizar la consulta para obtener los documentos del usuario con el ID proporcionado
    cur = mysql.connection.cursor()
    cur.execute("SELECT id, filename, status, changeRequest FROM files WHERE user_id = %s", (user_id,))
    documents = cur.fetchall()
    cur.close()

    return render_template('/clientuser/docs.jinja', user_id=user_id, documents=documents)   

@clients.route('/request_change/<int:document_id>', methods=['POST'])
@client_required
@login_required
def request_change_document(document_id):
    # Ensure that the document belongs to the current user
    cur = mysql.connection.cursor()
    cur.execute("SELECT user_id FROM files WHERE id = %s", (document_id,))
    result = cur.fetchone()

    if result and result[0] == current_user.id:
        # Update the changeRequest field to 1
        cur.execute("UPDATE files SET changeRequest = 1 WHERE id = %s", (document_id,))
        mysql.connection.commit()
        cur.close()
        flash('Solicitud de cambio enviada correctamente ✔️')
    else:
        flash('No tienes permisos para solicitar cambio de este documento ❌')

    return redirect(url_for('clients.docs'))

@clients.route('/delete_document/<int:document_id>', methods=['POST'])
@client_required
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


#-----------------listado de los pedidos del cliente---------------------
@clients.route('/orders')
@client_required
@login_required
def orders():
    user_id = current_user.id
    cur = mysql.connection.cursor()
    #tomamos id la fecha y total de los pedidos del usuario actual
    cur.execute("SELECT id, order_date, total, cancel_status FROM orders WHERE clientUser_id = %s AND (cancel_status != 0 OR cancel_status IS NULL)", (user_id,))
    orders_data = cur.fetchall()
    cur.close()

    # Renderizar la plantilla con los datos obtenidos
    return render_template('/clientuser/orders.jinja', orders_data=orders_data)
    
#-----------------listado de los pedidos cancelados del cliente-------------------
@clients.route('/canceledOrders')
@client_required
@login_required
def canceledOrders():

    user_id = current_user.id
    cur = mysql.connection.cursor()
    #tomamos id la fecha y total de los pedidos del usuario actual
    cur.execute("SELECT id, order_date, total, cancel_status FROM orders WHERE clientUser_id = %s AND cancel_status = 0", (user_id,))
    orders_data = cur.fetchall()
    cur.close()

    # Renderizar la plantilla con los datos obtenidos
    return render_template('/clientuser/canceledOrders.jinja', orders_data=orders_data)



@clients.route('/cancel_order_request/<int:order_id>', methods=['POST'])
@client_required
@login_required
def cancel_order_request(order_id):
    if request.method == 'POST':
        
        user_id = current_user.id
        cur = mysql.connection.cursor()
        
        # Update the cancel_status to 1 for the specified order
        cur.execute("UPDATE orders SET cancel_status = 1 WHERE id = %s AND clientUser_id = %s", (order_id, user_id))
        mysql.connection.commit()
        cur.close()
        
        #flash('Order canceled successfully', 'success')
    
    # Redirect back to the list of orders
    return redirect(url_for('clients.orders'))


@clients.route('/orders/info/<int:id_order>')
@client_required
@login_required
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
    WHERE o.id = %s AND (o.clientUser_id = %s OR %s = 1)
    """, (id_order, current_user.id, current_user.tipoUsuario))
    
    order_info = cur.fetchone()
    if order_info is None:
        flash('No tienes permiso para ver este pedido.', 'error')
        return redirect(url_for('clients.orders'))
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
@client_required
@login_required
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
@client_required
@login_required
def products():
    user_id = current_user.id

    cur = mysql.connection.cursor() 
    cur.execute("SELECT id, name, image, price, id_Machine, sell_price FROM products")
    product_data = cur.fetchall()

    # Crear una lista para almacenar los productos como dicconarios
    products = [] 
    for product in product_data: #itera sobre los datos de los productos obtenidos
        product_dict = { #crear un diccionario para cada producto con id, name, image y price
            'id': product[0],
            'name': product[1],
            'image': product[2],
            'price': product[3],
            'id_Machine' : product[4],
            'sell_price': product[5]
        }
        products.append(product_dict) #agrega el diccionario del producto a la lista de productos

    cur.close()
    
    # Pass the selected purchase option to the template
    purchase_option = request.args.get('purchase_option', 'renta')

    return render_template('/clientuser/products.jinja', user_id=user_id, products=products, purchase_option=purchase_option)


# -------------Peticion de productos/Place order------------------------
@clients.route('/clientuser/place_order', methods=['POST'])
@client_required
@login_required
def place_order():
    if request.method == 'POST':
        client_user_id = current_user.id
        cart_machine_ids_str = request.form.get('cart_machine_ids', '')
        cart_weeks_str = request.form.get('cart_weeks')

        if not cart_machine_ids_str or not cart_weeks_str:
            flash('El carrito está vacío o es inválido.', 'error')
            return redirect(url_for('clients.products'))

        try:
            cart_weeks = json.loads(cart_weeks_str)
        except (TypeError, ValueError, json.JSONDecodeError):
            flash('No se pudo leer el carrito.', 'error')
            return redirect(url_for('clients.products'))

        # Variable para almacenar el tipo del pedido
        order_type = 1  # Inicialmente, establecemos el tipo en 1 (renta)

        cur = mysql.connection.cursor()
        cur.execute("SELECT id_Machine, price, sell_price FROM products")
        catalog = {
            str(row[0]): {'rent': row[1], 'sell': row[2]}
            for row in cur.fetchall()
        }

        line_items = []
        cart_total = 0
        for machine_id in cart_machine_ids_str.split(','):
            machine_id = machine_id.strip()
            if not machine_id:
                continue
            machine_data = cart_weeks.get(machine_id) or {}
            machine_type = str(machine_data.get('type', '1'))
            try:
                weeks = int(machine_data.get('weeks') or 1)
            except (TypeError, ValueError):
                weeks = 1
            weeks = max(1, weeks)

            prices = catalog.get(machine_id)
            if not prices:
                continue

            if machine_type == "0":
                order_type = 0
                line_price = float(prices['sell'] or 0)
            else:
                line_price = float(prices['rent'] or 0) * weeks

            cart_total += line_price
            line_items.append((machine_id, weeks, line_price, machine_type))

        if not line_items:
            cur.close()
            flash('El carrito está vacío o es inválido.', 'error')
            return redirect(url_for('clients.products'))

        cur.execute(
            "INSERT INTO orders (clientUser_id, total, type) VALUES (%s, %s, %s)",
            (client_user_id, cart_total, order_type),
        )
        mysql.connection.commit()
        order_id = cur.lastrowid

        for machine_id, weeks, price, machine_type in line_items:
            cur.execute(
                "INSERT INTO machineorders (order_id, machine_id, weeks, price, type) VALUES (%s, %s, %s, %s, %s)",
                (order_id, machine_id, weeks, price, machine_type),
            )
            mysql.connection.commit()

        cur.close()

        return redirect(url_for('clients.products'))

    return redirect(url_for('clients.products'))


@clients.route('/fetch_notifications')
@client_required
def fetch_notifications():
    user_id = current_user.id

    cur = mysql.connection.cursor()
    cur.execute("SELECT id, filename, status FROM files WHERE user_id = %s", (user_id,))
    notifications = cur.fetchall()
    cur.close()

    # Se muestra en formato JSON
    return jsonify(notifications)
    