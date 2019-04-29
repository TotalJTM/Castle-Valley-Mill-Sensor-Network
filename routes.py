from flask import render_template, url_for, flash, redirect, request, session
from flask_socketio import SocketIO
from network import app, db, bcrypt, socketio
from network.forms import LoginForm, DeviceForm, SensorForm, DeviceForm, SensorEventForm
from network.models import User, Device, Sensor, SensorEvent
from flask_login import login_user, current_user, logout_user, login_required
import network.logs as log
from network.pagecompiler import get_header_json, get_full_json, get_floor_json
import json
from network.serversecrets import DEVICE_KEY

@app.route("/")
@login_required
def home():
    data = get_full_json()
    data = json.loads(data)
    log.logger.debug(data)
    return render_template('website.html', data=data)

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
            session['username'] = user.username
            session['perms'] = user.perms
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

@login_required
@app.route("/config/new/<config_option>/<dev_num>", methods=['GET', 'POST'])
def form_new(config_option,dev_num):
    if(config_option == 'device'):
        form = DeviceForm(request.form)
        if(request.method == 'POST' and form.validate_on_submit()):
            new_device = Device.create(assigned_id=form.entry_assigned_id.data,title=form.entry_title.data,mill_floor=form.entry_mill_floor.data,battery_type=form.entry_battery_type.data)
            socketio.emit('reload', True)
            return '<script>window.close()</script>'
        return render_template('deviceform.html', form=form)

    if(config_option == 'sensor'):
        form = SensorForm(request.form)
        if(request.method == 'POST' and form.validate_on_submit()):
            Device.new_sensor(dev_num,sensor_id=form.entry_assigned_id.data,sensor_title=form.entry_title.data,sensor_type=form.entry_sensor_type.data)
            socketio.emit('reload', True)
            return '<script>window.close()</script>'
        return render_template('sensorform.html', form=form)

@login_required
@app.route("/config/view/sensorevent/<address>", methods=['GET', 'POST'])
def view_events(address):
    parse_address = address.split('-')
    data = Device.get_sensor_data(parse_address[0],parse_address[1],0)
    data = json.loads(data)
    data = data["events"]
    log.logger.debug(data)
    return render_template('eventlist.html', data=data, devaddr=address)

@login_required
@app.route("/config/edit/<config_option>/<dev_num>", methods=['GET', 'POST'])
def form_edit(config_option,dev_num):
    if config_option == 'device':
        form = DeviceForm(request.form)
        element = Device.query.filter_by(assigned_id=dev_num).first()
        if(request.method == 'POST'):
            element.assigned_id = form.entry_assigned_id.data
            element.title = form.entry_title.data
            element.mill_floor = form.entry_mill_floor.data
            element.battery_type = form.entry_battery_type.data
            db.session.commit()
            socketio.emit('reload', True)
            return '<script>window.close()</script>'
        form.entry_assigned_id.data = element.assigned_id
        form.entry_title.data = element.title
        form.entry_mill_floor.data = element.mill_floor
        form.entry_battery_type.data = element.battery_type
        return render_template('deviceform.html', form=form)

    if config_option == 'sensor':
        form = SensorForm(request.form)
        dev_num_parse = dev_num.split('-')
        element = Device.query.filter_by(assigned_id=dev_num_parse[0]).first()
        for i in element.sensors:
            if i.assigned_id == int(dev_num_parse[1]):
                if(request.method == 'POST'):
                    i.assigned_id = form.entry_assigned_id.data
                    i.title = form.entry_title.data
                    i.sensor_type = form.entry_sensor_type.data
                    i.parse_ind = form.entry_parse_ind.data
                    if form.entry_sensor_modifier.data != "":
                        i.sensor_modifier = form.entry_sensor_modifier.data
                    i.sensor_modifier_sign = form.entry_sensor_modifier_sign.data
                    db.session.commit()
                    log.logger.debug(i.title)
                    log.logger.debug("done")
                    socketio.emit('reload', True)
                    return '<script>window.close()</script>'
                else:
                    form.entry_assigned_id.data = i.assigned_id
                    form.entry_title.data = i.title
                    form.entry_sensor_type.data = i.sensor_type
                    form.entry_parse_ind.data = i.parse_ind
                    form.entry_sensor_modifier.data = i.sensor_modifier
                    form.entry_sensor_modifier_sign.data = i.sensor_modifier_sign
                    return render_template('sensorform.html', form=form)

    if config_option == 'sensor_event':
        form = SensorEventForm(request.form)
        log.logger.debug(dev_num)
        dev_num_parse = dev_num.split('-')
        log.logger.debug(dev_num_parse)
        element = Device.query.filter_by(assigned_id=str(dev_num_parse[0])).first()
        for i in element.sensors:
            if i.assigned_id == int(dev_num_parse[1]):
                for j in i.events:
                    if j.id == int(dev_num_parse[2]):
                        if(request.method == 'POST'):
                            #j.id.data = form.entry_id.data
                            j.title = form.entry_title.data
                            j.threshold_val = form.entry_threshold_val.data
                            j.threshold_comparator = form.entry_threshold_comparator.data
                            j.on_event = form.entry_on_event.data
                            db.session.commit()
                            socketio.emit('reload', True)
                            return '<script>window.close()</script>'
                        form.entry_title.data = j.title
                        form.entry_threshold_val.data = j.threshold_val
                        form.entry_threshold_comparator.data = j.threshold_comparator
                        form.entry_on_event.data = j.on_event
                    return render_template('eventform.html', form=form)

        return "no sensor"
    return "not valid address"

