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

	def __init__(self,assigned_id,title,mill_floor,battery_type):
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
		element = Device.query.filter_by(assigned_id=passed_id).first()
		db.session.delete(element)
		db.session.commit()

	def change_title(passed_device_id, new_title):
		element = Device.query.filter_by(assigned_id=passed_id).first()
		element.title = new_title
		db.session.commit()

	def get_data(passed_id):
		element = Device.query.filter_by(assigned_id=passed_id).first()
		display_data = []
		counter = 0
		for i in reversed(j.battery_data):
			if counter < nDatapoints:
				display_data.append(f'{{"data":{i.data},"timestamp":{i.timestamp}}}')
		generate_json = f'{{"assigned_id":{element.assigned_id},"title":{element.title},"mill_floor":{element.mill_floor},"battery_type":{element.battery_type},"battery_data":{element.battery_data[:10]},"sensors":{element.sensors}}}'
		return generate_json

	def new_sensor(passed_id,sensor_id,sensor_type,sensor_title=None):
		element = Device.query.filter_by(assigned_id=passed_id).first()
		new_sensor = Sensor(assigned_id=sensor_id,title=sensor_title,sensor_type=sensor_type)
		element.sensors.append(new_sensor)
		db.session.commit()

	def remove_sensor(passed_id,sensor_id):
		element = Device.query.filter_by(assigned_id=passed_id).first()
		db.session.delete(element)
		db.session.commit()

	def get_sensor_data(passed_id,sensor_id,nDatapoints):
		element = Device.query.filter_by(assigned_id=passed_id).first()
		for j in element.sensors:
			if j.assigned_id == sensor_id:
				display_data = []
				counter = 0
				for i in reversed(j.sensor_data):
					if counter < nDatapoints:
						display_data.append(f'{{"data":{i.data},"timestamp":{i.timestamp}}}')
				generate_json = f'{{"assigned_id":{j.assigned_id},"title":{j.title},"sensor_type":{j.sensor_type},"sensor_data":{display_data}}}'		
				return generate_json
		return 'err-nosensor'

	def new_sensor_data(passed_id,sensor_id,new_data):
		data_entry = SensorData(data=new_data)
		element = Device.query.filter_by(assigned_id=passed_id).first()
		for j in element.sensors:
			if j.assigned_id == sensor_id:
				j.sensor_data.append(data_entry)
		db.session.commit()

	def new_battery_data(passed_id,new_data):
		data_entry = BatteryData(data=new_data)
		element = Device.query.filter_by(assigned_id=passed_id).first()
		element.battery_data.append(data_entry)
		db.session.commit()


class BatteryData(db.Model):
	__bind_key__ = 'network'
	id = db.Column(db.Integer, primary_key=True)
	data = db.Column(db.Integer, unique=False, nullable=False)
	timestamp = db.Column(db.DateTime, default=datetime.utcnow)
	parent_id = db.Column(db.Integer, db.ForeignKey('device.id'), nullable=False)

class Sensor(db.Model):
	__bind_key__ = 'network'
	id = db.Column(db.Integer, primary_key=True)
	assigned_id = db.Column(db.Integer, unique=False, nullable=False)
	title = db.Column(db.String(30), unique=False, nullable=True)
	sensor_type = db.Column(db.String(12), unique=False, nullable=False)
	parse_ind = db.Column(db.String(10), unique=False, nullable=True)
	sensor_data = db.relationship('SensorData', backref='sensor', lazy=True)
	events = db.relationship('SensorEvent', backref='sensor', lazy=True)
	parent_id = db.Column(db.Integer, db.ForeignKey('device.id'), nullable=False)

class SensorData(db.Model):
	__bind_key__ = 'network'
	id = db.Column(db.Integer, primary_key=True)
	data = db.Column(db.String(20), unique=False, nullable=False)
	timestamp = db.Column(db.DateTime, default=datetime.utcnow)
	parent_id = db.Column(db.Integer, db.ForeignKey('sensor.id'), nullable=False)

class SensorEvent(db.Model):
	__bind_key__ = 'network'
	id = db.Column(db.Integer, primary_key=True)
	title = db.Column(db.String(20), unique=False, nullable=True)
	threshold_val = db.Column(db.String(20), unique=False, nullable=False)
	threshold_comparator = db.Column(db.String(2), unique=False, nullable=False)
	parent_id = db.Column(db.Integer, db.ForeignKey('sensor.id'), nullable=False)