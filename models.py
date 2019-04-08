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
		generate_json = f'{{"assigned_id":{element.assigned_id},"title":{element.title},"mill_floor":{element.mill_floor},"battery_type":{element.battery_type},"battery_data":{element.battery_data[:10]},"sensors":{element.sensors}}}'
		return generate_json

	def new_sensor(passed_id,sensor_id,sensor_title=None,sensor_type):
		element = Device.query.filter_by(assigned_id=passed_id).first()
		new_sensor = Sensor(assigned_id=sensor_id,title=sensor_title,sensor_type=sensor_type)
		element.sensors.append(new_sensor)
		db.session.add(obj)
		db.session.commit()

	def remove_sensor(passed_id,sensor_id):
		element = Device.query.filter_by(assigned_id=passed_id).first()
		db.session.delete(element)
		db.session.commit()

	def get_sensor_data(passed_id,sensor_id,nDatapoints):
		element = Device.query.filter_by(assigned_id=passed_id).first()
		for j in element.sensors:
			if j.assigned_id == sensor_id:
				generate_json = f'{{"assigned_id":{j.assigned_id},"title":{j.title},"sensor_data":{j.sensor_data[:nDatapoints]}}}'		

		return generate_json
		db.session.commit()

	def add_sensor_data(passed_id,sensor_id,data):
		data_entry = SensorData.create(data)
		element = Device.query.filter_by(assigned_id=passed_id).first()
		for j in element.sensors:
			if j.assigned_id == sensor_id:
				j.sensor_data.append(data_entry)
		db.session.add(obj)
		db.session.commit()

	def add_battery_data(passed_id,sensor_id,data):
		data_entry = SensorData.create()
		element = Device.query.filter_by(assigned_id=passed_id).first()
		for j in element.battery_data:
			if j.assigned_id == sensor_id:
				j.battery_data.append(data_entry)


class BatteryData(db.Model):
	__bind_key__ = 'network'
	id = db.Column(db.Integer, primary_key=True)
	data = db.Column(db.Integer, unique=False, nullable=False)
	timestamp = db.Column(db.DateTime, default=datetime.utcnow)
	parent_id = db.Column(db.Integer, db.ForeignKey('device.id'), nullable=False)

	def __init__(self,data,parent_id):
		self.data =data
		self.parent_id = parent_id

@classmethod
	def create(cls, **kw):
		obj = cls(**kw)
		db.session.add(obj)
		db.session.commit()


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

	def __init__(self,assigned_id,title=None,sensor_type):
		self.assigned_id = assigned_id
		self.title = title
		self.sensor_type = sensor_type
		
	@classmethod
	def create(cls, **kw):
		obj = cls(**kw)
		db.session.add(obj)
		db.session.commit()


class SensorData(db.Model):
	__bind_key__ = 'network'
	id = db.Column(db.Integer, primary_key=True)
	data = db.Column(db.String(20), unique=False, nullable=False)
	timestamp = db.Column(db.DateTime, default=datetime.utcnow)
	parent_id = db.Column(db.Integer, db.ForeignKey('sensor.id'), nullable=False)

	def __init__(self,new_data):
		self.data=new_data

	@classmethod
	def create(cls, **kw):
		obj = cls(**kw)
		db.session.add(obj)
		db.session.commit()

class SensorEvent(db.Model):
	__bind_key__ = 'network'
	id = db.Column(db.Integer, primary_key=True)
	title = db.Column(db.String(20), unique=False, nullable=True)
	threshold_val = db.Column(db.String(20), unique=False, nullable=False)
	threshold_comparator = db.Column(db.String(2), unique=False, nullable=False)
	parent_id = db.Column(db.Integer, db.ForeignKey('sensor.id'), nullable=False)
	


	@classmethod
	def create(cls, **kw):
		obj = cls(**kw)
		db.session.add(obj)
		db.session.commit()
