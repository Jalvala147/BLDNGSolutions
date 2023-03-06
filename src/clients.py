from flask_mysqldb import MySQL
from flask import render_template, session, redirect, flash
from flask import Blueprint
from flask import request
from flask import Flask
app = Flask(__name__)
mysql = MySQL()

clients = Blueprint('clients', __name__)

#--------------------rutas clientes-----------------------
@clients.route('/clientsHome')
def clientsHome():
    return render_template('/clientuser/clientsHome.html')

@clients.route('/documentsuser')   
def documentsuser():
    return render_template('/clientuser/documentsuser.html')
    
@clients.route('/information')   
def information():
    return render_template('/clientuser/information.html')
    
@clients.route('/payments')   
def payments():
    return render_template('/clientuser/payments.html')
    
@clients.route('/statusprogress')   
def statusprogress():
    return render_template('/clientuser/statusprogress.html')