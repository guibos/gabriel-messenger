QuickStart
##########

Create configuration file
*************************

Configuration file is a yaml that must be named `config.yaml`. This file must be saved on
`/etc/gabriel-messenger/config.yaml`

See next example:

.. include:: _static/config.yaml
   :literal:

You can download this example :download:`here <_static/config.yaml>`.

* **Configuration**: Global configuration. This not change between environments.

  * **Environment**

* **Environment**: Node that save all environments.

  * **Environment node**: To know what environment are available, check this: :py:meth:`src.ser.common.enums.environment.Environment`

    * **Sender Section**: (Sender) This section save all configuration of each *Sender Service*. If you are not interested to load some *Sender Service*, not write (or comment) his sender section.

      * **Sender Configuration**: (In this case WhatsApp Web) This configure a sender service if you want to know how to configure each *Sender Service* check this document :doc:`Modules <../modules>`.

    * **Receiver Section**: This section save all configuration of each *Receiver Service*. If you are not interested to load some *Receiver Service*, not write (or comment) his sender section.

      * **Senders**: Section where is configured where publications will be send.

        * **Sender Service Name**: (In this case WhatsApp Web) will be the same as **Sender Configuration** Key.

          * **Channel name or channel id**: (In this case "Guibos" or "Gabriels") Is a id or str of a channel or group that you want send publications. To get more information for each sender service check: :doc:`Modules <../modules>`.

            * **publication_data**: This data will add or replace values of a publication. In previous example uses title replacement or title adding. :py:meth:`src.ser.common.itf.publication.Publication`

        * **module_config**: Configuration of the *Receiver Module*. To get more information for each receiver service check: :doc:`Modules <../modules>`.

Good Practices
==============

One of the biggest practise is create yaml anchors to avoid duplicated configuration.

.. include:: _static/yaml_anchors.yaml
   :literal:

For more information this `document <http://blogs.perl.org/users/tinita/2019/05/reusing-data-with-yaml-anchors-aliases-and-merge-keys.html>`_ is a good reference.


Create application environment
******************************

Currently the are two main ways to execute this app:

* `Run a docker image`_
* `Create your own environment`_

The easy way to use this app is `run a docker image`_.

Run a docker image
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
