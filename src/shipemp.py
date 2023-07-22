from flask_mysqldb import MySQL
from flask import render_template, session, redirect, flash
from flask import Blueprint
from flask import request
from flask import Flask
from flask import Flask, render_template, jsonify
import requests
app = Flask(__name__)
mysql = MySQL()
import os

shipemp = Blueprint('shipemp', __name__)

GOOGLE_MAPS_API_KEY = "AIzaSyAJzmmel__k7beEoyd-LhonGRhMrR2mEJE"

#--------------------rutas mantenimiento-----------------------
@shipemp.route('/shipping/orders')
def orders():
    return render_template('/shipping/orders.jinja')


@shipemp.route('/shipping/routes')
def routes():
    return render_template('/shipping/routes.jinja', api_key=GOOGLE_MAPS_API_KEY)