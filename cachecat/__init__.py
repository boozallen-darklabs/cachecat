"""

First, install **cachecat** using pip.

.. code-block:: bash

    # Install cachecat
    $ git clone https://github.com/boozallen-darklabs/cachecat
    $ pip3 install -e ./cachecat

Once installed, the :code:`cachecat` bash command should become available.
:code:`cachecat` is designed to feel like :code:`netcat` as a means to
connect clients together over a network. In this case, you can use
:code:`cachecat` to connect clients to a *channel* on a vulnerable
web cache and exchange data.

.. code-block:: bash

    # Connect first client to the cache server on channel 100
    $ cachecat -u https://webcachetunneling.com/ -k q -c 100 -v

    # Connect second client and send data from stdin
    $ cachecat -u https://webcachetunneling.com/ -k q -c 100
    Hello,
    world!

"""

import logging
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
