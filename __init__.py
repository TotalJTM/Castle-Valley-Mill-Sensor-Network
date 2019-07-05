from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_socketio import SocketIO
import network.logs as log
import time
from threading import Thread, active_count
import os

basedir = os.path.abspath(os.path.dirname(__file__))				#get directory location

app = Flask(__name__)				#initialize our flask instance
socketio = SocketIO(app)			#initialize our socketio instance

SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'database\\app.db')
tuser = 'sqlite:///' + os.path.join(basedir, 'database\\userdb.db')
tnet = 'sqlite:///' + os.path.join(basedir, 'database\\network.db')
tcheck = 'sqlite:///' + os.path.join(basedir, 'database\\checklist.db')
SQLALCHEMY_BINDS = {		#create seperate database binds, allows multiple databases called 'users' and 'network'
    'users': tuser,
    'network': tnet,
    'checklist': tcheck
}
app.config['SECRET_KEY'] = '5791628bb0b13ce0c676dfde280ba245'		#random key for flask security
app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI		#configure database uri
app.config['SQLALCHEMY_BINDS'] = SQLALCHEMY_BINDS					#configure database binds
db = SQLAlchemy(app)									#initialize sqlalchemy
db.create_all()											#create database and build tables

bcrypt = Bcrypt(app)									#initialize bcrypt for password hashing
login_manager = LoginManager(app)						#initialize login manager to handle user permissions
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

global active_alerts		#make global list for storing alert messages
active_alerts = []
from network import checklist
from network import routes

def update_client():							#create a thread to update the header of interface
	while active_count() > 0:					#if active threads
		routes.update_header(active_alerts)		#call update_header function to push new updates to interface
		time.sleep(7)							#sleep thread for x seconds so we dont spam user

content_delivery = Thread(target=update_client)	#make a new thread for update_client method
content_delivery.daemon = True					#allow the thread to be terminated
content_delivery.start()						#start updating interface header