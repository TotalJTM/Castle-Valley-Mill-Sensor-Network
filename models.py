from datetime import datetime
from network import db, login_manager
from flask_login import UserMixin
import network.logs as log
import json


@login_manager.user_loader
def load_user(user_id):
	if user_id:
		return User.query.get(int(user_id))

class User(db.Model, UserMixin):
	__bind_key__ = 'users'
	id = db.Column(db.Integer, primary_key=True)
	username = db.Column(db.String(20), unique=True, nullable=False)
	password = db.Column(db.String(60), nullable=False)
	perms = db.Column(db.String(10), unique=False, nullable=False)

	def __repr__(self):
		return f"User('{self.username}')"

	def get_user_data(username):
		element = Device.query.filter_by(username=username).first()
		generate_json = f'{{"user_current":{element.username},"user_permission":{element.perms}}}'
		return generate_json

class Device(db.Model):
	__bind_key__ = 'network'
	id = db.Column(db.Integer, primary_key=True)
	assigned_id = db.Column(db.String(10), unique=True, nullable=False)
	title = db.Column(db.String(30), unique=False, nullable=True)
	mill_floor = db.Column(db.Integer, unique=False, nullable=True)
	battery_type = db.Column(db.Integer, unique=False, nullable=False)
	battery_data = db.relationship('BatteryData', backref='device', lazy=True)
	sensors = db.relationship('Sensor', backref='device', lazy=False)

	def __init__(self,assigned_id,battery_type,title=None,mill_floor=None):
		self.assigned_id = assigned_id
		self.title = title
		self.mill_floor = mill_floor
		self.battery_type = battery_type

	@classmethod
	def create(cls, **kw):
		obj = cls(**kw)
		db.session.add(obj)
		db.session.commit()

	def remove(passed_device_id):
		element = Device.query.filter_by(assigned_id=passed_device_id).first()
		for j in element.battery_data:
				db.session.delete(j)
		for sens in element.sensors:
			for j in sens.sensor_data:
				db.session.delete(j)
			for j in sens.events:
				db.session.delete(j)
			db.session.delete(sens)
		db.session.delete(element)
		db.session.commit()

	def change_title(passed_device_id, new_title):
		element = Device.query.filter_by(assigned_id=passed_device_id).first()
		element.title = new_title
		db.session.commit()

	def get_data(passed_id,nDatapoints=5):
		element = Device.query.filter_by(assigned_id=passed_id).first()
		display_data = ""
		counter = 0
		for i in reversed(element.battery_data):
			if counter < nDatapoints:
				display_data +=(f'{{"data":{i.data},"timestamp":{i.timestamp}}}')
				if counter != nDatapoints-1:
							display_data += ","
				counter = counter+1
		sensor_data = ""
		for i in range(0,len(element.sensors)):
					sensor_data += f'{{"title":"{element.sensors[i].title}","assigned_id":{element.sensors[i].assigned_id}}}'
					if i != len(element.sensors)-1:
							sensor_data += ","
		generate_json = f'{{"assigned_id":{element.assigned_id},"title":"{element.title}","mill_floor":{element.mill_floor},"battery_type":{element.battery_type},"battery_data":[{display_data}],"sensors":[{sensor_data}]}}'
		return generate_json

	def new_sensor(passed_id,sensor_id,sensor_type,sensor_title=None,sensor_modifier_sign="none"):
		element = Device.query.filter_by(assigned_id=str(passed_id)).first()
		if element:
			new_sensor = Sensor(assigned_id=str(sensor_id),title=sensor_title,sensor_type=str(sensor_type))
			element.sensors.append(new_sensor)
			db.session.commit()
		else:
			return 'err-nodevice'

	def remove_sensor(passed_id,sensor_id):
		element = Device.query.filter_by(assigned_id=passed_id).first()
		for i in element.sensors:
			if i.assigned_id == int(sensor_id):
				for j in i.events:
					db.session.delete(j)
				for j in i.sensor_data:
					db.session.delete(j)
				db.session.delete(i)
		db.session.commit()

	def get_sensor_data(passed_id,sensor_id,nDatapoints):
		element = Device.query.filter_by(assigned_id=passed_id).first()
		for j in element.sensors:
			if j.assigned_id == int(sensor_id):
				display_data = ""
				event_data = ""
				counter = 0
				for i in reversed(j.sensor_data):
					if counter < nDatapoints and len(j.sensor_data) != 0:
						display_data += (f'{{"data":"{i.data}","timestamp":{i.timestamp}}}')
						if counter != nDatapoints-1:
							display_data += ","
						counter = counter+1
				for i in range(0,len(j.events)):
					event_data += f'{{"id":"{j.events[i].id}","title":"{j.events[i].title}","threshold_val":"{j.events[i].threshold_val}","threshold_comparator":"{j.events[i].threshold_comparator}","on_event":"{j.events[i].on_event}"}}'
					if i != len(j.events)-1 and len(element.sensors) != 0:
							event_data += ","
				log.logger.debug(len(element.sensors))
				sensor_modifier_l = j.sensor_modifier 
				if not sensor_modifier_l:
					sensor_modifier_l = f'"{j.sensor_modifier}"'
				log.logger.debug(j.sensor_modifier)
				generate_json = f'{{"assigned_id":"{j.assigned_id}","title":"{j.title}","sensor_type":"{j.sensor_type}","sensor_data":[{display_data}],"parse_ind":"{j.parse_ind}","sensor_modifier":{sensor_modifier_l},"sensor_modifier_sign":"{j.sensor_modifier_sign}","events":[{event_data}]}}'		
				return generate_json
		return 'err-nosensor'

	def modify_sensor_data(data, sensor):
		if sensor.sensor_modifier_sign == "none":
			return data
		elif sensor.sensor_modifier_sign == "sub":
			return data-sensor.sensor_modifier
		elif sensor.sensor_modifier_sign == "add":
			return data+sensor.sensor_modifier
		elif sensor.sensor_modifier_sign == "mult":
			return data*sensor.sensor_modifier
		elif sensor.sensor_modifier_sign == "div":
			return data/sensor.sensor_modifier
		elif sensor.sensor_modifier_sign == "mod":
			return data%sensor.sensor_modifier
		else:
			return data

	def new_sensor_data(passed_id,sensor_id,new_data):
		element = Device.query.filter_by(assigned_id=passed_id).first()
		for j in element.sensors:
			if j.assigned_id == sensor_id:
				new_data = new_data.strip('\n')
				new_data = new_data.strip('\r')
				data = Device.modify_sensor_data(new_data,j)
				log.logger.debug(data)
				data_entry = SensorData(data=data)
				j.sensor_data.append(data_entry)
		db.session.commit()

	def new_battery_data(passed_id,new_data):
		data_entry = BatteryData(data=new_data)
		element = Device.query.filter_by(assigned_id=passed_id).first()
		element.battery_data.append(data_entry)
		db.session.commit()

	def new_sensor_event(passed_id,sensor_id,threshold_val,threshold_comparator,on_event,title=""):
		element = Device.query.filter_by(assigned_id=str(passed_id)).first()
		for i in element.sensors:
			log.logger.debug(f"i.assigned_id")
			if i.assigned_id == int(sensor_id):
				event = SensorEvent(threshold_val=threshold_val,threshold_comparator=threshold_comparator,on_event=on_event,title=title)
				i.events.append(event)
		db.session.commit()

	def remove_sensor_event(passed_id,sensor_id,database_event_id):
		element = Device.query.filter_by(assigned_id=passed_id).first()
		for i in element.sensors:
			if i.assigned_id == int(sensor_id):
				for j in i.events:
					log.logger.debug(f"{j.id} {database_event_id}")
					if j.id == int(database_event_id):
						log.logger.debug("killed event")
						db.session.delete(j)
		db.session.commit()

