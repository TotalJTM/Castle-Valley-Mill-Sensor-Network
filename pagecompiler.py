from flask import session
from network import app, db, bcrypt
from network.forms import LoginForm, DeviceForm, SensorForm, DeviceForm
from network.models import User, Device, Sensor, SensorEvent
from flask_login import login_user, current_user, logout_user, login_required
import network.logs as log
from datetime import datetime
import json

def get_header_json():
	time = datetime.now().strftime("%b %d, %I:%M")
	data = f'{{"user":{{"user_current":"{current_user.username}","user_permission":"{current_user.perms}"}},"header":{{"masthead_time":"{time}"}}}}'
	return data

def get_full_device_sensor_list():
	comp = []
	for i in Device.query.all():
		dev = []
		for j in i.sensors:
			dev.append(f'{{"sensor_id":"{j.assigned_id}",sensor_title:"{j.title}"}}')
		comp.append(f'"device_id":"{i.assigned_id}",device_title:"{i.title}","sensors":{json.dumps(dev)}')
	return comp

def get_full_json(header=True,dev_sens_event=True,bat_data=True,sens_data=True,nDatapoints=1):
	data = "{"
	if header:
		time = datetime.now().strftime("%b %d, %I:%M")
		data += f'"user":{{"user_current":"{current_user.username}","user_permission":"{current_user.perms}"}},"header":{{"masthead_time":"{time}"}}'
		if(dev_sens_event == True or bat_data == True or sens_data == True):
			data += ","
	if dev_sens_event:
		data += '"devices":['
		dev_count = 0
		full_dev_list = Device.query.all()
		for i in full_dev_list:
			batdata = "["
			sensors = "["
			if bat_data:
				counter = 0
				for t in reversed(i.battery_data):
					if counter < nDatapoints:
						batdata += f'{{"data":"{t.data}","timestamp":"{t.timestamp}""}}'
						counter = counter+1
						if counter != nDatapoints:
							batdata += ","
			sens_count = 0
			for j in i.sensors:
				sensevent = "["
				sensdata = "["
				counter = 0
				for k in j.events:
					sensevent += f'{{"id":"{k.id}","title":"{k.title}"}}'
					counter = counter+1
					if counter != len(j.events):
						sensevent += ","
				if sens_data:
					counter = 0
					for t in reversed(j.sensor_data):
						if counter < nDatapoints:
							sensdata += f'{{"data":"{t.data}","timestamp":"{t.timestamp}""}}'
							counter = counter+1
							if counter != nDatapoints:
								sensdata += ","
				sensors += f'{{"assigned_id":"{j.assigned_id}","title":"{j.title}","sensor_type":"{j.sensor_type}","sensor_data":{sensdata}],"events":{sensevent}]}}'
				sens_count = sens_count + 1
				if sens_count != len(i.sensors):
					sensors += ","
			data += f'{{"assigned_id":"{i.assigned_id}","title":"{i.title}","mill_floor":{i.mill_floor},"battery_type":{i.battery_type},"battery_data":{batdata}],"sensors":{sensors}]}}'
			dev_count = dev_count + 1
			if dev_count != len(full_dev_list):
				data += ","
	data += "]}"
	return data