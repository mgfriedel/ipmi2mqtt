FROM python:3.10-alpine
WORKDIR /app
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

#COPY config.yaml config.yaml
COPY ipmi2mqtt.py ipmi2mqtt.py

#RUN apk add --no-cache curl jq wget \
#RUN apk add --no-cache curl jq wget tcpdump busybox avahi open-lldp openrc bash
#ENV INITSYSTEM on

CMD ["python3", "ipmi2mqtt.py"]
#ENTRYPOINT ["/bin/sh"]
