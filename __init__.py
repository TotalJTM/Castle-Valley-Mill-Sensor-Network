from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
import network.logs as log
import os

basedir = os.path.abspath(os.path.dirname(__file__))
log.logger.debug(basedir)

app = Flask(__name__)
SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'database\\app.db')
tuser = 'sqlite:///' + os.path.join(basedir, 'database\\userdb.db')
tnet = 'sqlite:///' + os.path.join(basedir, 'database\\network.db')
SQLALCHEMY_BINDS = {
    'users': tuser,
    'network': tnet
}
app.config['SECRET_KEY'] = '5791628bb0b13ce0c676dfde280ba245'
#app.config['SQLALCHEMY_DATABASE_URI'] ='sqlite:///userdb.db'
app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_BINDS'] = SQLALCHEMY_BINDS
db = SQLAlchemy(app)
db.create_all()
#db.app = app
log.logger.debug(db)

bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

from network.models import User
log.logger.debug(User.query.all())

#global nodeList
#nodeList = []

#import network.configuration as conf
#nodeList = conf.get_node_config(nodeList)

from network import routes
#users.init()