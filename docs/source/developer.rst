Developer
#########


Architecture
************

You will need to implement your new service with this architecture:

.. graphviz::

   digraph Workflow {

        "ServiceMixin" -> "ReceiverMixin"
        "ServiceMixin" -> "SenderMixin"
        "ReceiverMixin" -> "NewReceiverService"
        "SenderMixin" -> "NewSenderService"
   }


Main Classes
************

Interfaces
==========

.. autoclass:: src.ser.common.itf.publication.Publication


Mixins
======

.. autoclass:: src.ser.common.service_mixin.ServiceMixin

.. autoclass:: src.ser.common.receiver_mixin.ReceiverMixin

.. autoclass:: src.ser.common.sender_mixin.SenderMixin


Enums
=====

.. autoclass:: src.ser.common.enums.environment.Environment
   :members:


Testing
*******

Run application
===============

.. code-block:: shell

   pipenv run run

Force environment
=================

You can switch your environment without changing your configuration file. See next code:

.. code-block:: shell

   pipenv run run --environment <environment>
