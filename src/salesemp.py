from flask_mysqldb import MySQL
from flask import render_template, session, redirect, flash
from flask import Blueprint
from flask import request
from flask import Flask
app = Flask(__name__)
mysql = MySQL()
import os

salesemp = Blueprint('salesemp', __name__)



@salesemp.route('/sales/salesHome')   
def salesHome():
    return render_template('/salesEmpArea/salesHome.html')


# Definimos la función clientsList para la ruta '/salesEmpArea/clientsList'
@salesemp.route('/salesEmpArea/clientsList')
def clientsList():
    cur = mysql.connection.cursor()
    cur.execute("SELECT id, username, fullname, email FROM user WHERE tipousuario = 3 AND areaUsuario = 4")
    users = cur.fetchall()
    cur.close()
    return render_template('salesEmpArea/clientsList.html', users=users)



# Configura la carpeta donde se almacenarán los documentos cargados
app.config['UPLOAD_FOLDER'] = 'uploads'

# Asegúrate de que los documentos subidos tengan una extensión válida
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Define la ruta para procesar la solicitud de carga de documentos
@salesemp.route('/upload_document', methods=['POST'])
def upload_document():
    if 'document' not in request.files:
        return redirect(request.url)
    file = request.files['document']
    if file.filename == '':
        return redirect(request.url)
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        # Inserta la información del archivo en la base de datos
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO documents (user_id, filename) VALUES (%s, %s)", (session['user_id'], filename))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('documentsUser'))
    else:
        return "Archivo no válido"

@salesemp.route('/salesEmpArea/viewDocument/<int:document_id>')
def viewDocument(document_id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT filename, filedata FROM documents WHERE id = %s", (document_id,))
    result = cur.fetchone()
    cur.close()
    return send_file(BytesIO(result['filedata']), attachment_filename=result['filename'])


@salesemp.route('/files')
def files():
    cur = mysql.connection.cursor()
    cur.execute("SELECT id, filename FROM files WHERE user_id = %s", (session['user_id'],))
    files = cur.fetchall()
    cur.close()
    return render_template('clientsList.html', files=files)



# Definimos la función sales_list para la ruta '/sales'
@salesemp.route('/sales')
def sales_list():
    return 'Página de ventas'

@salesemp.route('/newRequest')   
def newRequest():
    return render_template('/sales/newRequest.html')
    
@salesemp.route('/salesEmpArea/prospects')   
def prospects():
    return render_template('templates/sales/prospects.html')
    
@salesemp.route('/rents')   
def rents():
    return render_template('/sales/rents.html')

@salesemp.route('/sales/sales')   
def sales():
    return render_template('/sales/sales.html')

