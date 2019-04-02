from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, IntegerField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from network.models import Device, Sensor, SensorEvent

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')

class DeviceForm(FlaskForm):
	entry_assigned_id = StringField('Device ID', validators=[DataRequired()])
	entry_title = StringField('Device Name')
	entry_mill_floor = IntegerField('Floor Code')
	entry_battery_type = IntegerField('Battery Type Code', validators=[DataRequired()])

	def validate_entry_assigned_id(self, entry_assigned_id):							#custom validators must be the same name as assigned above
		val = Device.query.filter_by(assigned_id=entry_assigned_id.data).first()		#check for first entry with entered id (only unique field in model)
		if(val is not None):															#throw error if id already exists
			raise ValidationError('Device already exists with that ID')
