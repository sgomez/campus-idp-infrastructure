#!/usr/bin/env python3

import os
import pika
import time
import base64
import sys
import urllib
import json
from createIdPshib import createIdPshib


rabbitmqUser = os.environ.get('RABBITMQ_DEFAULT_USER')
rabbitmqPassword = os.environ.get('RABBITMQ_DEFAULT_PASS')
rabbitmqVhost = os.environ.get('RABBITMQ_VHOST', '/')
rabbitmqHost = os.environ.get('RABBITMQ_HOST', 'rabbitmq')
rabbitmqPort = 5672

# path to script provided by Marco
ansibleTrigger = '/opt/ssss/sf'

defaults = {'src': None, 'status_endpoint': None,
            'apitoken': None, 'qtoken': None}


# finalcallback method is triggered every time when new task is received

def finalcallback(ch, method, properties, payload):
    # setting default as incorrect input
    correctData = False
    print("")
    print("######  NEW TASK ##################")
    print(" [x] Received %r" % payload)
#    time.sleep(payload.count(b'.'))
    print(" [x] Decoding payload...")

    # try to parse payload as json
    try:
        data = json.loads(payload.decode("utf-8"))
        correctData = True
        print(" [x] Payload Loaded")
    except Exception as e:
        # if payload is incorrect raise exception and remove task from rabbitmq server
        ch.basic_ack(delivery_tag=method.delivery_tag)
        print(" [ERR] Invalid payload :  {} ".format(e))

    if correctData:
        print(" [x] Proceeding with payload")
        print("XXXXXXXXXXXXXXXXXXXX")
        print(data)
        print("XXXXXXXXXXXXXXXXXXXX")
        myData = defaults.copy()
        try:
            myData.update(data)
            print(' [x] -----------------')
            print(" [x] Final data: %r" % myData)
            print(' [x] -----------------')
            srcURL = myData['src']
            statusEndpoint = myData['status_endpoint']
            apiToken = myData['apitoken']
            qToken = myData['qtoken']

            # PUT createIdPShib HERE
            ansResult = createIdPshib(apiToken, qToken, srcURL, statusEndpoint)

        except Exception as e:
            ch.basic_ack(delivery_tag=method.delivery_tag)
            print("ERROR: could not update : {}".format(e))
    ch.basic_ack(delivery_tag=method.delivery_tag)
    print(" [x] Done")


# base64_url_decode method is not used at the moment
def base64_url_decode(inp):
    padding_factor = (4 - len(inp) % 4) % 4
    inp += "="*padding_factor
    return base64.b64decode(unicode(inp).translate(dict(zip(map(ord,
                                                                u'-_'), u'+/'))))


########### MAIN PROGRAMM ##########
#  it is running in infinite loop  #
####################################
while True:
    try:
        credentials = pika.PlainCredentials(rabbitmqUser, rabbitmqPassword)
        connection = pika.BlockingConnection(pika.ConnectionParameters(host=rabbitmqHost,
                                                                       port=rabbitmqPort,
                                                                       credentials=credentials,
                                                                       virtual_host=rabbitmqVhost))
        channel = connection.channel()
        channel.queue_declare(queue='ansibletrigger', durable=True)
        print(' [*] Waiting for messages. To exit press CTRL+C')
        channel.basic_qos(prefetch_count=1)
        channel.basic_consume(
            'ansibletrigger', on_message_callback=finalcallback)
        channel.start_consuming()
    except pika.exceptions.AuthenticationError:
        print("AuthenticationError")
    except pika.exceptions.ConnectionClosed:
        print("ConnectionClosed .. trying to reconnect")
        time.sleep(2)
