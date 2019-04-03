import json
#import network.nodes as nde


configurationFileDir = "network/config/"

def get_node_config(nodeList):
	nodeList = []
	newlist = []
	with open(configurationFileDir+'nodesensorlist.json') as file:
		d = json.load(file)
		for i in d["nodes"]:
			print(i)
			nodeList.insert(0,nde.node(i["nodeID"],i["nodeAssignedName"], i["batteryType"]))
			for s in i["sensors"]:
				ss = nodeList[0].sensor(s["sensorID"], s["sensorType"], s["sensorAssignedName"], s["sensorCalibration"])
				nodeList[0].sensors.insert(-1, ss)
	return nodeList