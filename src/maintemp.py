from flask_mysqldb import MySQL
from flask import render_template, session, redirect, flash
from flask import Blueprint
from flask import request
from flask import Flask
app = Flask(__name__)
mysql = MySQL()
import os

maintemp = Blueprint('maintemp', __name__)

#--------------------rutas mantenimiento-----------------------
@maintemp.route('/mantHistory')
def mantHistory():
    return render_template('maintenance/mantHistory.html')

@maintemp.route('/mantMachines')   
def mantMachines():
    return render_template('/maintenance/mantMachines.html')
    
@maintemp.route('/mantManteinance')   
def mantManteinance():
    return render_template('/maintenance/mantManteinance.html')
    
@maintemp.route('/mantReports')   
def mantReports():
    return render_template('/maintenance/mantReports.html')

@maintemp.route('/maintenance/mantHome')   
def mantHome():
    return render_template('/maintenance/mantHome.html')