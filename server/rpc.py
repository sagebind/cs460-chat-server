import json
import logging
import socket
import threading


"""
Exception thrown if the peer sends an error.
"""
class RpcException(Exception):
    pass


"""
Connects to a remote RPC peer.
"""
def connect(address, port, handler, timeout=5):
    connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    connection.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
    connection.settimeout(timeout)
    connection.connect((address, port))

    listener = Listener(connection)
    return Proxy(listener, handler)


"""
Object that acts as a stub for remote methods.

A proxy object is usually created by calling connect() to connect to a remote
peer.

The proxy also acts as a state object for the current connection, since the
object lasts as long as the connection does.
"""
class Proxy:
    """
    Creates a new proxy object around the given listener.
    """
    def __init__(self, listener, handler):
        self.listener = listener
        self.listener.handler = handler(self) # Instantiate the handler class
        self.listener.start()
        self.id_counter = 0

    """
    Gets the name of the remote peer as a tuple of the address and port.
    """
    def get_peer_name(self):
        return self.listener.address

    """
    Calls a method on the peer.
    """
    def invoke(self, name, params = {}):
        request = {
            "jsonrpc": "2.0",
            "method": name,
            "params": params,
            "id": self.id_counter
        }
        self.id_counter += 1

        # Send the request and then read the response.
        self.listener.send(request)
        response = self.listener.receive_and_wait(request["id"])

        if "error" in response:
            raise RpcException(response["error"]["code"], response["error"]["message"])

        return response["result"]

    """
    Informs the peer that the connection is closing and then closes the socket.
    """
    def close(self):
        self.invoke("close")
        self.listener.close()

    """
    Provides syntax sugar for calling remote methods.
    """
    def __getattr__(self, name):
        def closure(**kwargs):
            return self.invoke(name, kwargs)

        return closure


"""
Wrapper around a socket that provides message parsing, writing, and background
reading.

Uses a dedicated thread for reading and handling incoming messages from the
remote peer.
"""
class Listener(threading.Thread):
    """
    Creates a new listener for a given socket.
    """
    def __init__(self, socket, timeout = 1.0, bufsize = 4096):
        threading.Thread.__init__(self)

        self.message_buffer = {}
        self.message_events = {}
        self.open = False
        self.socket = socket
        self.write_lock = threading.Lock()
        self.handler = None
        self.bufsize = bufsize

        socket.settimeout(timeout)
        self.address = socket.getpeername()

    """
    Receives a message with a given ID, waiting until it arrives.

    Returns the message as a dictionary.
    """
    def receive_and_wait(self, id, timeout=5.0):
        self.message_events[id] = threading.Event()

        # Block until the item in the buffer is accessible.
        if not self.message_events[id].wait(timeout):
            del self.message_events[id]
            raise Exception("Message timed out")

        # Get the message and remove it from the buffer.
        message = self.message_buffer[id]
        del self.message_events[id]
        del self.message_buffer[id]

        return message

    """
    Sends a message to the peer and waits for the response.
    """
    def send(self, message):
        self.write_lock.acquire()
        logging.info("Sending message to %s", self.address)

        # Serialize the message.
        serialized = json.dumps(message)
        # Send a packet ending in a magic byte package separator.
        self.socket.sendall(serialized.encode() + b"\0\0\0\0")
        self.write_lock.release()

    """
    Runs the listener, which reads from the peer forever until close() is called.
    """
    def run(self):
        # Set up a local byte buffer.
        buffer = bytearray()

        # Read forever until we are told to close.
        self.open = True
        while self.open:
            # Read some data from the peer when it arrives.
            try:
                packet = self.socket.recv(self.bufsize)
                buffer.extend(packet)
            except socket.timeout:
                continue
            except (ConnectionError, OSError):
                self.close()
                break

            if len(packet) == 0:
                self.close()
                break

            # Look for any complete messages in the buffer.
            while True:
                # Look for the "magic string" at the end of each message.
                pos = buffer.find(b"\0\0\0\0")
                if pos < 0:
                    break

                # Slice the correct portion out of the buffer.
                string = buffer[:pos].decode()
                del buffer[:pos + 4]

                # Parse the message as JSON.
                message = json.loads(string)
                logging.info("Received message from %s", self.address)

                if not "method" in message:
                    # If the message is a response, put it into the shared buffer and alert consumers.
                    # Make sure the ID is valid.
                    if not message["id"] in self.message_events:
                        logging.warning("Unknown reply ID %d", message["id"])
                    else:
                        self.message_buffer[message["id"]] = message
                        self.message_events[message["id"]].set()
                else:
                    # The message is a request, so handle it now.
                    threading.Thread(target=lambda: self._handle_request(message)).start()

        # Make sure the socket gets closed if we were asked politely to close.
        self.close()

    """
    Closes the listener politely whenever the loop runs around next.
    """
    def close_later(self):
        self.open = False

    """
    Closes the listener immediately.
    """
    def close(self):
        self.open = False
        self.write_lock.acquire()
        try:
            self.socket.shutdown(socket.SHUT_RDWR)
            self.socket.close()
        except OSError:
            pass
        finally:
            self.write_lock.release()

    def _handle_request(self, request):
        response = {
            "jsonrpc": "2.0",
            "id": request["id"]
        }

        # Attempt to invoke the requested method.
        try:
            # If the method is "close", close the connection.
            if request["method"] == "close":
                self.close_later()
                response["result"] = True

            # For any other method, invoke it on the handler.
            else:
                func = getattr(self.handler, request["method"])
                args = request["params"]
                return_val = func(**args)

                response["result"] = return_val
        except Exception as e:
            # Method errored, so respond with an error instead.
            response["error"] = {
                "code": 500,
                "message": str(e)
            }

        # Send back a response to the peer.
        self.send(response)


"""
Base class for handlers.
"""
class Handler:
    def __init__(self, proxy):
        self.proxy = proxy
