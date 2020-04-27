Modules
#######

Sender Services
***************

WhatsApp Web
============
WhatsApp Web Module uses WhatsApp Web service to communicate with your cellphone through a web browser.

Do not use this module if you need high availability. If you require high availability see:
`WhatsApp API <https://www.whatsapp.com/business/api>`_. This module is subject to problems of all kinds.
This module is intended for those individuals, companies or associations that cannot cover the expenses of
`WhatsApp API <https://www.whatsapp.com/business/api>`_.

Features
--------
This module allow:

* Send text messages
* Send images
* Send files
* Send with different cellphone numbers.

This module not allow:

* Send videos

Configuration
-------------

.. include:: _static/config_whatsapp.yaml
   :literal:

"Guibos" and "Gabriel" will be different instance of WhatsApp Web module. Previous key don't have any special meaning.
These keys are used by Receiver Services to discriminate different instances. Each instance will have his own web
browser configuration. In each instance you must add QR code on startup. For now you will disable headless mode to add
new. Each instance must have configured different cellphone numbers.

Technical Notes
---------------
This module uses `pyppeteer2 <https://github.com/pyppeteer/pyppeteer2>`_. This library is async, that work with
chromium browser. `Pyppeteer2 <https://github.com/pyppeteer/pyppeteer2>`_ controls chromium browser through
`websockets <https://www.w3.org/TR/2009/WD-websockets-20091222/>`_.
This module simulate what is doing a person when he interact with WhatsApp Web. To chose a html element,
`selectors <https://www.w3.org/TR/selectors-api/>`_ are used.

Class
-----

.. autoclass:: src.ser.whats_app_web.service.WhatsAppWebService
   :members:

Flowchart
---------

.. graphviz::

    digraph process {
        get_publication [label="Get publication from queue"];
        deep_copy [label="Create a deep copy from Publication"];
        clean_channel [label="Clean text of search channel"];
        type_channel [label="Type channel name \n into Search Box"];
        click_channel [label="Click channel"];
        there_are_files [label="There are files?"];
        attach_file [label="Attach file"];
        send_file [label="Send File"];
        there_are_images [label="There are images?,\n except the first one"];
        attach_image [label="Attach File"];
        send_image [label="Send Image"];
        there_are_first_image_text [label="There are first image\n or text to send?"];
        there_are_first_image [label="There are first image?"];
        attach_first_image [label="Attach image"];
        there_are_text [label="There are text?"];
        type_text [label="Type text"];
        send_message [label="Send message"];
        raised_exception [label="Raised Exception"];
        session_closed [label="Session Closed: User closed session \n from his cellphone or session is expired"];
        another_usage [label="WhatsApp is open in another window: \n User is using WhatsApp Web"];

        get_publication -> deep_copy;
        deep_copy -> clean_channel;
        raised_exception -> session_closed;
        raised_exception -> another_usage;
        another_usage -> clean_channel [label="Re:Zero"];
        session_closed -> clean_channel [label="Re:Zero"];
        clean_channel -> type_channel;
        type_channel -> raised_exception [label="error"];
        type_channel -> click_channel;
        click_channel -> raised_exception [label="error"];
        click_channel -> there_are_images;
        there_are_images -> attach_image [label=yes];
        attach_image -> raised_exception [label=error];
        attach_image -> send_image;
        send_image -> remove_image;
        remove_image -> there_are_images;
        there_are_images -> there_are_first_image_text;
        there_are_first_image_text -> get_publication [label=no];
        there_are_first_image_text -> there_are_first_image [label=yes];
        there_are_first_image -> attach_first_image [label=yes];
        there_are_first_image -> there_are_text [label=no];
        attach_first_image -> raised_exception [label="error"];
        attach_first_image -> there_are_text;
        there_are_text -> type_text [label="yes"];
        there_are_text -> send_message [label=no];
        type_text -> raised_exception [label=error];
        type_text -> send_message;
        send_message -> raised_exception [label=error];
        send_message -> there_are_files;
        there_are_files -> attach_file [label=yes];
        attach_file -> raised_exception [label=error];
        attach_file -> send_file;
        send_file -> remove_file;
        remove_file -> there_are_files;
        there_are_files -> get_publication [label="Publication sent"];
    }


Receiver Services
*****************

Recycler
========

Recycler service get publications from config and send one of them between time specified in `wait_time` field. Take
care that *Recycler Service* create a instance for each of items of the main list. So you can send different
publications to different *Senders Services* and different recipients.

Configuration
-------------

.. include:: _static/config_recycler.yaml
   :literal:

Module config have a list of publications. Is not necessary to complete all fields.