@socketio.on('handle_config')
def handle_config(json_data):
    id_name = json_data['id']
    id_name = id_name.split('-')
    action = json_data['action']
    log.logger.debug(id_name)
    if action == "remove":
        if id_name[1]:
            Device.remove_sensor(id_name[0],id_name[1])
            socketio.emit('reload', True)
        else:
            Device.remove(id_name[0])
            socketio.emit('reload', True)
    if str(action) == "removeevent":
        log.logger.debug(action)
        Device.remove_sensor_event(id_name[0],id_name[1],id_name[2])
        socketio.emit('reload', True)

#@app.route("/config/remove/<config_option>", methods=['GET'])
#def form_remove(config_option):
#    if(config_option == 'device'):
#        form = DeviceForm2(request.form)
#        if(request.method == 'GET' and form.validate_on_submit()):
#            remove_device = Device.remove(assigned_id=form.entry_assigned_id.data,title=form.entry_title.data,mill_floor=form.entry_mill_floor.data,battery_type=form.entry_battery_type.data)
#            return redirect(url_for('view/devices'))
#        return render_template('deviceform2.html', form=form)

@login_required
@app.route("/config/event/new/<config_option>/<address>", methods=['GET', 'POST'])
def form_event(config_option,address):
    parse_address = address.split('-')
    log.logger.debug(parse_address)
    if config_option == 'sensorevent':
        form = SensorEventForm(request.form)
        if(request.method == 'POST'):
            Device.new_sensor_event(passed_id=str(parse_address[0]),sensor_id=str(parse_address[1]),threshold_val=form.entry_threshold_val.data,threshold_comparator=form.entry_threshold_comparator.data,on_event=form.entry_on_event.data,title=form.entry_title.data)
            d = Device.get_sensor_data(passed_id=str(parse_address[0]),sensor_id=str(parse_address[1]),nDatapoints=1)
            log.logger.debug(f'data {d} {parse_address[0]} {parse_address[1]}')
            socketio.emit('reload', True)
            return '<script>window.close()</script>'
        return render_template('eventform.html', form=form)
    return "not valid address"


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
    log.logger.debug(message)
    if message["network_key"] == DEVICE_KEY:
        if not Device.query.filter_by(assigned_id=message["id"]).first():
            #log.logger.debug(f"new dev on network {message["id"]}")
            Device.create(assigned_id=message["id"],battery_type=message["battery_type"])
            Device.new_battery_data(passed_id=message["id"],new_data=message["battery_level"])
            for sensor in message["sensors"]:
                Device.new_sensor(passed_id=message["id"],sensor_id=sensor["id"],sensor_type=sensor["type"])
                Device.new_sensor_data(passed_id=message["id"],sensor_id=sensor["id"],new_data=sensor["data"])
        else:
            Device.new_battery_data(passed_id=message["id"],new_data=message["battery_level"])
            for sensor in message["sensors"]:
                check_sensor = False
                for j in Device.query.filter_by(assigned_id=message["id"]).first().sensors:
                    if j.assigned_id == sensor["id"]:
                        Device.new_sensor_data(passed_id=message["id"],sensor_id=sensor["id"],new_data=sensor["data"])
                        check_sensor = True
                if not check_sensor:
                    Device.new_sensor(passed_id=message["id"],sensor_id=sensor["id"],sensor_type=sensor["type"])
                    Device.new_sensor_data(passed_id=message["id"],sensor_id=sensor["id"],new_data=sensor["data"])
    return 'done'

@app.route("/server/retrieve", methods=['POST'])
def serve_device():
    return ooo

@app.route("/floor/first", methods=["GET"])
def serve_floor_first():
    data = get_floor_json(1)
    data = json.loads(data)
    return render_template('website.html', data=data)

@app.route("/floor/second", methods=["GET"])
def serve_floor_second():
    data = get_floor_json(2)
    data = json.loads(data)
    return render_template('website.html', data=data)

@app.route("/floor/third", methods=["GET"])
def serve_floor_third():
    data = get_floor_json(3)
    data = json.loads(data)
    return render_template('website.html', data=data)

@app.route("/floor/basement", methods=["GET"])
def serve_floor_basement():
    data = get_floor_json(0)
    data = json.loads(data)
    return render_template('website.html', data=data)

@login_required
@app.route("/config", methods=["GET"])
def serve_config():
    data = get_full_json()
    data = json.loads(data)
    if session["perms"] == "super":
        return render_template('config.html', data=data)
    else:
        return "You do not have correct permissions for this section"