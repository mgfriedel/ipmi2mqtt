# ipmi2mqtt
ipmi2mqtt polls IPMI devices and publishes to MQTT in a format compatible with the Home Assistant (hass) auto-discovery system.
Power controls are also available, it will take at least 1 poll interval for switch status to update in hass. For power down, the shutdown call is used which attempts to gracefully shut the system down instead of a hard power off.

## Docker Hub Deployment
#### Configure:
- Copy config.yaml.example to config.yaml
- Modify config.yaml with your MQTT server and IPMI device(s)

#### Test:
```
docker run --rm -it -v $(pwd)/config.yaml:/app/config.yaml --name ipmi2mqtt mgfriedel/ipmi2mqtt
```

#### Run w/ auto restart:
```
docker run -d --restart unless-stopped -it -v $(pwd)/config.yaml:/app/config.yaml --name ipmi2mqtt mgfriedel/ipmi2mqtt
```

#### Stop/Remove:
```
docker stop ipmi2mqtt
docker rm ipmi2mqtt
```

## Manual Deployment Prep
#### Clone:
```
git clone https://github.com/mgfriedel/ipmi2mqtt.git
```

#### Prep:
```
cd ipmi2mqtt
cp config.yaml.example config.yaml
```
#### Configure
Edit config.yaml with your IPMI device(s) and MQTT server information.
The script is intended to be loaded as a container, but can be run locally if desired.

## Manual Docker
### Build
```
docker build -t ipmi2mqtt:latest .
```

### Run
#### Test Run:
```
docker run --rm -it -v $(pwd)/config.yaml:/app/config.yaml --name ipmi2mqtt ipmi2mqtt
```

#### Run w/ auto restart:
```
docker run -d --restart unless-stopped -it -v $(pwd)/config.yaml:/app/config.yaml --name ipmi2mqtt ipmi2mqtt
```

#### Stop/Remove:
```
docker stop ipmi2mqtt
docker rm ipmi2mqtt
```

### Helper Scripts:
- Run ``./build.sh`` to build a new image and prune (all) unlabeled/dangling images
- Run ``./test.sh`` to test a temporary container that will remove itself when done
- Run ``./start.sh`` to start a Docker container that will auto-restart unless stopped
- Run ``./stop.sh`` to stop and remove the ipmi2mqtt container

## Manual Run Without Docker
Note: ipmi2mptt must be run from the same directory config.xml is located.

#### Install required modules:
```
pip3 install -r requirements.txt
```

#### Run:
```
python3 ipmi2mqtt.py
```
