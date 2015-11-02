#!/usr/bin/env python

import sys
from taaster.worker import *
import argparse

parser = argparse.ArgumentParser(description='Process some integers.')
parser.add_argument(
        '-a',
        '--amqp',
        default="localhost:5672",
        type=str,
        help='list for rabbitmq servers'
        )
parser.add_argument(
        '-q',
        '--queue',
        default="taas.test_queue",
        type=str,
        help='rabbitmq queue name'
        )
parser.add_argument(
        '-s',
        '--store',
        default="localhost:8081",
        type=str,
        help='log api url'
        )

args = parser.parse_args()
print("Start worker... logapi at %s, amqp at %s:%s" % (args.store, args.amqp, args.queue))

# exit(0)
def main():
    couchdb_host, couchdb_port = args.store.split(":")
    amqp_host, amqp_port = args.amqp.split(":")
    worker = TaasWorker(
            couchdb_host = couchdb_host,
            couchdb_port = int(couchdb_port),
            amqp_host = amqp_host,
            amqp_port = int(amqp_port),
            amqp_queue = args.queue
            )
    worker.run_forever()

if __name__ == '__main__':
    main()
