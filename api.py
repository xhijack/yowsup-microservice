from datetime import datetime
from flask import Flask, request
from flasgger import Swagger
from flask_cors import CORS
from nameko.standalone.rpc import ClusterRpcProxy
from flasgger.utils import swag_from
from flask import request
from pymongo import MongoClient
import logging
import os

from whitelist import ips

app = Flask(__name__)
CORS(app)
Swagger(app)

# CONFIG = {'AMQP_URI': "pyamqp://guest:guest@localhost"}
CONFIG = {'AMQP_URI': "amqp://ntjuoyrh:S5mrn6IUnwfzrUaqvPsJ-K60FA9CuFog@skunk.rmq.cloudamqp.com/ntjuoyrh"}

client = MongoClient('mongodb://wa_ramdani:wa_ramdani@ds121999.mlab.com:21999/whatsapp-messages')

db = client['whatsapp-messages']


@app.route('/send', methods=['POST'])
@swag_from('docs/send.yml')
def send():

    ip_number = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
    # if ip_number in ips:
    logger = app.logger
    type = request.json.get('type')
    body = request.json.get('body')
    address = request.json.get('address')

    if not db.messages.find_one({'toNumber': address, 'message': body}):
        logger.info('Get message: %s,%s,%s' % (type, body, address))

        db.messages.insert_one({
            'toNumber': address,
            'message': body,
            'ip': ip_number,
            'created': datetime.now()
        })

        with ClusterRpcProxy(CONFIG) as rpc:
            # asynchronously spawning and email notification
            rpc.yowsup.send(type, body, address)

    msg = "The message was sucessfully sended to the queue"
    return msg, 200
    # else:
    #     return "Silakan hanya menggunakan halaman resmi kami", 401


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80)
