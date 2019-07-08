from datetime import datetime
from network import db, login_manager
from flask_login import UserMixin
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, IntegerField, RadioField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
import network.logs as log
import json

def get_date(month=None,day=None,year=None):
	if month != None or day != None or year != None:
		return datetime.strptime("{day}/{month}/{year}", "%d/%m/%y")
	else:
		currdate = datetime.now()
		return [int(currdate.strftime("%d")),int(currdate.strftime("%m")),int(currdate.strftime("%y"))]

def get_time(hour=None,minute=None):
	if hour!=None or minute!=None:
		datetime.strptime("{hour}:{minute}", "%H:%M:%S")
	else:
		currdate = datetime.now()
		return currdate.strftime("%H:%M:%S")

class mchecklist(db.Model):
	__bind_key__ = 'checklist'
	id = db.Column(db.Integer, primary_key=True)
	title = db.Column(db.String(26), unique=False, nullable=False)
	zones_in_list = db.relationship('buildingZone', backref='main', lazy=False, order_by="buildingZone.zone_position")

class buildingZone(db.Model):
	__bind_key__ = 'checklist'
	id = db.Column(db.Integer, primary_key=True)
	title = db.Column(db.String(30), unique=False, nullable=False)
	zone_position = db.Column(db.Integer, unique=False, nullable=False)
	items_in_zone = db.relationship('checklistItem', backref='building_zone', lazy=False, order_by="checklistItem.task_placement")
	parent_id = db.Column(db.Integer, db.ForeignKey('mchecklist.id'), nullable=False)

class checklistItem(db.Model):
	__bind_key__ = 'checklist'
	id = db.Column(db.Integer, primary_key=True)
	#group = db.Column(db.String(20), unique=False, nullable=False)
	#zone = db.Column(db.String(20), unique=False, nullable=False)
	task_name = db.Column(db.String(64), unique=False, nullable=False)
	task_placement = db.Column(db.Integer, unique=False, nullable=True)
	interactions = db.relationship('checklistUserInteraction', backref='checklist_item', lazy=False, order_by="checklistUserInteraction.id")
	parent_id = db.Column(db.Integer, db.ForeignKey('building_zone.id'), nullable=False)

class checklistUserInteraction(db.Model):
	__bind_key__ = 'checklist'
	id = db.Column(db.Integer, primary_key=True)
	state = db.Column(db.Boolean, unique=False, default=False)
	year_of_change = db.Column(db.Integer, unique=False, nullable=False)
	month_of_change = db.Column(db.Integer, unique=False, nullable=False)
	day_of_change = db.Column(db.Integer, unique=False, nullable=False)
	time_of_change = db.Column(db.String(10), unique=False, nullable=False)
	employee_id = db.Column(db.String(20),unique=False,nullable=False)
	parent_id = db.Column(db.Integer, db.ForeignKey('checklist_item.id'), nullable=False)

