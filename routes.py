from flask import render_template, url_for, flash, redirect, request, session
from flask_socketio import SocketIO
from network import app, db, bcrypt, socketio
from network.forms import LoginForm, DeviceForm, SensorForm, DeviceForm, SensorEventForm
from network.models import User, Device, Sensor, SensorEvent
from network.checklist import checklist
from flask_login import login_user, current_user, logout_user, login_required
import network.logs as log
from network.pagecompiler import get_header_json, get_full_json, get_floor_json
from datetime import datetime
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
            socketio.emit('reload', True, namespace="/config")
            return '<script>window.close()</script>'
        return render_template('deviceform.html', form=form)

    if(config_option == 'sensor'):
        form = SensorForm(request.form)
        if(request.method == 'POST' and form.validate_on_submit()):
            Device.new_sensor(dev_num,sensor_id=form.entry_assigned_id.data,sensor_title=form.entry_title.data,sensor_type=form.entry_sensor_type.data)
            socketio.emit('reload', True, namespace="/config")
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
            socketio.emit('reload', True, namespace="/config")
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
                    socketio.emit('reload', True, namespace="/config")
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
                            socketio.emit('reload', True, namespace="/config")
                            return '<script>window.close()</script>'
                        form.entry_title.data = j.title
                        form.entry_threshold_val.data = j.threshold_val
                        form.entry_threshold_comparator.data = j.threshold_comparator
                        form.entry_on_event.data = j.on_event
                    return render_template('eventform.html', form=form)

        return "no sensor"
    return "not valid address"

@socketio.on('handle_config', namespace="/config")
def handle_config(json_data):
    id_name = json_data['id']
    pid_name = id_name.split('-')
    action = json_data['action']
    log.logger.debug(id_name)
    if action == "remove":
        if len(pid_name) > 1:
            Device.remove_sensor(pid_name[0],pid_name[1])
            log.logger.debug("sensor remove")
            socketio.emit('reload', True, namespace="/config")
        else:
            Device.remove(id_name)
            socketio.emit('reload', True, namespace="/config")
    if str(action) == "removeevent":
        log.logger.debug(action)
        Device.remove_sensor_event(pid_name[0],pid_name[1],pid_name[2])
        socketio.emit('reload', True, namespace="/config")

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
            socketio.emit('reload', True, namespace="/config")
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
                ndata = sensor["data"].split('|')
                if len(ndata) > 1:
                    Device.new_sensor(passed_id=message["id"],sensor_id=sensor["id"],sensor_type=sensor["type"])
                    Device.new_sensor_data(passed_id=message["id"],sensor_id=sensor["id"],new_data=ndata[1])
                    update_site_data(message["id"])
                else:
                    Device.new_sensor(passed_id=message["id"],sensor_id=sensor["id"],sensor_type=sensor["type"])
                    Device.new_sensor_data(passed_id=message["id"],sensor_id=sensor["id"],new_data=sensor["data"])
                    update_site_data(message["id"])
        else:
            Device.new_battery_data(passed_id=message["id"],new_data=message["battery_level"])
            for sensor in message["sensors"]:
                check_sensor = False
                ndata = sensor["data"].split('|')
                for j in Device.query.filter_by(assigned_id=message["id"]).first().sensors:
                    if j.assigned_id == sensor["id"]:
                        if len(ndata) > 1:
                            Device.new_sensor_data(passed_id=message["id"],sensor_id=sensor["id"],new_data=ndata[1])
                            check_sensor = True
                            update_site_data(message["id"])
                        else:
                            Device.new_sensor_data(passed_id=message["id"],sensor_id=sensor["id"],new_data=sensor["data"])
                            check_sensor = True
                            update_site_data(message["id"])
                if not check_sensor:
                    Device.new_sensor(passed_id=message["id"],sensor_id=sensor["id"],sensor_type=sensor["type"])
                    if len(ndata) > 1:
                        Device.new_sensor_data(passed_id=message["id"],sensor_id=sensor["id"],new_data=ndata[1])
                    else:
                        Device.new_sensor_data(passed_id=message["id"],sensor_id=sensor["id"],new_data=sensor["data"])

    return 'done'

