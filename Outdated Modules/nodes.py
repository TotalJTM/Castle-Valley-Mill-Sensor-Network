import time, json
import logging
from network import nodeList
logger = logging.getLogger(__name__)

class node():
	def __init__(self, ename, eid, battType=0, nDataLength=5):
		self.nodeName = ename					#name we give the node
		self.nodeID	= eid						#name the node has assigned itself
		self.batteryType = battType
		self.batteryReadings = []				#array of recent battery voltages
		self.lastResponse = []					#array of time values, when sensor responds add a new list item
		self.sensors = []						#sensors attached to our node
		self.nodeDataLength = nDataLength 		#amount of battery and response readings by system
		logger.debug(f"new node created [{self.nodeName}]")

	class sensor():
		def __init__(self, esid, eType, ename="", sdataLength=5):
			self.sensorName = ename						#name of sensor (dafults to nothing)
			self.sensorType = eType						#type of sensor
			self.sensorID = esid						#id of sensor given by device
			self.sensorData = []						#recent data for sensor device
			self.sensorDataLength = sdataLength 		#amount of data to be held by system
		
		def updateSensorData(self, newData):			#update a specific sensor's data
			if(len(self.sensorData)>=self.sensorDataLength):
				self.sensorData.pop(-1)
				self.sensorData.insert(0, newData)
			else:
				self.sensorData.insert(0, newData)

	def toJSON(self):
		return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)

	def updateNodeData(self, emessageJSON):							#update a specific node's data
		status = False
		rjson = emessageJSON #json.load(emessageJSON)
		for jsonObj in rjson["sensors"]:
			for i in self.sensors:
				if(jsonObj['id'] == i.sensorID):
					i.updateSensorData(jsonObj['data'])
					status = True
			if(status == False):
				self.sensors.insert(len(self.sensors),self.sensor(jsonObj['id'],jsonObj['type']))
				self.sensors[-1].updateSensorData(jsonObj['data'])

		if(len(self.batteryReadings)>=self.nodeDataLength):
			self.batteryReadings.pop(-1)
			self.batteryReadings.insert(0, rjson['battery'])
			self.lastResponse.pop(-1)
			self.lastResponse.insert(0, time.strftime("%d:%H:%M:%S", time.localtime()))
		else:
			self.batteryReadings.insert(0, rjson['battery'])
			self.lastResponse.insert(0, time.strftime("%d:%H:%M:%S", time.localtime()))

def get_node_json():
	comp_list = []
	for i in nodeList:
		comp_node = {}
		comp_node["nodeName"] = i.nodeName
		comp_node["nodeID"] = i.nodeID
		comp_node["batteryReadings"] = i.batteryReadings
		comp_node["lastResponse"] = i.lastResponse
		comp_node["batteryType"] = i.batteryType
		comp_node["sensors"] = {}
		for j in i.sensors:
			comp_sensor = {}
			comp_sensor["sensorName"] = j.sensorName
			comp_sensor["sensorID"] = j.sensorID
			comp_sensor["sensorType"] = j.sensorType
			comp_sensor["sensorData"] = j.sensorData
			comp_node["sensors"].append(comp_sensor)
		comp_list["nodes"].append(comp_sensor)
	send_list = {}
	send_list['nodes'] = comp_list
	logger.debug(json.dumps(send_list["nodes"]))
	return send_list