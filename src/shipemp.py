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
import os

shipemp = Blueprint('shipemp', __name__)

GOOGLE_MAPS_API_KEY = "AIzaSyAJzmmel__k7beEoyd-LhonGRhMrR2mEJE"


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
    # Establish a cursor to execute SQL queries
    cursor = mysql.connection.cursor()
    query = '''
    SELECT orders.id, GROUP_CONCAT(machineorders.machine_id) AS machine_ids, 
           CONCAT(orders.address, ', ', orders.postalCode) AS delivery_address
    FROM orders
    INNER JOIN machineorders ON orders.id = machineorders.order_id
    WHERE orders.verifiedDocs = 1 AND orders.paymentMade = 1 AND orders.shipmentMade = 0
    GROUP BY orders.id
    '''
    cursor.execute(query)
    # Fetch all the results
    data = cursor.fetchall()
    # Close the cursor and MySQL connection
    cursor.close()
    # Render the template with the data
    return render_template('/shipping/newOrders.jinja', data=data)


#--------------------ordenes-----------------------
@shipemp.route('/shipping/orders')
@shipping_required
def orders():
    # Establish a cursor to execute SQL queries
    cursor = mysql.connection.cursor()
    query = '''
    SELECT orders.id, GROUP_CONCAT(machineorders.machine_id) AS machine_ids, orders.address, orders.postalCode, orders.phoneNumber
    FROM orders
    INNER JOIN machineorders ON orders.id = machineorders.order_id
    WHERE orders.verifiedDocs = 1 AND orders.paymentMade = 1 AND orders.shipmentMade = 0
    GROUP BY orders.id, orders.address, orders.postalCode, orders.phoneNumber
    '''
    cursor.execute(query)
    # Fetch all the results
    data = cursor.fetchall()
    # Close the cursor and MySQL connection
    cursor.close()
    # Render the template with the data
    return render_template('/shipping/orders.jinja', data=data)


@shipemp.route('/shipping/completedOrders')
@shipping_required
def completedOrders():
    # Establish a cursor to execute SQL queries
    cursor = mysql.connection.cursor()
    query = '''
    SELECT orders.id, GROUP_CONCAT(machineorders.machine_id) AS machine_ids, orders.address, orders.postalCode, orders.phoneNumber
    FROM orders
    INNER JOIN machineorders ON orders.id = machineorders.order_id
    WHERE orders.verifiedDocs = 1 AND orders.paymentMade = 1 AND orders.shipmentMade = 1
    GROUP BY orders.id, orders.address, orders.postalCode, orders.phoneNumber
    '''
    cursor.execute(query)
    # Fetch all the results
    data = cursor.fetchall()
    # Close the cursor and MySQL connection
    cursor.close()
    # Render the template with the data
    return render_template('/shipping/completedOrders.jinja', data=data)


#---------Cambiar estado de pedido a enviado------------

@shipemp.route('/shipping/markShipped/<int:order_id>', methods=['GET', 'POST'])
@shipping_required
def markShipped(order_id):
    # Establish a cursor to execute SQL queries
    cursor = mysql.connection.cursor()

    # Update the shipmentMade field to 1 for the specified order ID
    update_query = "UPDATE orders SET shipmentMade = 1 WHERE id = %s"
    cursor.execute(update_query, (order_id,))

    # Commit the changes to the database
    mysql.connection.commit()

    # Close the cursor and MySQL connection
    cursor.close()

    # Redirect back to the newOrders page
    return redirect(url_for('shipemp.orders'))

#---------Cambiar estado de pedido a no enviado------------

@shipemp.route('/shipping/unmarkShipped/<int:order_id>', methods=['GET', 'POST'])
@shipping_required
def unmarkShipped(order_id):
    # Establish a cursor to execute SQL queries
    cursor = mysql.connection.cursor()

    # Update the shipmentMade field to 1 for the specified order ID
    update_query = "UPDATE orders SET shipmentMade = 0 WHERE id = %s"
    cursor.execute(update_query, (order_id,))

    # Commit the changes to the database
    mysql.connection.commit()

    # Close the cursor and MySQL connection
    cursor.close()

    # Redirect back to the newOrders page
    return redirect(url_for('shipemp.orders'))

#--------------------------------------------------------
@shipemp.route('/shipping/ordersInfo/<int:order_id>')
@shipping_required
def ordersInfo(order_id):
    # Establish a cursor to execute SQL queries
    cursor = mysql.connection.cursor()

    # Query to retrieve order information, machine details, and user fullname
    query = '''
    SELECT orders.id, 
           machineorders.id AS machine_order_id, 
           machineorders.machine_id, 
           machines.model, 
           machines.brand, 
           user.fullname,  -- Use 'user' for the table name
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

    # Fetch the result
    order_info = cursor.fetchone()

    # Close the cursor and MySQL connection
    cursor.close()

    # Render the template with the retrieved data
    return render_template('shipping/ordersInfo.jinja', order_info=order_info)

#-------Rutas con google maps

@shipemp.route('/shipping/routes')
@shipping_required
def routes():
    # Retrieve the URL-encoded startLocation and endLocation parameters
    start_location = request.args.get('startLocation')
    end_location = request.args.get('endLocation')

    # Decode the URL-encoded parameters
    start_location_decoded = unquote(start_location)
    end_location_decoded = unquote(end_location)

    return render_template('/shipping/routes.jinja', start_location=start_location_decoded, end_location=end_location_decoded, api_key=GOOGLE_MAPS_API_KEY)

