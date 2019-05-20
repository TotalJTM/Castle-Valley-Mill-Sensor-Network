from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, IntegerField, RadioField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from network.models import Device, Sensor, SensorEvent

class LoginForm(FlaskForm):		#flask_wtf login form for login page
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')

class DeviceForm(FlaskForm):	#flask_wtf device registration form to add new devices to db
	entry_assigned_id = StringField('Device ID', validators=[DataRequired()])
	entry_title = StringField('Device Name')
	entry_mill_floor = IntegerField('Floor Code')
	entry_battery_type = IntegerField('Battery Type Code', validators=[DataRequired()])

	def validate_entry_assigned_id(self, entry_assigned_id):							#custom validators must be the same name as assigned above
		val = Device.query.filter_by(assigned_id=entry_assigned_id.data).first()		#check for first entry with entered id (only unique field in model)
		if(val is not None):															#throw error if id already exists
			raise ValidationError('Device already exists with that ID')

class SensorForm(FlaskForm):	#flask_wtf sensor registration form to add new sensors to existing device
	entry_assigned_id = StringField('Sensor ID', validators=[DataRequired()])
	entry_title = StringField('Sensor Name')
	entry_sensor_type = StringField('Sensor Type', validators=[DataRequired()])
	entry_parse_ind = StringField('Parse Position')
	entry_sensor_modifier = StringField('Modifier Value')
	entry_sensor_modifier_sign = RadioField('Modifier Operation', choices=[('add','+'),('sub','-'),('mult','X'),('div','/'),('mod','%'),('none','nothing')], default='none')

class SensorEventForm(FlaskForm):	#flask_wtf sensor event registration form to create new sensor event for provided sensor
	entry_device_id = StringField('Device ID', validators=[DataRequired()])
	entry_title = StringField('Event Name')
	entry_threshold_val = StringField('Threshold Value', validators=[DataRequired()])
	entry_threshold_comparator = RadioField('Modifier Operation', choices=[('eq','Equal To'),('gre','Greater Than'),('les','Less Than')])
	entry_on_event = StringField('Triggers', validators=[DataRequired()])