def update_site_data(dev_num):
    message = {'newdata':[]}
    counter = 0
    element = Device.query.filter_by(assigned_id=dev_num).first()
    message['newdata'].append({'id':f'data|battery|{dev_num}', 'type':'battery', 'data':f'{element.battery_data[-1].data}'})
    message['newdata'].append({'id':f'data|timestamp|{dev_num}', 'type':'timestamp', 'data':f'{element.battery_data[-1].timestamp}'})
    for sensor in element.sensors:
        message['newdata'].append({"id":f'data|{dev_num}|{sensor.assigned_id}', "type":"data", "data":f'{sensor.sensor_data[-1].data}'})
            #if counter != len(sensor):
            #    message += ','
    socketio.emit('updatepage', message, namespace="/data")

def update_header(alerts):
    alert_list = ""
    counter = 0
    for alert in alerts:
        alert_list += f'{alert}'
        counter = counter + 1
        if counter != len(alert):
            alert_list += ','
    time = datetime.now().strftime("%b %d, %I:%M:%S")
    socketio.emit('updateheader', {'time':f'{time}', 'alerts':[f'{alert_list}']}, broadcast=True, namespace="/all")

@app.route("/server/retrieve", methods=['POST'])
def serve_device():
    return ooo

@app.route("/floor/first", methods=["GET"])
def serve_floor_first():
    blocks_and_groups = '{"block":[{"title":"valve1","id":"111115|1"}],"group":[{"table_title":"1st Floor Bearing Temperatures","sensor_type":"bearing_temp"},{"table_title":"1st Floor Line Shaft RPM","sensor_type":"shaft_rpm"},{"table_title":"1st Floor Valves","sensor_type":"valve"},{"table_title":"1st Floor Devices Battery Level","sensor_type":"dev|battery_level"},{"table_title":"1st Floor Devices Last Online","sensor_type":"dev|last_online"}]}' #{"title":"","id":""} {"table_title":"","sensor_type":""}
    data = compile_into_BandG(1,blocks_and_groups)
    log.logger.debug(data)
    return render_template('floorblank.html', data=data)

@app.route("/floor/second", methods=["GET"])
def serve_floor_second():
    blocks_and_groups = '{"block":[{"title":"valve1","id":"111115|1"}],"group":[{"table_title":"1st Floor Devices Battery Level","sensor_type":"dev|battery_level"}]}' #{"title":"","id":""} {"table_title":"","sensor_type":""}
    data = compile_into_BandG(2,blocks_and_groups)
    log.logger.debug(data)
    return render_template('floorblank.html', data=data)

@app.route("/floor/third", methods=["GET"])
def serve_floor_third():
    blocks_and_groups = '{"block":[{"title":"valve1","id":"111115|1"}],"group":[{"table_title":"1st Floor Devices Battery Level","sensor_type":"dev|battery_level"}]}' #{"title":"","id":""} {"table_title":"","sensor_type":""}
    data = compile_into_BandG(3,blocks_and_groups)
    log.logger.debug(data)
    return render_template('floorblank.html', data=data)

@app.route("/floor/basement", methods=["GET"])
def serve_floor_basement():
    blocks_and_groups = '{"block":[{"title":"valve1","id":"111115|1"}],"group":[{"table_title":"1st Floor Devices Battery Level","sensor_type":"dev|battery_level"}]}' #{"title":"","id":""} {"table_title":"","sensor_type":""}
    data = compile_into_BandG(0,blocks_and_groups)
    log.logger.debug(data)
    return render_template('floorblank.html', data=data)

@login_required
@app.route("/checklist/", methods=["GET"])
def serve_checklist_menu():
    data = '{'
    data += get_header_json()
    data += '}'
    data = json.loads(data)

    element = checklist.get_checklist_names()
    nl = []
    for i in element:
        temp = i.lower()
        temp = temp.replace(' ','-')
        nl.append([i,temp])
    return render_template('checklistmenu.html', data=data, checklistname=nl)

@login_required
@app.route("/checklist/<spec_checklist>", methods=["GET"])
def serve_checklists(spec_checklist):
    data = '{'
    data += get_header_json()
    data += '}'
    data = json.loads(data)

    element = checklist.get_checklist_names()
    nl = []
    for i in element:
        temp = i.lower()
        temp = temp.replace(' ','-')
        nl.append([i,temp])
    for i in element:
        temp = i.lower()
        temp = temp.replace(' ','-')
        if temp == spec_checklist:
            cldata = checklist.get_checklist_day(i)
            return render_template('checklistblank.html', data=data, checklist=cldata, checklistname=nl)
    return None

