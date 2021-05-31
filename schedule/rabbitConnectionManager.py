from pika.exceptions import StreamLostError
from json import dumps
import pika


class RabbitConnectionManager:
    """ Object for managing a RabbitMQ connection.

        This class uses the pika module to interact with an instance of RabbitMQ.

        Args:
            rabbitConnStr       (str):     Connection string for connecting to a RabbitMQ instance.
            rabbitQueueName     (str):     Name of the RabbitMQ queue to connect to.
            durable             (bool):    Whether or not the Queue is registered as durable.
    """

    def __init__(self, rabbitConnStr, rabbitQueueName, durable=False):

        # RabbitMQ Connection string
        self.__rabbitConnStr = rabbitConnStr

        # RabbitMQ Queue name
        self.rabbitQueueName = rabbitQueueName

        # Connection durability
        self.__isDurable = durable

        # Establish the connection to the RabbitMQ instance
        self.__rabbitConn, self.__channel = self.connectToRabbitMQ(
            self.__rabbitConnStr,
            self.rabbitQueueName,
            self.__isDurable
        )

        # A retry count
        self.publishRetryCount = 0

    def connectToRabbitMQ(self, rabbitConnStr, rabbitQueueName, durable=False):
        # Connect to the RabbitMQ instance that should be used in this session.

        # TODO: Add error handling in case RabbitMQ cannot be reached

        # Parse the URL parameters from the connection url
        params = pika.URLParameters(rabbitConnStr)

        # Create a blocking connection with the parsed parameters
        rabbitConn = pika.BlockingConnection(params)

        # Start a channel
        channel = rabbitConn.channel()

        # Connect to the desired queue
        channel.queue_declare(
            queue=rabbitQueueName,
            durable=durable
        )

        # Return the connection and channel to the caller.
        return rabbitConn, channel

    def isConnectionOpen(self):
        # Return True if the RabbitMQ connection is open.
        return self.__rabbitConn.is_open

    def closeConnection(self):
        # Close the RabbitMQ connection
        self.__rabbitConn.close()

    def publishMsg(self, msgBody, headers, deliveryMode=1):
        # Publish a message to the queue.

        # TODO: add error handling in case we cannot publish

        # Check to see if the RabbitMQ connection is still open
        if not self.isConnectionOpen():
            # Re-establish the connection to the RabbitMQ instance
            self.__rabbitConn, self.__channel = self.connectToRabbitMQ(self.__rabbitConnStr, self.rabbitQueueName)

        try:
            # Publish the message to the queue
            self.__channel.basic_publish(
                exchange="",
                routing_key=self.rabbitQueueName,
                # Convert the msgBody to a JSON string and encode it in a byte array for pika
                body=bytes(dumps(msgBody), "utf-8"),
                properties=pika.BasicProperties(
                    headers=headers,
                    delivery_mode=deliveryMode
                )
            )

            # Reset the publish attempt count
            self.publishRetryCount = 0

        except StreamLostError:
            # There was a connection interruption.

            # If we haven't attempted to retry the message
            if self.publishRetryCount < 1:
                # Increment the retry count
                self.publishRetryCount += 1
                # Attempt to publish the message again
                self.publishMsg(msgBody, headers)

            else:
                # If we have run through all of our retry attempts
                #  then return False, indicating that there was an
                #  issue.
                return False

        # If we were able to successfully queue the message, return True
        return True

    def consumeMessages(self, callbackFunction, rabbitQueueLimit=1):
        # Begin consuming messages over the RabbitMQ connection

        # TODO: Add error handling in case we cannot consume

        # Check to see if the RabbitMQ connection is still open
        if not self.isConnectionOpen():
            # Re-establish the connection to the RabbitMQ instance
            self.__rabbitConn, self.__channel = self.connectToRabbitMQ(self.__rabbitConnStr, self.rabbitQueueName)

        self.__channel.basic_consume(
            self.rabbitQueueName,
            callbackFunction
        )

        # Configure the channel so that RabbitMQ does not send a given worker process
        #  more than 'rabbitSchedulerQueueLimit' number of messages at a time.
        #  https://www.rabbitmq.com/tutorials/tutorial-two-python.html
        self.__channel.basic_qos(
            prefetch_count=rabbitQueueLimit
        )

        # Start consuming
        self.__channel.start_consuming()
