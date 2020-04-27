Documentation
#############

Definitions
***********

* **Publication**: A publication is a dataclass that includes all the information necessary to generate an entry on any social network. A publication will be shared by a **receiver service** to n ***sender services***.
* **Service**: A service is a utility that allow to manage publications in some way. There are two types of services: "**Receivers**" and "**Senders**".

  * **Receiver Service**: A service that download information from external resources and generate publications. This publications will be upload in configured queues of **sender services**.
  * **Sender Service**: A service that get publications from his queue and publish to external resource.

* **Task**: Tasks are used to schedule coroutines concurrently. See: `asyncio task <https://docs.python.org/3/library/asyncio-task.html>`_.

  * All services will generate one or more task (normally one) to perform his functionality.
  * Other tasks: to manage state of services. Currently only to perform shutdown of all services. See next code:

.. autoclass:: src.app.application.Application
    :members: _clean_shutdown


Workflow
********

.. graphviz::

   digraph Workflow {
        "Ext Resource rA" -> "Receiver rA";
        "Receiver rA" -> "Queue s1";
        "Receiver rA" -> "Queue s2";
        "Ext Resource rB" -> "Receiver rB";
        "Receiver rB" -> "Queue s1";
        "Receiver rB" -> "Queue s2";
        "Receiver rB" -> "Queue sN";
        "Ext Resource rN" -> "Receiver rN";
        "Receiver rN" -> "Queue sN";
        "Queue s1" -> "Sender s1";
        "Sender s1" -> "Ext Resource s1";
        "Queue s2" -> "Sender s2";
        "Sender s2" -> "Ext Resource s2";
        "Queue sN" -> "Sender sN";
        "Sender sN" -> "Ext Resource sN";
   }

Each **receiver Service** download data from external resource, create publications with this data and send this publications to each queue configured. One queue, one *Sender Service*. Sender get publications from his queue and send to external resource.