@app.route("/checklist/<spec_checklist>/config", methods=["GET","POST"])
def config_checklists(spec_checklist):
    data = '{'
    data += get_header_json()
    data += '}'
    data = json.loads(data)

    nl = []

    if session['perms'] == 'super' and request.method == 'POST':
        passed = request.form.to_dict()
        f_action = passed['data[action]']
        f_id = passed['data[id]']
        f_type = passed['data[type]']
        clist_name = None

        element = checklist.get_checklist_names()
        nl = []
        for i in element:
            temp = i.lower()
            temp = temp.replace(' ','-')
            nl.append([i,temp])
            if temp == spec_checklist:
                clist_name = i
        log.logger.debug(f'{f_id},{f_action},{f_type}')
        if clist_name:
            if f_type == 'item':
                if f_action == 'remove':
                    checklist.remove_item(clist_name,int(f_id))
                    log.logger.debug(f'{f_id},{clist_name}')
                    socketio.emit('reload_clist', True)
                if f_action == 'modify':
                    pass
                    
            if f_type == 'zone':
                if f_action == 'remove':
                    log.logger.debug(f'{clist_name}, {f_id}')
                    checklist.remove_zone(clist_name,f_id)
                    socketio.emit('reload_clist', True)
                if f_action == 'modify':
                    pass
                    
            if f_type == 'checklist':
                if f_action == 'remove':
                    checklist.remove_checklist(clist_name)
                    socketio.emit('reload_clist', True)
                    spec_checklisttemp = checklist.get_checklist_names()
                    spec_checklist = spec_checklisttemp[0]
                if f_action == 'modify':
                    pass

    element = checklist.get_checklist_names()
    for i in element:
        temp = i.lower()
        temp = temp.replace(' ','-')
        if temp == spec_checklist:
            cldata = checklist.get_checklist_day(i)

    nl = []
    for i in element:
            temp = i.lower()
            temp = temp.replace(' ','-')
            nl.append([i,temp])

    return render_template('checklistblankconf.html', data=data, checklist=cldata, checklistname=nl)

@app.route("/checklist/form/<form_type>/<f_id>", methods=["GET","POST"])
def checklist_form(form_type,f_id):
    if form_type == 'checklist':
        form = checklist.ChecklistForm(request.form)
        if request.method == 'POST' :
            log.logger.debug(f'{form.title.data}')
            checklist.new_checklist(form.title.data)
            socketio.emit('reload_clist', True)
            return '<script>window.close()</script>'
        return render_template('checklistform.html', form=form, id=f_id, f_type=form_type)
    if form_type == 'zone':
        form = checklist.ZoneForm(request.form)
        if request.method == 'POST' :
            log.logger.debug(f'{form.title.data},{f_id}')
            f_id = checklist.get_real_checklist_name(f_id)
            log.logger.debug(f'{f_id}')
            if form.placement.data is None or form.placement.data == '':
                checklist.new_zone(f_id,form.title.data)
            else:
                checklist.new_zone(f_id,form.title.data,placement=form.placement.data)
            socketio.emit('reload_clist', True)
            return '<script>window.close()</script>'
        form.placement.data = ''
        return render_template('checklistform.html', form=form, id=f_id, f_type=form_type)
    if form_type == 'item':
        form = checklist.ItemForm(request.form)
        if request.method == 'POST' :
            f_id = f_id.split('_')
            f_id[0] = checklist.get_real_checklist_name(f_id[0])
            f_id[1] = checklist.get_real_zone_name(f_id[1])
            log.logger.debug(f'{f_id[0]},{f_id[1]}')
            if form.placement.data:
                checklist.new_item(f_id[0],f_id[1],form.title.data,placement=form.placement.data)
            else:
                checklist.new_item(f_id[0],f_id[1],form.title.data)
            socketio.emit('reload_clist', True)
            return '<script>window.close()</script>'
        return render_template('checklistform.html', form=form, id=f_id, f_type=form_type)

