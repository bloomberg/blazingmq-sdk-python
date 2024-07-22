.. py:currentmodule:: blazingmq


Examples
##################


Producer
=================================

A complete example of a program that posts a message and waits for it to be acknowledged
by the broker.

Note that ``on_ack`` is an optional argument. However, receiving acknowledgment is the only
way to guarantee that your message was received by the broker. In this example, messages are sent
in a fully synchronous fashion - the program waits for an acknowledgement before terminating.

.. literalinclude:: ../examples/producer.py

Producer with Correlation ID
=================================

A complete example of a program that posts a series of messages with
identifiers that can be used to correlate the Ack or Nack from the broker with
the posted message.

Unlike the BlazingMQ C++ SDK, which has a concept “correlation id”, which can
be provided with every posted message and will be provided back to the producer
with an Ack or Nack from the broker, the BlazingMQ Python SDK does not provide
this as a first-class notion.  Instead, in Python, a different ``on_ack``
callback can be provided on each posted message, storing arbitrary data in its
closure.  Using ``functools.partial``, we can construct these lightweight
callback closures to add a correlation id, or any arbitrary identifying data.

.. literalinclude:: ../examples/producer_with_correlation.py

Consumer with `threading.Event`
=================================

A complete example of a program that consumes messages from a BlazingMQ
queue. The main thread is blocked waiting for `threading.Event` to be set upon
receiving ``SIGTERM``, while incoming messages are processed in the callback on
the BlazingMQ event handler thread.

.. literalinclude:: ../examples/consumer.py

Consumer with `queue.Queue`
=================================

Correct synchronization may be difficult to implement. It sometimes helps to use the
Python standard library `queue.Queue`. The following example consumes messages from
a BlazingMQ queue and uses `queue.Queue` for synchronization.

The main thread is blocked in a `Queue.get <queue.Queue.get>` while all new messages are immediately
added to the in-process queue. There will be no more than ``max_unconfirmed_messages``
in the in-process queue at any given time (unless more than ``max_unconfirmed_bytes``
was received first) because the broker will pause delivery once
this value has been reached. Once ``SIGTERM`` is received, a sentinel object is added to
the in-process queue; all BlazingMQ messages received after the signal will be ignored.

Also note that, in this example, we provide ``suspends_on_bad_host_health=True``
when we open the queue. This stops the queue from receiving messages if the
machine is marked unhealthy, so that we don't unintentionally process a message
on an unhealthy machine.

.. literalinclude:: ../examples/consumer2.py
