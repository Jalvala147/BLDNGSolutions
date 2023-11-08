from flask_mysqldb import MySQL
from flask import render_template, session, flash
from functools import wraps
from flask import flash, redirect, url_for
from flask_login import current_user
from flask import Blueprint
from flask import request
from flask import Flask, render_template, jsonify
from urllib.parse import urlencode, unquote

app = Flask(__name__)
mysql = MySQL()

shipemp = Blueprint('shipemp', __name__)

GOOGLE_MAPS_API_KEY = "AIzaSyCiYij4rKyNlM9uXBUDjhlnfGxSzm_xi9M"


# Decorador para envíos (tipoUsuario = 2 y areaUsuario = 6 o tipoUsuario = 1 y areaUsuario = 1)
def shipping_required(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if not current_user.is_authenticated:
            flash("Debes iniciar sesión para acceder a esta página.")
            return redirect(url_for('loginemp'))
        elif not (current_user.tipoUsuario == 2 and current_user.areaUsuario == 6) and not (current_user.tipoUsuario == 1 and current_user.areaUsuario == 1):
            flash("Acceso no autorizado. Debes ser un empleado de envíos para acceder a esta página.")
            return redirect(url_for('loginemp'))
        return func(*args, **kwargs)
    return decorated_view


@shipemp.route('/shipping_home')
@shipping_required
def shipping_home():
    # Código necesario para la página "shipping/shipHome.jinja"
    return render_template('shipping/shipHome.jinja')

#--------------Nuevs ordenes(solo informacion basica)----------
@shipemp.route('/shipping/newOrders')
@shipping_required
def newOrders():
    # cursor
    cursor = mysql.connection.cursor()
    query = '''
    SELECT orders.id, 
           GROUP_CONCAT(machines.brand, ' ', machines.model) AS machine_info, 
           CONCAT(orders.address, ', ', orders.postalCode) AS delivery_address
    FROM orders
    INNER JOIN machineorders ON orders.id = machineorders.order_id
    INNER JOIN machines ON machineorders.machine_id = machines.id_Machine
    WHERE orders.verifiedDocs = 1 AND orders.paymentMade = 1 AND orders.shipmentMade = 0
    GROUP BY orders.id
    '''
    cursor.execute(query)

    data = cursor.fetchall()

    cursor.close()
    # Renderizar la plantilla con la informacion obtenida de la bd
    return render_template('/shipping/newOrders.jinja', data=data)

@shipemp.route('/ship_notifications')
@shipping_required
def ship_notifications():

    cursor = mysql.connection.cursor()
    query = '''
    SELECT orders.id, 
           GROUP_CONCAT(machines.brand, ' ', machines.model) AS machine_info, 
           CONCAT(orders.address, ', ', orders.postalCode) AS delivery_address
    FROM orders
    INNER JOIN machineorders ON orders.id = machineorders.order_id
    INNER JOIN machines ON machineorders.machine_id = machines.id_Machine
    WHERE orders.verifiedDocs = 1 AND orders.paymentMade = 1 AND orders.shipmentMade = 0
    GROUP BY orders.id
    '''
    cursor.execute(query)
    data = cursor.fetchall()
    cursor.close()

    return jsonify(data)


#--------------------Órdenes-----------------------
@shipemp.route('/shipping/orders')
@shipping_required
def orders():
    # Establecer un cursor para ejecutar consultas SQL
    cursor = mysql.connection.cursor()
    query = '''
    SELECT orders.id, GROUP_CONCAT(machineorders.machine_id) AS machine_ids, orders.address, orders.postalCode, orders.phoneNumber
    FROM orders
    INNER JOIN machineorders ON orders.id = machineorders.order_id
    WHERE orders.verifiedDocs = 1 AND orders.paymentMade = 1 AND orders.shipmentMade = 0
    GROUP BY orders.id, orders.address, orders.postalCode, orders.phoneNumber
    '''
    cursor.execute(query)
    # Obtener todos los resultados
    data = cursor.fetchall()
    # Cerrar el cursor y la conexión a MySQL
    cursor.close()
    # Renderizar la plantilla con los datos
    return render_template('/shipping/orders.jinja', data=data)


@shipemp.route('/shipping/completedOrders')
@shipping_required
def completedOrders():
    # Establecer un cursor para ejecutar consultas SQL
    cursor = mysql.connection.cursor()
    query = '''
    SELECT orders.id, GROUP_CONCAT(machineorders.machine_id) AS machine_ids, orders.address, orders.postalCode, orders.phoneNumber
    FROM orders
    INNER JOIN machineorders ON orders.id = machineorders.order_id
    WHERE orders.verifiedDocs = 1 AND orders.paymentMade = 1 AND orders.shipmentMade = 1
    GROUP BY orders.id, orders.address, orders.postalCode, orders.phoneNumber
    '''
    cursor.execute(query)
    # Obtener todos los resultados
    data = cursor.fetchall()
    # Cerrar el cursor y la conexión a MySQL
    cursor.close()
    # Renderizar la plantilla con los datos
    return render_template('/shipping/completedOrders.jinja', data=data)



#---------Cambiar el Estado del Pedido a Enviado------------
@shipemp.route('/shipping/markShipped/<int:order_id>', methods=['GET', 'POST'])
@shipping_required
def markShipped(order_id):
    # Establecer un cursor para ejecutar consultas SQL
    cursor = mysql.connection.cursor()

    # Actualizar el campo shipmentMade a 1 para el ID de orden especificado
    update_query = "UPDATE orders SET shipmentMade = 1 WHERE id = %s"
    cursor.execute(update_query, (order_id,))

    # Confirmar los cambios en la base de datos
    mysql.connection.commit()

    # Cerrar el cursor y la conexión a MySQL
    cursor.close()

    # Redirigir de nuevo a la página de newOrders
    return redirect(url_for('shipemp.orders'))


#---------Cambiar el Estado del Pedido a No Enviado------------
@shipemp.route('/shipping/unmarkShipped/<int:order_id>', methods=['GET', 'POST'])
@shipping_required
def unmarkShipped(order_id):
    # Establecer un cursor para ejecutar consultas SQL
    cursor = mysql.connection.cursor()

    # Actualizar el campo shipmentMade a 0 para el ID de orden especificado
    update_query = "UPDATE orders SET shipmentMade = 0 WHERE id = %s"
    cursor.execute(update_query, (order_id,))

    # Confirmar los cambios en la base de datos
    mysql.connection.commit()

    # Cerrar el cursor y la conexión a MySQL
    cursor.close()

    # Redirigir de nuevo a la página de newOrders
    return redirect(url_for('shipemp.orders'))

#-------------------Información de las Órdenes-------------------
@shipemp.route('/shipping/ordersInfo/<int:order_id>')
@shipping_required
def ordersInfo(order_id):
    # Establecer un cursor para ejecutar consultas SQL
    cursor = mysql.connection.cursor()

    # Consulta para recuperar la información de la orden, detalles de la máquina y el nombre completo del usuario
    query = '''
    SELECT orders.id, 
           machineorders.id AS machine_order_id, 
           machineorders.machine_id, 
           machines.model, 
           machines.brand, 
           user.fullname, 
           orders.address, 
           orders.postalCode, 
           orders.phoneNumber
    FROM orders
    INNER JOIN machineorders ON orders.id = machineorders.order_id
    INNER JOIN machines ON machineorders.machine_id = machines.id_Machine
    INNER JOIN user ON orders.clientUser_id = user.id
    WHERE orders.id = %s
    '''

    cursor.execute(query, (order_id,))

    # Obtener el resultado
    order_info = cursor.fetchone()

    # Cerrar el cursor y la conexión a MySQL
    cursor.close()

    # Renderizar la plantilla con los datos recuperados
    return render_template('shipping/ordersInfo.jinja', order_info=order_info)


#-------Rutas con Google Maps
@shipemp.route('/shipping/routes')
@shipping_required
def routes():
    # Recuperar los parámetros startLocation y endLocation codificados en URL
    start_location = request.args.get('startLocation')
    end_location = request.args.get('endLocation')

    # Decodificar los parámetros codificados en URL
    start_location_decoded = unquote(start_location)
    end_location_decoded = unquote(end_location)

    return render_template('/shipping/routes.jinja', start_location=start_location_decoded, end_location=end_location_decoded, api_key=GOOGLE_MAPS_API_KEY)
