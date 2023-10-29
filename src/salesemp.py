from flask_mysqldb import MySQL
from flask import render_template, session, redirect, flash
from flask_wtf.csrf import CSRFProtect
from flask import Blueprint
from flask import request
from flask import Flask
from flask import url_for
from flask import redirect  
from flask_login import LoginManager, login_user, login_required, current_user, logout_user
from functools import wraps
from io import BytesIO
import os
import io
from flask import jsonify
from flask import send_from_directory, make_response
from flask import send_file


app = Flask(__name__)
mysql = MySQL()


salesemp = Blueprint('salesemp', __name__)

csrf = CSRFProtect()


@salesemp.route('/logout')
def logout():
    logout_user()
    session.pop('username', None)
    return redirect(url_for('startpage'))
#------------------------------------------------------------------------
# Decorador para ventas (tipoUsuario = 2 y areaUsuario = 2 o tipoUsuario = 1 y areaUsuario = 1)
def sales_required(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if not current_user.is_authenticated:
            flash("Debes iniciar sesión.")
            return redirect(url_for('loginemp'))
        elif not (current_user.tipoUsuario == 2 and current_user.areaUsuario == 2) and not (current_user.tipoUsuario == 1 and current_user.areaUsuario == 1):
            flash("Acceso no autorizado. Debes ser un empleado de ventas o un administrador para acceder a esta página.")
            return redirect(url_for('loginemp'))
        return func(*args, **kwargs)
    return decorated_view

#----------------------------Listado de ventas---------------------------
@salesemp.route('/salesEmpArea/salesList')
@sales_required
def salesList():
    
    cur = mysql.connection.cursor()
    cur.execute("SELECT id, cancel_status FROM orders WHERE status = 1 AND (cancel_status != 0 OR cancel_status IS NULL) AND type = 0")

    orders_ids = cur.fetchall()
    cur.close
    return render_template('/salesEmpArea/salesList.jinja', order_ids=orders_ids)


#-----------------------------Listado de rentas-------------------------
@salesemp.route('/salesEmpArea/rentsList')   
@sales_required
def rentsList():
    cur = mysql.connection.cursor()
    cur.execute("SELECT id, cancel_status FROM orders WHERE status = 1 AND (cancel_status != 0 OR cancel_status IS NULL) AND type = 1")

    orders_ids = cur.fetchall()
    cur.close
    return render_template('/salesEmpArea/rentsList.jinja', order_ids=orders_ids)

#-------------Aceptar solicitudes de cancelacion de pedidos
@salesemp.route('/salesEmpArea/acceptCancelRequest/<int:order_id>', methods=['POST'])
def acceptCancelRequest(order_id):
    if request.method == 'POST':
        # Actualiza el valor de cancel_status a 0 en la base de datos
        cur = mysql.connection.cursor()
        cur.execute("UPDATE orders SET cancel_status = 0 WHERE id = %s", (order_id,))
        mysql.connection.commit()
        cur.close()
        flash('Solicitud de cancelación aceptada', 'success')
        return '', 204

#Listado de rentas canceladas
@salesemp.route('/salesEmpArea/canceledRentsList')   
@sales_required
def canceledRentsList():
    cur = mysql.connection.cursor()
    cur.execute("SELECT id, cancel_status FROM orders WHERE status = 1 AND cancel_status = 0 AND type = 1")

    orders_ids = cur.fetchall()
    cur.close
    return render_template('/salesEmpArea/canceledRentsList.jinja', order_ids=orders_ids)

#Listado de ventas canceladas
@salesemp.route('/salesEmpArea/canceledSalesList')   
@sales_required
def canceledSalesList():
    cur = mysql.connection.cursor()
    cur.execute("SELECT id, cancel_status FROM orders WHERE status = 1 AND cancel_status = 0 AND type = 0")

    orders_ids = cur.fetchall()
    cur.close
    return render_template('/salesEmpArea/canceledSalesList.jinja', order_ids=orders_ids)

#Funcion para actualizar el campo verifiedDocs cuando el empleado haya verificado los documentos
@salesemp.route('/salesEmpArea/updateVerifiedDocs/<int:order_id>')
@sales_required
def update_verified_docs(order_id):
    try:
        cur = mysql.connection.cursor()
        # Actualiza el campo verifiedDocs a 1 para la orden con el ID especificado
        cur.execute("UPDATE orders SET verifiedDocs = 1 WHERE id = %s", (order_id,))
        mysql.connection.commit()
        cur.close()
        flash("Documentos verificados con éxito.", "success")  
        return redirect(url_for('salesemp.rentsList'))  
    except Exception as e:
        flash("Error al verificar los documentos.", "error")  
        return redirect(url_for('salesemp.rentsList'))

#Funcion para actualizar el campo paymentMade a 1 cuando el empleado haya verificado que el pago fue recibido
@salesemp.route('/salesEmpArea/updatePaymentMade/<int:order_id>')
@sales_required
def update_payment_made(order_id):
    try:
        cur = mysql.connection.cursor()
        # Actualiza el campo paymentMade a 1 para la orden con el ID especificado
        cur.execute("UPDATE orders SET paymentMade = 1 WHERE id = %s", (order_id,))
        mysql.connection.commit()
        cur.close()
        flash("Pago registrado con éxito.", "success")  
        return redirect(url_for('salesemp.rentsList'))  
    except Exception as e:
        flash("Error al registrar el pago.", "error")  
        return redirect(url_for('salesemp.rentsList'))


#---------------Mostrar toda la informacion de las tablas orders y machineorders para rentas---------
@salesemp.route('/salesEmpArea/rentsDetails/<int:order_id>')
@sales_required
def orderDetails(order_id):
    cur = mysql.connection.cursor()

    # Consulta para obtener los detalles del pedido, las máquinas, semanas, precios y el total correspondiente al order_id en la tabla machineorders
    query = """
    SELECT o.clientUser_id, GROUP_CONCAT(CONCAT(m.brand, ' ', m.model)) AS machines, o.order_date, u.fullname, GROUP_CONCAT(mo.weeks) AS weeks, GROUP_CONCAT(mo.price) AS prices, SUM(mo.price) AS order_total
    FROM orders o
    INNER JOIN machineorders mo ON o.id = mo.order_id
    INNER JOIN machines m ON mo.machine_id = m.id_machine
    INNER JOIN user u ON o.clientUser_id = u.id
    WHERE o.id = %s
    GROUP BY o.clientUser_id, o.order_date, u.fullname
    """
    cur.execute(query, (order_id,))
    order_details = cur.fetchone()

    if order_details is not None:
        # Consulta para obtener la información de la tabla "orders" relacionada con el order_id
        order_info_query = """
        SELECT address, postalCode, rfc, phoneNumber, paymentMethod
        FROM orders
        WHERE id = %s
        """
        cur.execute(order_info_query, (order_id,))
        order_info = cur.fetchone()
        cur.close()

        # Separar las semanas y precios en listas
        weeks = order_details[4].split(',')
        prices = order_details[5].split(',')

        return render_template('/salesEmpArea/rentsDetails.jinja', order_id=order_id, order_details=order_details, weeks=weeks, prices=prices, order_info=order_info)
    else:
        # Manejo el caso en el que no se encuentre ningún pedido con el order_id
        return redirect(url_for('salesemp.rentsList'))
    

#---------------Mostrar toda la informacion de las tablas orders y machineorders para ventas---------
@salesemp.route('/salesEmpArea/salesDetails/<int:order_id>')
@sales_required
def salesDetails(order_id):
    cur = mysql.connection.cursor()

    # Consulta para obtener los detalles del pedido, las máquinas, semanas, precios y el total correspondiente al order_id en la tabla machineorders
    query = """
    SELECT o.clientUser_id, GROUP_CONCAT(CONCAT(m.brand, ' ', m.model)) AS machines, o.order_date, u.fullname, GROUP_CONCAT(mo.weeks) AS weeks, GROUP_CONCAT(mo.price) AS prices, SUM(mo.price) AS order_total
    FROM orders o
    INNER JOIN machineorders mo ON o.id = mo.order_id
    INNER JOIN machines m ON mo.machine_id = m.id_machine
    INNER JOIN user u ON o.clientUser_id = u.id
    WHERE o.id = %s
    GROUP BY o.clientUser_id, o.order_date, u.fullname
    """
    cur.execute(query, (order_id,))
    order_details = cur.fetchone()

    if order_details is not None:
        # Consulta para obtener la información de la tabla "orders" relacionada con el order_id
        order_info_query = """
        SELECT address, postalCode, rfc, phoneNumber, paymentMethod
        FROM orders
        WHERE id = %s
        """
        cur.execute(order_info_query, (order_id,))
        order_info = cur.fetchone()
        cur.close()

        # Separar las semanas y precios en listas
        weeks = order_details[4].split(',')
        prices = order_details[5].split(',')

        return render_template('/salesEmpArea/salesDetails.jinja', order_id=order_id, order_details=order_details, weeks=weeks, prices=prices, order_info=order_info)
    else:
        # Manejo el caso en el que no se encuentre ningún pedido con el order_id
        return redirect(url_for('salesemp.salesList'))


#---------------Detalles editables--------------------

@salesemp.route('/salesEmpArea/actualizarOrden/<int:order_id>', methods=['POST'])
@sales_required
def actualizarOrden(order_id):
    if request.method == 'POST':
        new_address = request.form['address']
        new_postalCode = request.form['postalCode']
        new_rfc = request.form['rfc']
        new_phoneNumber = request.form['phoneNumber']
        new_paymentMethod = request.form['paymentMethod']

        # Realiza una consulta SQL para actualizar la información en la base de datos
        cur = mysql.connection.cursor()
        update_query = """
        UPDATE orders
        SET address = %s, postalCode = %s, rfc = %s, phoneNumber = %s, paymentMethod = %s
        WHERE id = %s
        """
        cur.execute(update_query, (new_address, new_postalCode, new_rfc, new_phoneNumber, new_paymentMethod, order_id))
        mysql.connection.commit()
        cur.close()

        # no se hace redirección para que no se cambie de ventana
        return '', 204



#Cambio de estado cuando se marque como completada una orden
@salesemp.route('/salesEmpArea/orderCompleted/<int:order_id>')
@sales_required
def orderCompleted(order_id):
    cur = mysql.connection.cursor()
    
    # Actualizar el estado a 0
    update_order_query = "UPDATE orders SET status = 0 WHERE id = %s"
    cur.execute(update_order_query, (order_id,))
    mysql.connection.commit()
    
    cur.close()
    
    return redirect(url_for('salesemp.rentsList'))

#Listar los pedidos completados (con el status cambiado)
@salesemp.route('/salesEmpArea/completedOrders')   
@sales_required
def completedOrders():
    cur = mysql.connection.cursor()
    cur.execute("SELECT id FROM orders WHERE status = 0")
    orders_ids = cur.fetchall()
    cur.close
    return render_template('/salesEmpArea/completedOrders.jinja', order_ids=orders_ids)

#---------


@salesemp.route('/salesEmpArea/autoProgress/<int:order_id>')
@sales_required
def auto_progress(order_id):
    try:
        # Consulta la base de datos para obtener el valor de verifiedDocs y paymentMade para la orden actual
        cur = mysql.connection.cursor()
        cur.execute("SELECT verifiedDocs, paymentMade FROM orders WHERE id = %s", (order_id,))
        result = cur.fetchone()
        cur.close()

        # Verifica los valores de verifiedDocs y paymentMade
        verified_docs = result[0]
        payment_made = result[1]

        # Determina el nuevo valor de currentStep en función de los valores en la base de datos
        currentStep = 1  # Por defecto, el primer círculo está activo

        if verified_docs == 1:
            currentStep = 2  # Si verifiedDocs es 1, avanza al segundo círculo

        if payment_made == 1:
            currentStep = 3  # Si paymentMade es 1, avanza al tercer círculo

        # Renderiza la plantilla HTML con el nuevo valor de currentStep
        return render_template('/clientuser/statusprogress.jinja', currentStep=currentStep)

    except Exception as e:
        # Maneja cualquier error que pueda ocurrir durante la consulta
        flash("Error al obtener información de la base de datos.", "error")
        return redirect(url_for('salesemp.rentsList'))

#------------------------------Guardado de archivos------------------------
@salesemp.route('/download_file/<filename>')
def download_file(filename):
    # Obtén el archivo blob de la base de datos
    cur = mysql.connection.cursor()
    cur.execute("SELECT file_data FROM files WHERE filename = %s", (filename,))
    file_data = cur.fetchone()[0]
    cur.close()

    # Crea una respuesta para enviar el archivo al cliente
    response = make_response(file_data)
    response.headers["Content-Disposition"] = f"attachment; filename={filename}"
    
    return response
    
    
@salesemp.route('/view_file/<filename>')
def view_file(filename):
    # Obtén el archivo blob de la base de datos
    cur = mysql.connection.cursor()
    cur.execute("SELECT file_data FROM files WHERE filename = %s", (filename,))
    file_data = cur.fetchone()[0]
    cur.close()

    # Crea una respuesta para enviar el archivo al navegador
    response = make_response(file_data)
    response.headers["Content-Type"] = "application/pdf"  # Establece el tipo de contenido según el tipo de archivo
    
    return response


@salesemp.route('/salesEmpArea/uploadedDocuments/<int:user_id>')
@sales_required
def uploaded_documents(user_id):
    # Realizar la consulta para obtener los documentos del usuario con el ID proporcionado
    cur = mysql.connection.cursor()
    cur.execute("SELECT id, filename, status, changeRequest FROM files WHERE user_id = %s", (user_id,))
    documents = cur.fetchall()
    cur.close()

    # Pasar los documentos a la plantilla uploaded_documents.jinja
    return render_template('/salesEmpArea/uploadedDocuments.jinja', user_id=user_id, documents=documents)


@salesemp.route('/accept_change_request/<int:file_id>/<int:user_id>')
@sales_required
def accept_change_request(file_id, user_id):
    # Actualiza el campo changeRequest a 0 para el documento con el ID proporcionado
    cur = mysql.connection.cursor()
    cur.execute("UPDATE files SET changeRequest = 0 WHERE id = %s AND user_id = %s", (file_id, user_id))
    mysql.connection.commit()
    cur.close()

    # Redirige de nuevo a la página de documentos del usuario
    return redirect(url_for('salesemp.uploaded_documents', user_id=user_id))

#----------------------------------------------------


@salesemp.route('/mark_as_completed/<int:file_id>/<int:user_id>')
@sales_required
def mark_as_completed(file_id, user_id):
    # Actualiza el estado en la base de datos a completado (1)
    cur = mysql.connection.cursor()
    cur.execute("UPDATE files SET status = 1 WHERE id = %s AND user_id = %s", (file_id, user_id))
    mysql.connection.commit()
    cur.close()

    # Obtén los documentos actualizados del mismo ID de usuario
    cur = mysql.connection.cursor()
    cur.execute("SELECT id, filename, status FROM files WHERE user_id = %s", (user_id,))
    documents = cur.fetchall()
    cur.close()

    return redirect(url_for('salesemp.uploaded_documents', user_id=user_id))


@salesemp.route('/mark_as_incomplete/<int:file_id>/<int:user_id>')
@sales_required
def mark_as_incomplete(file_id, user_id):
    # Actualiza el estado en la base de datos a incompleto (0)
    cur = mysql.connection.cursor()
    cur.execute("UPDATE files SET status = 0 WHERE id = %s AND user_id = %s", (file_id, user_id))
    mysql.connection.commit()
    cur.close()

    # Obtén los documentos actualizados del mismo ID de usuario
    cur = mysql.connection.cursor()
    cur.execute("SELECT id, filename, status FROM files WHERE user_id = %s", (user_id,))
    documents = cur.fetchall()
    cur.close()

    return redirect(url_for('salesemp.uploaded_documents', user_id=user_id))




#----------------------------------------------------

@salesemp.route('/salesEmpArea/salesHome')   
@sales_required
def salesHome():
    return render_template('salesEmpArea/salesHome.jinja')


# Definimos la función clientsList para la ruta '/salesEmpArea/clientsList'
@salesemp.route('/salesEmpArea/clientsList')
@sales_required
def clientsList():
    cur = mysql.connection.cursor()
    cur.execute("SELECT id, username, fullname, email FROM user WHERE tipousuario = 3 AND areaUsuario = 4")
    users = cur.fetchall()
    cur.close()
    return render_template('salesEmpArea/clientsList.jinja', users=users)

#-----------------------------------------------------------

@salesemp.route('/salesEmpArea/newRequest')
@sales_required
def newRequest():
    cur = mysql.connection.cursor()
    # Joins
    cur.execute("""
        SELECT orders.id AS 'NO. DE SOLICITUD',
               user.fullname AS 'SOLICITANTE',
               user.email AS 'CORREO',
               GROUP_CONCAT(CONCAT(machines.brand, ' ', machines.model) ORDER BY machineorders.machine_id) AS 'MAQUINAS'
        FROM orders
        INNER JOIN user ON orders.ClientUser_id = user.id
        INNER JOIN machineorders ON orders.id = machineorders.order_id
        INNER JOIN machines ON machineorders.machine_id = machines.id_Machine
        WHERE orders.status = 1
        GROUP BY orders.id, user.fullname, user.email
    """)
    orders_data = cur.fetchall()
    cur.close()

    #Mandar los resultados al la plantilla newRequest.jinja y renderizarla
    return render_template('salesEmpArea/newRequest.jinja', orders=orders_data)


@salesemp.route('/salesEmpArea/updateType/<int:id_order>', methods=['POST'])
@sales_required
def update_type(id_order):
    if request.method == 'POST':
        cur = mysql.connection.cursor()

        # Obtiene la opción seleccionada del formulario
        new_type = request.form['type']

        # Actualiza el campo "type" en la base de datos para el registro correspondiente
        cur.execute("UPDATE machinesorders SET type = %s WHERE id_order = %s", (new_type, id_order))
        mysql.connection.commit()

        # Cierra el cursor
        cur.close()

    # Redirecciona nuevamente a la página de solicitudes después de la actualización
    return redirect(url_for('salesemp.newRequest'))


#-----------------------------------------------------------

# Ruta para mostrar la lista de prospectos
@salesemp.route('/salesEmpArea/prospects')  
@sales_required 
def prospects():
    cur = mysql.connection.cursor()
    cur.execute("SELECT id_Prospect, fullname, company, number, email FROM prospects WHERE contacted = 0")
    prospects = cur.fetchall()
    cur.close()

    return render_template('salesEmpArea/prospects.jinja', prospects=prospects)

# Ruta para agregar un nuevo prospecto
@salesemp.route('/salesEmpArea/prospects/add', methods=['GET', 'POST'])
@sales_required
def add_prospect():
    if request.method == 'POST':
        # Obtener los datos del formulario
        fullname = request.form['fullname']
        company = request.form['company']
        number = request.form['number']
        email = request.form['email']
        

        # Insertar un nuevo prospecto en la base de datos
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO prospects (fullname,company, number, email) VALUES (%s, %s, %s, %s)", (fullname, company, number, email ))
        mysql.connection.commit()
        cur.close()

        # Redirigir a la página de prospectos después de agregar el prospecto
        return redirect(url_for('salesemp.prospects'))
    else:
        # Mostrar el formulario para agregar un nuevo prospecto
        return render_template('salesEmpArea/prospects/add_prospect.jinja')

# Ruta para editar un prospecto existente
@salesemp.route('/salesEmpArea/prospects/edit/<int:prospect_id>', methods=['GET', 'POST'])
@sales_required
def edit_prospect(prospect_id):
    if request.method == 'POST':
        # Obtener los datos del formulario
        fullname = request.form['fullname']
        company = request.form['company']
        number = request.form['number']
        email = request.form['email']
        

        # Actualizar el prospecto en la base de datos
        cur = mysql.connection.cursor()
        cur.execute("UPDATE prospects SET fullname = %s, number = %s, email = %s, company = %s WHERE id_Prospect = %s", (fullname, number, email, company, prospect_id))
        mysql.connection.commit()
        cur.close()

        # Redirigir a la página de prospectos después de editar el prospecto
        return redirect(url_for('salesemp.prospects'))
    else:
        # Obtener los detalles actuales del prospecto de la base de datos
        cur = mysql.connection.cursor()
        cur.execute("SELECT id_Prospect, fullname, number, email, company FROM prospects WHERE id_Prospect = %s", (prospect_id,))
        prospect_details = cur.fetchone()
        cur.close()

        # Mostrar el formulario de edición con los detalles actuales del prospecto
        return render_template('salesEmpArea/prospects/edit_prospect.jinja', prospect=prospect_details)

@salesemp.route('/salesEmpArea/prospects/mark_contacted/<int:prospect_id>')
@sales_required
def mark_contacted(prospect_id):
    # Actualiza el campo 'contacted' en la base de datos a 1 para el prospecto específico
    cur = mysql.connection.cursor()
    cur.execute("UPDATE prospects SET contacted = 1 WHERE id_Prospect = %s", (prospect_id,))
    mysql.connection.commit()
    cur.close()

    # Redirige de vuelta a la página de prospectos después de marcar como contactado
    return redirect(url_for('salesemp.prospects'))

# Ruta para mostrar la lista de prospectos contactados
@salesemp.route('/salesEmpArea/contactedProspects')  
@sales_required 
def contactedProspects():
    cur = mysql.connection.cursor()
    cur.execute("SELECT id_Prospect, fullname, company, number, email FROM prospects WHERE contacted = 1")
    prospects = cur.fetchall()
    cur.close()

    return render_template('salesEmpArea/prospects/contactedProspects.jinja', prospects=prospects)
