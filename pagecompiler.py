from flask import session
from network import app, db, bcrypt
from network.forms import LoginForm, DeviceForm, SensorForm, DeviceForm
from network.models import User, Device, Sensor, SensorEvent
from flask_login import login_user, current_user, logout_user, login_required
import network.logs as log
import json

def get_header_json():
	data = f'{{"user":{{"user_current":"{current_user.username}","user_permission":"{current_user.perms}"}},"header":{{"masthead_time":"April 5th, 3:15 PM"}}}}'
	return data

def get_full_device_sensor_list():
	comp = []
	for i in Device.query.all():
		dev = []
		for j in i.sensors:
			dev.append(f'{{"sensor_id":"{j.assigned_id}",sensor_title:"{j.title}"}}')
		comp.append(f'"device_id":"{i.assigned_id}",device_title:"{i.title}","sensors":{json.dumps(dev)}')
	return json.dumps(comp)