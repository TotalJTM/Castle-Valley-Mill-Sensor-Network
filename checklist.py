from datetime import datetime
from network import db, login_manager
from flask_login import UserMixin
import network.logs as log
import json

def get_date(month=None,day=None,year=None):
	if month != None or day != None or year != None:
		datetime.strptime("{day}/{month}/{year}", "%d/%m/%y")
	else:
		return [datetime.strftime.utcnow("%d"),datetime.strftime.utcnow("%m"),datetime.strftime.utcnow("%y")]

def get_time(hour=None,minute=None):
	if hour!=None or minute!=None:
		datetime.strptime("{hour}:{minute}", "%H:%M:%S")
	else:
		return datetime.strftime("%H:%M:%S")

class checklistItem(db.Model):
	__bind_key__ = 'checklist'
	id = db.Column(db.Integer, primary_key=True)
	zone = db.Column(db.String(12), unique=False, nullable=False)
	task_name = db.Column(db.String(36), unique=False, nullable=False)
	priority = db.Column(db.String(12), unique=False, nullable=True)
	task_placement = db.Column(db.Integer, nullable=True)
	interactions = db.relationship('checklistUserInteraction', backref='checklist_item', lazy=False)

	def new_checklist_item(zone, name, priority, task_placement=None):
		self.zone = zone
		self.name =name
		self.priority = priority
		if task_placement:
			self.task_placement = task_placement
		else:
			self.task_placement = len(checklistItem.query.filter_by(zone=zone))

	def interact_checklist_item(username, interaction, id_of_item):
		element = checklistItem.query.filter_by(id=id_of_item).first()
		if interaction == 'check':
			element.interaction.append(checklistUserInteraction(state=True,day_of_change=get_date(),time_of_change=get_time(),employee_id=username))
		elif interaction == 'uncheck':
			element.interaction.append(checklistUserInteraction(state=False,day_of_change=get_date(),time_of_change=get_time(),employee_id=username))
		elif interaction == 'flip':
			if element.state[-1] == True:
				element.interaction.append(checklistUserInteraction(state=False,day_of_change=get_date(),time_of_change=get_time(),employee_id=username))
			if element.state[-1] == False:
				element.interaction.append(checklistUserInteraction(state=True,day_of_change=get_date(),time_of_change=get_time(),employee_id=username))
		else:
			pass

	def return_checklist_json(month=None,day=None,year=None):
		zonequery = checklistItem.query.with_entities(checklistItem.zone).distinct()
		if month!=None and year!=None and day!=None:
			lday =  checklistUserInteraction.query.filter_by(month_of_item=month,year_of_change=year).first()
		elif month!=None and year!=None:
			lmonth =  checklistUserInteraction.query.filter_by(month_of_item=month,year_of_change=year).first()
		else:
			clist = checklistItem.query.all()
			date = get_date()
			#lday =  checklistUserInteraction.query.filter_by(month_of_item=date[1],year_of_change=date[2],day_of_change=date[0]).first()
			return_list = {'month':date[1], 'month_items':[]}
			for i in clist:
				if i.interactions[-1].day_of_change==date[0] and i.interactions[-1].month_of_change==date[1] and i.interactions[-1].year_of_change==date[2]:
					return_list['month_items'].append({'item_name':i.name})



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

#message = {'newdata':[]}
#    counter = 0
#    element = Device.query.filter_by(assigned_id=dev_num).first()
#    message['newdata'].append({'id':f'data|battery|{dev_num}', 'type':'battery', 'data':f'{element.battery_data[-1].data}'})
#    message['newdata'].append({'id':f'data|timestamp|{dev_num}', 'type':'timestamp', 'data':f'{element.battery_data[-1].timestamp}'})