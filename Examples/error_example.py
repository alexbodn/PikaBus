import asyncio
import pika
from PikaBus.abstractions.AbstractPikaBus import AbstractPikaBus
from PikaBus.PikaBusSetup import PikaBusSetup
from PikaBus.PikaErrorHandler import PikaErrorHandler


def failingMessageHandlerMethod(**kwargs):
    """
    A message handler method may simply be a method with som **kwargs.
    The **kwargs will be given all incoming pipeline data, the bus and the incoming payload.
    """
    data: dict = kwargs['data']
    bus: AbstractPikaBus = kwargs['bus']
    payload: dict = kwargs['payload']
    print(payload)
    raise Exception("I'm just failing as I'm told ..")


# Use pika connection params to set connection details
credentials = pika.PlainCredentials('amqp', 'amqp')
connParams = pika.ConnectionParameters(
    host='localhost',
    port=5672,
    virtual_host='/',
    credentials=credentials)

# Create a PikaBusSetup instance with a listener queue and your own PikaErrorHandler definition.
pikaErrorHandler = PikaErrorHandler(errorQueue='error', maxRetries=1)
pikaBusSetup = PikaBusSetup(connParams,
                            defaultListenerQueue='myFailingQueue',
                            pikaErrorHandler=pikaErrorHandler)
pikaBusSetup.AddMessageHandler(failingMessageHandlerMethod)

# Start consuming messages from the queue.
consumingTasks = pikaBusSetup.StartAsync()

# Create a temporary bus to subscribe on topics and send, defer or publish messages.
bus = pikaBusSetup.CreateBus()
payload = {'hello': 'world!', 'reply': True}

# To send a message means sending a message explicitly to one receiver.
# In this case the message will keep failing and end up in an dead-letter queue called `error`.
# Locate the failed message in the `error` queue at the RabbitMq admin portal on http://localhost:15672 (user=amqp, password=amqp)
bus.Send(payload=payload, queue='myFailingQueue')

input('Hit enter to stop all consuming channels \n\n')
pikaBusSetup.Stop()

# Wait for the consuming tasks to complete safely.
loop = asyncio.get_event_loop()
loop.run_until_complete(asyncio.gather(*consumingTasks))