QuickStart
##########

1. `Create configuration file`_
2. `Create application environment`_

   * `Run docker image`_
   * `Create your own environment`_


Create configuration file
*************************

Configuration file is a yaml that must be named `config.yaml`. This file must be saved on
`/etc/gabriel-messenger/config.yaml`

See next example:

.. include:: config.yaml
   :literal:

You can download this example :download:`here <config.yaml>`.

Create application environment
******************************

Currently the are two main ways to execute this app:

* `Run docker image`_
* `Create your own environment`_

The easy way to use this app is `run docker image`_.

Run docker image
==================

This method is the easy way. `Docker image <https://hub.docker.com/r/guibos/gabriel-messenger>`_ will be update of
every gabriel-messenger update.

Install docker
--------------
You must install `docker <https://docs.docker.com/get-docker/>`_.

Run container
-------------
.. code-block:: shell

   docker run -v <your-configuration-directory>:/etc/gabriel-messenger guibos/gabriel-messenger

Take care that `<your-configuration-directory>` is a directory in your docker host with your `config.yaml`

Create your own environment
===========================

Use this Dockerfile as an idea that you will need:

.. include:: ../../Dockerfile
   :literal:
