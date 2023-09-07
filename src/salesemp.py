from flask_mysqldb import MySQL
from flask import render_template, session, redirect, flash
from flask_wtf.csrf import CSRFProtect
from flask import Blueprint
from flask import request
from flask import Flask
from flask import url_for
from flask import redirect  
from flask_login import LoginManager, login_user, login_required, current_user, logout_user
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

@salesemp.route('/salesEmpArea/salesList')
def salesList():
    # Obtén una conexión a la base de datos
    cur = mysql.connection.cursor()

    # Realiza la consulta a la base de datos
    cur.execute("SELECT maquina, num_orden, estado_pedido FROM tabla_pedidos")

    # Obtiene los resultados de la consulta
    pedidos = cur.fetchall()

    # Cierra el cursor
    cur.close()

    # Pasa los datos a la plantilla salesList.jinja para mostrarlos en la tabla
    return render_template('/salesEmpArea/salesList.jinja', pedidos=pedidos)

#Listado de rentas
@salesemp.route('/salesEmpArea/rentsList')   
def rentsList():
    cur = mysql.connection.cursor()
    cur.execute("SELECT id FROM orders")
    orders_ids = cur.fetchall()
    cur.close
    return render_template('/salesEmpArea/rentsList.jinja', order_ids=orders_ids)


@salesemp.route('/salesEmpArea/rentsDetails/<int:order_id>')
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
    cur.close()

    # Separar las semanas y precios en listas
    weeks = order_details[4].split(',')
    prices = order_details[5].split(',')

    return render_template('/salesEmpArea/rentsDetails.jinja', order_id=order_id, order_details=order_details, weeks=weeks, prices=prices)




@salesemp.route('/salesEmpArea/orderCompleted/<int:order_id>')
def orderCompleted(order_id):
    cur = mysql.connection.cursor()
    
    try:
        # borrar los registros hijos
        delete_machineorders_query = "DELETE FROM machineorders WHERE order_id = %s"
        cur.execute(delete_machineorders_query, (order_id,))
        mysql.connection.commit()
        
        # despues los padres
        delete_order_query = "DELETE FROM orders WHERE id = %s"
        cur.execute(delete_order_query, (order_id,))
        mysql.connection.commit()
        
        cur.close()
        
        
        return redirect(url_for('salesemp.rentsList'))
    except Exception as e:
        
        print(f"Error deleting order: {str(e)}")
        mysql.connection.rollback()  # Rollback the transaction
        cur.close()
        # Redirect or display an error message to the user
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
def uploaded_documents(user_id):
    # Realizar la consulta para obtener los documentos del usuario con el ID proporcionado
    cur = mysql.connection.cursor()
    cur.execute("SELECT id, filename FROM files WHERE user_id = %s", (user_id,))
    documents = cur.fetchall()
    cur.close()

    # Pasar los documentos a la plantilla uploaded_documents.jinja
    return render_template('/salesEmpArea/uploadedDocuments.jinja', user_id=user_id, documents=documents)

#----------------------------------------------------


@salesemp.route('/mark_as_completed/<int:file_id>/<int:user_id>')
def mark_as_completed(file_id, user_id):
    # Actualiza el estado en la base de datos a completado (1)
    cur = mysql.connection.cursor()
    cur.execute("UPDATE files SET estado = 1 WHERE id = %s AND user_id = %s", (file_id, user_id))
    mysql.connection.commit()
    cur.close()

    # Obtén los documentos actualizados del mismo ID de usuario
    cur = mysql.connection.cursor()
    cur.execute("SELECT id, filename, estado FROM files WHERE user_id = %s", (user_id,))
    documents = cur.fetchall()
    cur.close()

    return render_template('/salesEmpArea/uploadedDocuments.jinja', documents=documents, user_id=user_id)


@salesemp.route('/mark_as_incomplete/<int:file_id>/<int:user_id>')
def mark_as_incomplete(file_id, user_id):
    # Actualiza el estado en la base de datos a incompleto (0)
    cur = mysql.connection.cursor()
    cur.execute("UPDATE files SET estado = 0 WHERE id = %s AND user_id = %s", (file_id, user_id))
    mysql.connection.commit()
    cur.close()

    # Obtén los documentos actualizados del mismo ID de usuario
    cur = mysql.connection.cursor()
    cur.execute("SELECT id, filename, estado FROM files WHERE user_id = %s", (user_id,))
    documents = cur.fetchall()
    cur.close()

    return render_template('/salesEmpArea/uploadedDocuments.jinja', documents=documents, user_id=user_id)




#----------------------------------------------------

@salesemp.route('/salesEmpArea/salesHome')   
def salesHome():
    return render_template('salesEmpArea/salesHome.jinja')


# Definimos la función clientsList para la ruta '/salesEmpArea/clientsList'
@salesemp.route('/salesEmpArea/clientsList')
def clientsList():
    cur = mysql.connection.cursor()
    cur.execute("SELECT id, username, fullname, email FROM user WHERE tipousuario = 3 AND areaUsuario = 4")
    users = cur.fetchall()
    cur.close()
    return render_template('salesEmpArea/clientsList.jinja', users=users)

#-----------------------------------------------------------

@salesemp.route('/salesEmpArea/newRequest')
def newRequest():
    cur = mysql.connection.cursor()

    # Ejecuta la consulta para obtener los registros de la tabla machinesorders
    cur.execute("SELECT id_order, clientUser_id, price, type FROM machinesorders")

    # Obtén todos los resultados de la consulta
    orders = cur.fetchall()

    # Cierra el cursor
    cur.close()

    # Pasa los resultados a la plantilla newRequest.jinja y renderízala
    return render_template('salesEmpArea/newRequest.jinja', orders=orders)



@salesemp.route('/salesEmpArea/updateType/<int:id_order>', methods=['POST'])
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