class BatteryData(db.Model):
	__bind_key__ = 'network'
	id = db.Column(db.Integer, primary_key=True)
	data = db.Column(db.Float, unique=False, nullable=False)
	timestamp = db.Column(db.DateTime, default=datetime.now)
	parent_id = db.Column(db.Integer, db.ForeignKey('device.id'), nullable=False)

class Sensor(db.Model):
	__bind_key__ = 'network'
	id = db.Column(db.Integer, primary_key=True)
	assigned_id = db.Column(db.Integer, unique=False, nullable=False)
	title = db.Column(db.String(30), unique=False, nullable=True)
	sensor_type = db.Column(db.String(12), unique=False, nullable=False)
	parse_ind = db.Column(db.String(10), unique=False, nullable=True)
	sensor_data = db.relationship('SensorData', backref='sensor', lazy=True)
	sensor_modifier = db.Column(db.Float, unique=False, nullable=True)
	sensor_modifier_sign = db.Column(db.String(6), unique=False, nullable=True)
	events = db.relationship('SensorEvent', backref='sensor', lazy=True)
	parent_id = db.Column(db.Integer, db.ForeignKey('device.id'), nullable=False)

class SensorData(db.Model):
	__bind_key__ = 'network'
	id = db.Column(db.Integer, primary_key=True)
	data = db.Column(db.String(20), unique=False, nullable=False)
	timestamp = db.Column(db.DateTime, default=datetime.now)
	parent_id = db.Column(db.Integer, db.ForeignKey('sensor.id'), nullable=False)

class SensorEvent(db.Model):
	__bind_key__ = 'network'
	id = db.Column(db.Integer, primary_key=True)
	title = db.Column(db.String(20), unique=False, nullable=True)
	threshold_val = db.Column(db.String(20), unique=False, nullable=False)
	threshold_comparator = db.Column(db.String(2), unique=False, nullable=False)
	on_event = db.Column(db.String(20), unique=False, nullable=False)
	parent_id = db.Column(db.Integer, db.ForeignKey('sensor.id'), nullable=False)