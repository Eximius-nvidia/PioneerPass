import paho.mqtt.client as mqttClient
import time
import random
import json
import os
import threading
from configparser import ConfigParser

broker = "127.0.0.1"
port = 1883
UI_deviceId = 3100
qos = 0

topic = "TelemetryInformationAck/"

payload1 = {
    "location" : "Majestic",
    "status" : 1,
}

payload = {	
        "timestamp" : "1594274872",
		"value" : "Temperature too high" , 
		"sensor" : "1644" }


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
    # Publish as the UI is active
    client.publish("TelemetryInformationAck/status/" + str(client._client_id, "UTF-8"), payload = json.dumps(payload1), qos=1, retain= True)

def on_message(client, userdata, msg):
    t = threading.Thread(target= process_msgs, args = (client, userdata, msg,))
    t.daemon = True
    t.start()
    
def process_msgs(client, userdata, msg): 
    if "status" not in msg.topic:
        location_id = msg.topic.split("/")[-1]
        payload_dictionary = json.loads(str(msg.payload, "UTF-8"))        
        payload['timestamp'] = payload_dictionary['value']['timestamp']
        payload['sensor'] = payload_dictionary['value']['deviceId']
        topic_to_send = topic + location_id
        print("Received data from", payload_dictionary['value']['deviceId'],payload_dictionary['value']['timestamp'], payload_dictionary['value']['value'])
        for getth in range(len(devices)) :
            if devices[getth].get('location') == location_id :
                Temp_UpperTh = float(devices[getth].get('thresholdtemp'))
    
        if location_id not in UIconfigprev.sections():            
            UIconfigprev.add_section(location_id)            
            UIconfigprev.set(location_id,'prevuiresp', 'Temperature too high')
            with open(prev_UI_data, 'w') as configuifile:
                UIconfigprev.write(configuifile)
                
        if payload_dictionary['value']['value'] > Temp_UpperTh: 
            payload['value'] = "Temperature too high"
            client.publish(topic_to_send, payload = json.dumps(payload), qos=qos, retain= False)
            UIconfigprev.set(location_id,'prevuiresp', 'Temperature too high')
            print("Sent response to ", payload_dictionary['value']['deviceId'], "as", payload['value'])
        elif payload_dictionary['value']['value'] <= Temp_UpperTh:
            if UIconfigprev[location_id]['prevuiresp'] == "Temperature too high":
                payload['value'] = "Temperature Back to normal"
                client.publish(topic_to_send, payload = json.dumps(payload), qos=qos, retain= False)
                UIconfigprev.set(location_id,'prevuiresp', 'Temperature Back to normal')            
            print("Sent response to ", payload_dictionary['value']['deviceId'], "as", payload['value'])
        else :
            print("No response required for ", payload_dictionary['value']['deviceId'], "as", payload_dictionary['value']['value'], "less than", Temp_UpperTh)
        
        with open(prev_UI_data, 'w') as configuifile: 
            UIconfigprev.write(configuifile)
        

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

if __name__ == "__main__":

    os.system('cls')
    client = mqttClient.Client(payload1['location'])  # create new instance
    client.on_connect = on_connect  # attach function to callback
    client.on_disconnect = on_disconnect
    client.on_message = on_message
    client.connect(broker, port=port)  # connect to broker
    client.subscribe("Temperature/#")
    client.loop_start()  # start the loop
    
    prev_UI_data = os.path.join(os.getcwd(),"UIfile.ini")
    if os.path.isfile(prev_UI_data):
        os.mkdir(prev_UI_data)
    UIconfigprev = ConfigParser()
    UIconfigprev.read(prev_UI_data)
    
    mp_specs = open('MP_Spec.json','r')
    jsondata = mp_specs.read()
    mpspec_json = json.loads(jsondata)
    devices = mpspec_json['locations']
    
    while not client.is_connected():  # Wait for connection
        time.sleep(0.1)

    try:
        while True:
            pass

    except KeyboardInterrupt:
        # Publish as the ATM is inactive
        payload1["status"] = 0
        client.publish("TelemetryInformationAck/status/" + str(client._client_id, "UTF-8"), payload = json.dumps(payload1), qos=1, retain=True)
        client.disconnect()
        client.loop_stop()
