from flask_mysqldb import MySQL
from flask import render_template, session, redirect, flash
from flask_wtf.csrf import CSRFProtect
from flask import Blueprint
from flask import request
from flask import Flask
from flask import url_for
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


#------------------------------------------------------------------------

@salesemp.route('/salesEmpArea/salesList')
def salesList():
    cur = mysql.connection.cursor()
    
    return render_template('/salesEmpArea/salesList.jinja')


@salesemp.route('/salesEmpArea/rentsList')   
def rentsList():
    cur = mysql.connection.cursor()
    
    return render_template('/salesEmpArea/rentsList.jinja')

#------------------------------------------------------------------------
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
    
    return render_template('/salesEmpArea/newRequest.jinja')


#-----------------------------------------------------------

    
@salesemp.route('/salesEmpArea/prospects')   
def prospects():
    return render_template('salesEmpArea/prospects.jinja')
    




