import json
from network import login_manager
from flask import session
from flask_login import UserMixin
import network.logs as log

def init():
	global userlist
	userlist = []

	with open('network/userlist.json','r') as file:
		file_json = json.load(file)
		log.logger.debug(file_json)
		for entry in file_json['users']:
			userlist.append(user(entry['username'],entry['password'],entry['perms']))


@login_manager.user_loader
def load_user(user_id):
	return check_user(user_id)

def check_user(user_id):
	for i in userlist:
		if i.username == user_id:
			return i
	return None

class user(UserMixin):
	def __init__(self, username, passwordhash, perms):
		self.username = username
		self.passwordhash = passwordhash
		self.perms = perms
	@classmethod
	def get(cls,id):
		return cls.user_database.get(id)

	def is_anonymous(self):
		return False

	def is_authenticated(self):
		return True
	
	def is_active(self):
		return True

	def get_id(self):
			try:
				return str(self.id)
			except AttributeError:
				raise NotImplementedError('No `id` attribute - override `get_id`')