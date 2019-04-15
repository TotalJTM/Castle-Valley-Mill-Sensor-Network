from flask import render_template, url_for, flash, redirect, request, session
from network import app, db, bcrypt
from network.forms import LoginForm, DeviceForm, SensorForm
from network.models import User, Device, Sensor, SensorEvent
from flask_login import login_user, current_user, logout_user, login_required
import network.logs as log
import secrets
#import network.nodes as nde

@app.route("/")
@login_required
def home():
    return render_template('layout.html')

#@app.route("/dashboard/")
#@login_required
#def dashboard():
#    log.logger.debug("main display served")
#    log.logger.debug(nodeList)
#    return render_template('dashboard.html',page_data=nde.get_node_json())

@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm(request.form)
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Please check username and password', 'danger')
    return render_template('login.html', title='Login', form=form)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route("/once")
def do_once():
    #hashed_password = bcrypt.generate_password_hash('password').decode('utf-8')
    #user = User(username='testuser', password=hashed_password, perms='reg')
    #db.session.add(user)
    #db.session.commit()
    return 'done'

@app.route("/crash")
def crash():
    Device.create()

@app.route("/config/new/<config_option>", methods=['GET','POST'])
def form_new(config_option):
    if(config_option == 'device'):
        form = DeviceForm(request.form)
        if(request.method == 'POST' and form.validate_on_submit()):
            new_device = Device.create(assigned_id=form.entry_assigned_id.data,title=form.entry_title.data,mill_floor=form.entry_mill_floor.data,battery_type=form.entry_battery_type.data)
            return redirect(url_for('view_devices'))
        return render_template('deviceform.html', form=form)

    if(config_option == 'sensor'):
        form = SensorForm(request.form)
        if(request.method == 'POST' and form.validate_on_submit()):
            Device.new_sensor(passed_id=form.entry_device_id.data,sensor_id=form.entry_assigned_id.data,sensor_title=form.entry_title.data,sensor_type=form.entry_sensor_type.data)
            return redirect(url_for('view_sensors'))
        return render_template('sensorform.html', form=form)

    # if(config_option == 'event'):
        # form = SensorEventForm(request.form)
        # if(request.method == 'POST' and form.validate_on_submit()):
            # element = Device.query.filter_by(assigned_id=form.entry_device_id).first()
            # sensor_event = Sensor(assigned_id=form.entry_assigned_id.data,title=form.entry_title.data,sensor_type=form.entry_sensor_type.data)


@app.route("/config/view/device", methods=['GET'])
def view_devices():
    j = ""
    for i in Device.query.all():
        j+=Device.get_data(i.assigned_id)
        j+="<br/>"
    return j

@app.route("/config/view/sensor", methods=['GET'])
def view_sensors():
    j = ""
    for i in Device.query.all():
        j+=i.assigned_id
        j+="<br/>"
        for q in i.sensors:
            j+=Device.get_sensor_data(i.assigned_id,q.assigned_id,4)
            j+="<br/>"
    return j

@app.route("/server/update", methods=['POST'])
def handle_device():
    message = request.data
    message = message.decode("utf-8")
    message = json.loads(message)
    if message["network_key"] == secrets.DEVICE_KEYS:
        if not Device.query.filter_by(assigned_id=message["id"]).first():
            #log.logger.debug(f"new dev on network {message["id"]}")
            Device.create()
        else:
            Device.new_battery_data(passed_id,bat_data)
            for i in sensor_json:
                check_sensor = False
                for j in Device.query.filter_by(assigned_id=message["id"]).first().sensors:
                    if j.assigned_id == i["id"]:
                        Device.new_sensor_data(passed_id,i["id"],i["data"])
                        check_sensor = True
                if not check_sensor:
                    Device.new_sensor(message["id"],i["id"],i["type"])
                    Device.new_sensor_data(message["id"],i["id"],i["data"])

@app.route("/server/retrieve", methods=['POST'])
def serve_device():
    return ooo