#form.entry_assigned_id.data

@socketio.on('handleChecklistUpdate')
def handleChecklistUpdate(json_data):
    #log.logger.debug(f'{json_data.id}, {json_data.ctype}')
    idOfClicked = int(json_data['id'])
    checklistType = json_data['ctype']
    log.logger.debug('11111111111111111111')
    log.logger.debug(session['username'])
    currentUser = str(session['username'])
    log.logger.debug(currentUser)
    element = checklist.get_checklist_names()
    for i in element:
        temp = i.lower()
        temp = temp.replace(' ','-')
        if temp == checklistType:
            checklist.interact_checklist_item(checklist=i,zone=None,id_of_item=idOfClicked,username=currentUser,interaction='flip')
            j = checklist.get_checklist_item(checklist=i,zone=None,id_of_item=idOfClicked)
            socketio.emit('clist_update', {'id':idOfClicked, 'state':j['item_state']})

@login_required
@app.route("/config", methods=["GET"])
def serve_config():
    data = get_full_json()
    data = json.loads(data)
    if session["perms"] == "super":
        return render_template('config.html', data=data)
    else:
        return "You do not have correct permissions for this section"

def compile_into_BandG(floor_num, blocks_and_groups_input):
    floor_data = get_floor_json(floor_num)
    floor_data = json.loads(floor_data)
    blocks_and_groups = blocks_and_groups_input
    b_and_g = json.loads(blocks_and_groups)

    data = "{"
    data += get_header_json()
    data += ',"blocks":['

    for i in b_and_g["block"]:
        d_data = ""
        d_state = 0
        count = 0
        addr = i["id"].split('|')
        for j in floor_data["devices"]:
            if j["assigned_id"] == addr[0]:
                for sens in j["sensors"]:
                    if j["assigned_id"] == int(addr[1]):
                        latest_data = sens["sensor_data"][0]
                        data += f'{{"title":"{i["title"]}","id":"{i["id"]}","data":"{latest_data["data"]}"}}'
                        count = count + 1
                        if count != len(b_and_g["block"]):
                            data += ","

    data += '],"groups":['
    count = 0
    for i in b_and_g["group"]:
        log.logger.debug(i)
        d_data = ""
        d_state = 0
        group_element = ""
        stype = i["sensor_type"].split('|')
        if len(stype) > 1:
            if stype[0] == "dev":
                if stype[1] == "battery_level":
                    for j in floor_data["devices"]:
                        try:
                            group_element += f'{{"title":"{j["title"]}","id":"{j["assigned_id"]}","data":"{j["battery_data"][0]["data"]}","status":""}},'
                        except:
                            pass
                elif stype[1] == "last_online":
                    for j in floor_data["devices"]:
                        try:
                            group_element += f'{{"title":"{j["title"]}","id":"{j["assigned_id"]}","data":"{j["battery_data"][0]["timestamp"]}","status":""}},'
                        except:
                            pass
                else:
                    for j in floor_data["devices"]:
                        data_field = j[f'{stype[1]}']
                        if data_field is not None:
                            group_element += f'{{"title":"{j["title"]}","id":"bat|{j["assigned_id"]}","data":"{data_field}","status":""}},'
                    
        else:
            for j in floor_data["devices"]:
                for sens in j["sensors"]:
                    if sens["sensor_type"] == i["sensor_type"]:
                        if(len(sens["sensor_data"]) > 0):
                            latest_data = sens["sensor_data"][0]
                            group_element += f'{{"title":"{j["title"]}","id":"{j["assigned_id"]}","data":"{latest_data["data"]}","status":""}},'
        if group_element != "":
            group_element = group_element[:-1]
        log.logger.debug(group_element)
        if len(stype) > 1:
            data += f'{{"title":"{i["table_title"]}","sensor_type":"{stype[1]}", "elements":[{group_element}]}}'
        else:
            log.logger.debug(stype)
            js = ""
            js = js.join(stype)
            data += f'{{"title":"{i["table_title"]}","sensor_type":"{js}", "elements":[{group_element}]}}'
        count = count+1
        log.logger.debug(f'{count}, {len(b_and_g["group"])}')
        if count != len(b_and_g["group"]):
            data += ","

    data += ']}'

    data = json.loads(data)
    return data