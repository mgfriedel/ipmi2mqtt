#!/usr/bin/env python3
#import sys
#import signal
import time
import yaml
import json
import pyipmi
import threading
import pyipmi.interfaces
import paho.mqtt.client as pmqtt
from types import SimpleNamespace

threadLock = threading.Lock()

def main():
    config = getConfig()
    registered = False
    threads = []

    #Create/Start Threads
    mqtt = mqttConnect(config)

    mqtt.loop_start()

    while True:
        for device in config.devices:
            thread = deviceThread(config, device, mqtt, registered)
            thread.start()
            threads.append(thread)
        if registered:
            registered = False
        time.sleep(config.ipmi.interval)

    #Wait for all threads just incase
    for thread in threads:
        thread.join()

    print("Done.")

### Functions ###
class deviceThread(threading.Thread):
    def __init__(self, config, device, mqtt, registered):
        threading.Thread.__init__(self)
        self.config = config
        self.device = device
        self.mqtt = mqtt
        self.registered = registered

    def run(self):
        ipmi = ipmiConnect(self.config.ipmi, self.device)
        processDevice(self.config, self.device, ipmi, self.mqtt, self.registered)


def ipmiConnect(auth, device):
    username = auth.username
    password = auth.password

    if hasattr(device, "username"):
        username = device.username
    if hasattr(device, "password"):
        password = device.password

    interface = pyipmi.interfaces.create_interface(
        interface='rmcp',
        slave_address=0x81,
        host_target_address=0x20,
        keep_alive_interval=1
    )

    ipmi = pyipmi.create_connection(interface)
    ipmi.session.set_session_type_rmcp(host=device.host, port=623)
    ipmi.session.set_auth_type_user(username=username, password=password)
    ipmi.target = pyipmi.Target(ipmb_address=0x20)
    ipmi.session.establish()
    return ipmi


def processDevice(config, device, ipmi, mqtt, registered):
    power = "ON" if ipmi.get_chassis_status().power_on else "OFF"
    sensors = ipmi.get_power_reading(1)
    watts = sensors.current_power

    if not registered:
        fru = ipmi.get_fru_inventory()
        product = fru.product_info_area
        mdevice = {
            #"configuration_url": f"https://{device.host}",
            "identifiers": str(product.serial_number),
            "manufacturer": str(product.manufacturer),
            "model": str(product.part_number),
            "name": device.name,
        }
        hassRegister(mdevice, device, mqtt)
    ipmi.session.close()
        
    if config.output >= 2:
        print(f"IPMI: {device.host} is powered {power} ({watts}W)")
    mqtt.publish(f"ipmi2mqtt/{device.name}/switch/state", power)
    mqtt.publish(f"ipmi2mqtt/{device.name}/watts/state", watts)

def hassRegister(mdevice, device, mqtt):
    payload = {
        "~": f"ipmi2mqtt/{device.name}/switch",
        "name": f"{device.name}_switch",
        "unique_id": f"{device.name}_switch",
        "platform": "mqtt",
        "command_topic": "~/set",
        "state_topic": "~/state",
        "device": mdevice,
    }
    topic = f"homeassistant/switch/{device.name}/switch/config"
    threadLock.acquire()
    #print(f"Register: {topic}")
    mqtt.publish(topic, json.dumps(payload))
    payload = {
        "~": f"ipmi2mqtt/{device.name}/watts",
        "name": f"{device.name}_watts",
        "unique_id": f"{device.name}_watts",
        "platform": "mqtt",
        "state_topic": "~/state",
        "device": mdevice,
    }
    topic = f"homeassistant/sensor/{device.name}/watts/config"
    mqtt.publish(topic, json.dumps(payload))
    threadLock.release()


#def term(_signo, _stack_frame):
#    m.loop_stop()
#    sys.exit()

class mqttSetHandler:
    def __init__(self, config, device):
        self.config = config
        self.device = device

    def message(self, client, userdata, message): 
        stateTopic = message.topic.replace("/set", "/state")
        value = message.payload.decode("utf-8") 
        if value in ["ON", "OFF"]:
            ipmi = ipmiConnect(self.config.ipmi, self.device)
            if value == "OFF":
                if self.config.output:
                    print(f"Shutting Down {self.device.name}")
                ipmi.chassis_control_soft_shutdown()
            elif value == "ON":
                ipmi.chassis_control_power_up()
                if self.config.output:
                    print(f"Powering Up {self.device.name}")
                power = "ON" if ipmi.get_chassis_status().power_on else "OFF"
                client.publish(f"{stateTopic}", power)
            ipmi.session.close()


def mqttConnect(config):
    mqtt = pmqtt.Client("ipmi2mqtt") #create new instance
    mqtt.connect(config.mqtt.host, config.mqtt.port)
    #signal.signal(signal.SIGTERM, term)
    # Possible todo: enable ping function to make sure a single instance is running
    #mqtt.subscribe("ipmi2mqtt/ping")
    #mqtt.message_callback_add("ipmi2mqtt/ping", on_ping)
    if config.output:
        print("MQTT Connected")
    for device in config.devices:
        setSubscribe = f"ipmi2mqtt/{device.name}/+/set"
        mqtt.subscribe(setSubscribe)
        setHandler = mqttSetHandler(config, device)
        mqtt.message_callback_add(setSubscribe, setHandler.message)
        #mqtt.message_callback_add(f"ipmi2mqtt/{device.name}/+/state", on_state)
        if config.output:
            print(f"Subscribed to {setSubscribe} for {device.name}")
    #mqtt.on_message=on_msg

    return mqtt

#Future potential handler to make sure single instance is running
def on_ping(client, userdata, message):
    if message.payload.decode('utf-8') == "Ping!":
        client.publish(message.topic, "Pong!")

def on_msg(client, userdata, message):
    print(f"MSG: {message.topic} => {message.payload.decode('utf-8')}")
    print(f"    QOS: {message.qos}, Retain: {message.retain}")

def on_state(client, userdata, message):
    print(f"STATE: {message.topic} => {message.payload.decode('utf-8')}")
    print(f"    QOS: {message.qos}, Retain: {message.retain}")

def on_set(client, userdata, message, config, device):
    print(f"SET: {message.topic} => {message.payload.decode('utf-8')}")
    print(f"    QOS: {message.qos}, Retain: {message.retain}")

def getConfig(configFile="config.yaml"):
    with open(configFile, "r") as f:
        return json.loads(json.dumps(yaml.safe_load(f)), object_hook=lambda d: SimpleNamespace(**d))

if __name__ == "__main__":
    main()