class checklist():

	def new_checklist(title):
		obj = mchecklist(title=title)
		db.session.add(obj)
		db.session.commit()

	def new_zone(checklist_title,zone_title,placement=None):
		element = mchecklist.query.filter_by(title=str(checklist_title)).first()
		if placement == None:
			placement = len(element.zones_in_list)
		obj = buildingZone(title=str(zone_title), zone_position=placement)
		element.zones_in_list.append(obj)
		db.session.commit()

	def new_item(checklist_title,zone_title,item_title,placement=None):
		element = mchecklist.query.filter_by(title=checklist_title).first()
		for i in element.zones_in_list:
			if i.title == zone_title:
				if placement == None:
					placement = len(i.items_in_zone)
				obj = checklistItem(task_name=item_title,task_placement=len(i.items_in_zone))
				i.items_in_zone.append(obj)
				for j in i.items_in_zone:
					if j.task_name == item_title:
						date = get_date()
						interact = checklistUserInteraction(state=False,day_of_change=date[0],month_of_change=date[1],year_of_change=date[2],time_of_change=get_time(),employee_id='S_reset')
						j.interactions.append(interact)
		db.session.commit()

	def remove_checklist(checklist_title):
		element = mchecklist.query.filter_by(title=str(checklist_title)).first()
		for i in element.zones_in_list:
			for j in i.items_in_zone:
				for k in j.interactions:
					db.session.delete(k)
				db.session.delete(j)
			db.session.delete(i)
		db.session.delete(element)
		db.session.commit()

	def remove_zone(checklist_title,zone_title):
		element = mchecklist.query.filter_by(title=str(checklist_title)).first()
		for i in element.zones_in_list:
			if i.title == zone_title:
				for j in i.items_in_zone:
					for k in j.interactions:
						db.session.delete(k)
					db.session.delete(j)
				db.session.delete(i)
		db.session.commit()

	def remove_item(checklist_title,item_id):
		element = mchecklist.query.filter_by(title=checklist_title).first()
		for i in element.zones_in_list:
			for j in i.items_in_zone:
				log.logger.debug(j.id)
				if j.id == item_id:
					log.logger.debug('deleted')
					for k in j.interactions:
						db.session.delete(k)
					db.session.delete(j)
		db.session.commit()

	#checklist.interact_checklist_item('Daily Morning','TotalJTM','flip',1)
	def interact_checklist_item(checklist, zone, id_of_item, username, interaction):
		element = mchecklist.query.filter_by(title=checklist).first()
		flag = False
		if zone == None:
			for i in element.zones_in_list:
				for j in i.items_in_zone:
					if j.id == id_of_item:
						element = j
		else:
			for i in element.zones_in_list:
				if i == zone:
					for j in i.items_in_zone:
						if j.id == id_of_item:
							element = j
		if not flag:
			date = get_date()
			if interaction == 'check':
				interact = checklistUserInteraction(state=True,day_of_change=date[0],month_of_change=date[1],year_of_change=date[2],time_of_change=get_time(),employee_id=username)
				element.interactions.append(interact)
			elif interaction == 'uncheck':
				interact = checklistUserInteraction(state=False,day_of_change=date[0],month_of_change=date[1],year_of_change=date[2],time_of_change=get_time(),employee_id=username)
				element.interactions.append(interact)
			elif interaction == 'flip':
				iInter = element.interactions[-1]
				log.logger.debug(iInter.state)
				if iInter.state == True:
					interact = checklistUserInteraction(state=False,day_of_change=date[0],month_of_change=date[1],year_of_change=date[2],time_of_change=get_time(),employee_id=username)
					element.interactions.append(interact)
				elif iInter.state == False:
					interact = checklistUserInteraction(state=True,day_of_change=date[0],month_of_change=date[1],year_of_change=date[2],time_of_change=get_time(),employee_id=username)
					element.interactions.append(interact)
				else:
					pass
			else:
				pass
			log.logger.debug(len(element.interactions))
			db.session.commit()

	def get_checklist_item(checklist, zone, id_of_item):
		element = mchecklist.query.filter_by(title=checklist).first()
		if zone:
			for i in element.zones_in_list:
				if i == zone:
					for j in i.items_in_zone:
						if j.id == id_of_item:
							return {"item_name":j.task_name,"item_id":j.id,"item_state":j.interactions[-1].state,"item_user":j.interactions[-1].employee_id,"item_placement":j.task_placement}
		else:
			for i in element.zones_in_list:
				for j in i.items_in_zone:
					if j.id == id_of_item:
						return {"item_name":j.task_name,"item_id":j.id,"item_state":j.interactions[-1].state,"item_user":j.interactions[-1].employee_id,"item_placement":j.task_placement}
	
	def get_checklist_day(checklist,day=None,month=None,year=None):
		element = mchecklist.query.filter_by(title=checklist).first()
		date = get_date()
		if day == None:
			day = date[0]
		if month == None:
			month = date[1]
		if  year== None:
			year = date[2]
		if element:
			temp = element.title.lower()
			curl = temp.replace(' ','-')
			jchecklist = {'checklist_name':element.title, 'checklist_url':curl,'zones':[]}
			for z in element.zones_in_list:
				temp2 = z.title.lower()
				zurl = temp2.replace(' ','-')
				jzone = {'zone_name':z.title, 'zone_position':z.zone_position, 'zone_url':zurl, 'zone_items':[]}
				for i in z.items_in_zone:
					#log.logger.debug(f'{i.task_name}')
					jinteractions = {'item_name':i.task_name, 'item_placement':i.task_placement, 'item_id':i.id, 'item_state':[]}
					for r in reversed(i.interactions):
						#log.logger.debug(f'{r.day_of_change},{r.month_of_change},{r.year_of_change}')
						if r.month_of_change==int(month) and r.day_of_change==int(day) and r.year_of_change==int(year):
							jinteractions['item_state'].append({'state':r.state,'time':r.time_of_change,'employee':r.employee_id})
					jzone['zone_items'].append(jinteractions)
				jchecklist['zones'].append(jzone)
			return jchecklist
		else:
			return None

	def get_real_checklist_name(lowered):
		element = checklist.get_checklist_names()
		for i in element:
			temp = i.lower()
			temp = temp.replace(' ','-')
			if temp == lowered:
				return i
		return None

	def get_real_zone_name(lowered):
		element = mchecklist.query.all()
		for j in element:
			for i in j.zones_in_list:
				i = i.title
				temp = i.lower()
				temp = temp.replace(' ','-')
				if temp == lowered:
					return i
		return None


	def get_checklist_names():
		element = mchecklist.query.all()
		checklist_names = []
		for i in element:
			checklist_names.append(i.title)
		return checklist_names

	def reset_checklist(checklist=None):
		date = get_date()
		if checklist:
			clist = mchecklist.query.filter_by(title=checklist).first()
			for z in clist.zones_in_list:
				for i in z.items_in_zone:
					interact = checklistUserInteraction(state=False,day_of_change=date[0],month_of_change=date[1],year_of_change=date[2],time_of_change=get_time(),employee_id='S_reset')
					i.interactions.append(interact)
					#log.logger.debug(f'"interaction" : {i.task_name}')
		else:
			clist = mchecklist.query.all()
			for c in clist:
				for z in c.zones_in_list:
					for i in z.items_in_zone:
						interact = checklistUserInteraction(state=False,day_of_change=date[0],month_of_change=date[1],year_of_change=date[2],time_of_change=get_time(),employee_id='S_reset')
						i.interactions.append(interact)
						#log.logger.debug(f'"interaction" : {i.task_name}')
		db.session.commit()

	class ChecklistForm(FlaskForm):
		title = StringField('Checklist Title', validators=[DataRequired()])

	class ZoneForm(FlaskForm):
		title = StringField('Zone Title', validators=[DataRequired()])
		placement = StringField('Appearance Order')

	class ItemForm(FlaskForm):
		title = StringField('Item Title', validators=[DataRequired()])
		placement = StringField('Appearance Order')

#message = {'newdata':[]}
#    counter = 0
#    element = Device.query.filter_by(assigned_id=dev_num).first()
#    message['newdata'].append({'id':f'data|battery|{dev_num}', 'type':'battery', 'data':f'{element.battery_data[-1].data}'})
#    message['newdata'].append({'id':f'data|timestamp|{dev_num}', 'type':'timestamp', 'data':f'{element.battery_data[-1].timestamp}'})