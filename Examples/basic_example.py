import asyncio
import pika
import logging
import datetime
from PikaBus.abstractions.AbstractPikaBus import AbstractPikaBus
from PikaBus.abstractions.AbstractPikaBusSetup import AbstractPikaBusSetup
from PikaBus.PikaBusSetup import PikaBusSetup

logging.basicConfig(format=f'[%(levelname)s] %(name)s - %(message)s', level='WARNING')


def MessageHandlerMethod(**kwargs):
    """
    A message handler method may simply be a method with som **kwargs.
    The **kwargs will be given all incoming pipeline data, the bus and the incoming payload.
    """
    data: dict = kwargs['data']
    bus: AbstractPikaBus = kwargs['bus']
    payload: dict = kwargs['payload']
    print(payload)
    if payload['reply']:
        payload['reply'] = False
        bus.Reply(payload=payload)


# Use pika connection params to set connection details
credentials = pika.PlainCredentials('amqp', 'amqp')
connParams = pika.ConnectionParameters(
    host='localhost',
    port=5672,
    virtual_host='/',
    credentials=credentials)

# Create a PikaBusSetup instance with a listener queue, and add the message handler method.
pikaBusSetup: AbstractPikaBusSetup = PikaBusSetup(connParams,
                                                  defaultListenerQueue='myQueue',
                                                  defaultSubscriptions='myTopic')
pikaBusSetup.AddMessageHandler(MessageHandlerMethod)

# Start consuming messages from the queue.
consumingTasks = pikaBusSetup.StartAsync()

# Create a temporary bus to subscribe on topics and send, defer or publish messages.
bus: AbstractPikaBus = pikaBusSetup.CreateBus()
bus.Subscribe('myTopic')
payload = {'hello': 'world!', 'reply': True}

# To send a message means sending a message explicitly to one receiver.
bus.Send(payload=payload, queue='myQueue')

# To defer a message means sending a message explicitly to one receiver with some delay before it is processed.
bus.Defer(payload=payload, delay=datetime.timedelta(seconds=1), queue='myQueue')

# To publish a message means publishing a message on a topic received by any subscribers of the topic.
bus.Publish(payload=payload, topic='myTopic')

input('Hit enter to stop all consuming channels \n\n')
pikaBusSetup.Stop()

# Wait for the consuming tasks to complete safely.
loop = asyncio.get_event_loop()
loop.run_until_complete(asyncio.gather(*consumingTasks))