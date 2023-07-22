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
@maintemp.route('/maintenance/mantHistory')
def mantHistory():
    return render_template('maintenance/mantHistory.jinja')

@maintemp.route('/maintenance/mantMachines')   
def mantMachines():
    return render_template('/maintenance/mantMachines.jinja')
    
@maintemp.route('/maintenance/mantReports')   
def mantReports():
    return render_template('/maintenance/mantReports.jinja')

@maintemp.route('/maintenance/mantHome')   
def mantHome():
    return render_template('/maintenance/mantHome.jinja')

@maintemp.route('/maintenance/mantMaintenance')
def mantMaintenance():
    return render_template('/maintenance/mantMaintenance.jinja')