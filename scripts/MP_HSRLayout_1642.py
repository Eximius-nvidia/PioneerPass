import paho.mqtt.client as mqttClient
import time
import random
import json
import os
import datetime


broker = "127.0.0.1"
port = 1883
sleep_interval = 10
qos = 0

topic = "Temperature/"
payload = {
    "location" : "HSR Layout",
    "status" : 1,
}

payload1 = {	
        "datatime":"1594274900.7114",
		"deviceidentifier":"BlackBoxTester2",
		"protocol":{
			"id":1,
			"name":"PioneerPassAPI",
			"type":20},
		"sensoridentifier":"PioneerPassAPI_1",
		"type":"sensor",
		"value":{
			"deviceId":"1642",
			"flag":"None",
			"measurementUnit":"C",
			"sensorName":"Temperature Sensor",
			"sensorType":"Temperature Sensor",
			"timestamp":1594274872,
			"value":"50.000"},
		"valuetype":"0xFF82"}

def on_connect(client, userdata, flags, rc):
    """
    Method to perform initial connection operation
    :param client:
    :param userdata:
    :param flags:
    :param rc:
    :return:
    """
    status = {0: "Connection successful",
              1: "Connection refused – incorrect protocol version",
              2: "Connection refused – invalid client identifier",
              3: "Connection refused – server unavailable",
              4: "Connection refused – bad username or password",
              5: "Connection refused – not authorised",
              6 - 255: "Currently unused"
              }
    print("-" * 60)
    text = "{:<27} : {}\n{:<27} : {}\n{:<27} : {}".format("Client connected to broker", client._host, "Client ID/Location ID", str(client._client_id,"UTF-8"), "Client status", status[rc])
    print(text)
    print("-" * 60)
    # Publish as the ATM is active
    client.publish("Temperature/status/" + str(client._client_id, "UTF-8"), payload = json.dumps(payload), qos=1, retain= True)

def on_disconnect(client, userdata, rc):
    """
    On client disconnect
    :param client:
    :param userdata:
    :param rc:
    :return:
    """
    if client.is_connected() == False:
        print("Client disconnected............")
    else:
        print("Something gone wrong in Client disconnecting")

def on_message(client, userdata, msg):
    if payload['location'] in msg.topic:
        print(msg.payload.decode())

if __name__ == "__main__":

    os.system('cls')
    client = mqttClient.Client(payload['location']) # create new instance
    client.on_connect = on_connect  # attach function to callback
    client.on_disconnect = on_disconnect
    client.on_message = on_message
    client.connect(broker, port=port)  # connect to broker
    client.subscribe("TelemetryInformationAck/#")
    client.loop_start()  # start the loop

    while not client.is_connected():  # Wait for connection
        time.sleep(0.1)

    try:
        while True:
            payload1['value']['value']   = round(random.uniform(15, 60),3) # Will be replaced with sensor's temperature
            payload1['value']['timestamp'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            topic_to_send = topic + payload['location']
            client.publish(topic_to_send, payload = json.dumps(payload1), qos=qos, retain= False)
            print("Current Temperature is ........ ",payload1['value']['value'], '\"' + str(payload1['value']['deviceId']) + '\"')
            # print("payload = {}".format(payload))
            time.sleep(sleep_interval)

    except KeyboardInterrupt:
        # Publish as the MP center is inactive
        payload["status"] = 0
        client.publish("Temperature/status/" + str(client._client_id, "UTF-8"), payload = json.dumps(payload), qos=1, retain=True)
        client.disconnect()
        print("------- Disconnected -------")
        os.sys.exit()
        client.loop_stop()
