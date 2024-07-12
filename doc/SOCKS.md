**Brief Introduction of SOCKS**

 **SOCKS** is n Internet protocol to exchanges network packets between a client and server through a proxy server. Works between application layer and the transport layer. On TCP port `1080`

**SOCKS5** provides ==authentication== and ==UDP== transmission and support ==IPV6== compared to former version of SOCKS.

**What can SOCKS do?**

- Circumvention tool. Bypass Internet filtering to access contents that are blocked.
- VPN

# Procedure for TCP

When a TCP based client wishes to establish connection with a server only reachable via a firewall:

1. Client open a TCP connection with SOCKS program on SOCKS server system.
2. Client sends a request to choose the authentication method.
    +----+----------+----------+
    |VER | NMETHODS | METHODS  |
    +----+----------+----------+
    | 1  |    1     | 1 to 255 |
    +----+----------+----------+
    VER is set to `5` for this version. NMETHODS denotes the number of bytes in METHODS.
3. Server select the one method from the request message and respond with another message:
    +----+--------+         
    |VER | METHOD |
    +----+--------+
    | 1  |   1    |
    +----+--------+
    o  X'00' NO AUTHENTICATION REQUIRED
    o  X'01' GSSAPI
    o  X'02' USERNAME/PASSWORD
    o  X'03' to X'7F' IANA ASSIGNED
    o  X'80' to X'FE' RESERVED FOR PRIVATE METHODS
    o  X'FF' NO ACCEPTABLE METHODS, close connection
4. If connection not closed, client and server enter a method specific sub-negotiation.
5. After the method-dependent subnegotiation, client sends the specific request in the following format:
    +----+-----+-------+------+----------+----------+
    |VER | CMD |  RSV  | ATYP | DST.ADDR | DST.PORT |
    +----+-----+-------+------+----------+----------+
    | 1  |  1  | X'00' |  1   | Variable |    2     |
    +----+-----+-------+------+----------+----------+
    o  VER    protocol version: X'05'
    o  CMD
        o  CONNECT X'01'
        o  BIND X'02'
        o  UDP ASSOCIATE X'03'
    o  RSV    RESERVED
    o  ATYP   address type of following address
        o  IPV4 address: X'01'
        o  DOMAINNAME: X'03'
        o  IPV6 address: X'04'
    o  DST.ADDR       desired destination address
    o  DST.PORT desired destination port in network octet
        order
6. SOCKS server establishes connection with destination server.
6. SOCKS server return reply messages.
    +----+-----+-------+------+----------+----------+
    |VER | REP |  RSV  | ATYP | BND.ADDR | BND.PORT |
    +----+-----+-------+------+----------+----------+
    | 1  |  1  | X'00' |  1   | Variable |    2     |
    +----+-----+-------+------+----------+----------+
    o  REP    Reply field:
        o  X'00' succeeded
        o  X'01' general SOCKS server failure
        o  X'02' connection not allowed by ruleset
        o  X'03' Network unreachable
        o  X'04' Host unreachable
        o  X'05' Connection refused
        o  X'06' TTL expired
        o  X'07' Command not supported
        o  X'08' Address type not supported
        o  X'09' to X'FF' unassigned
    o  BND.ADDR       server bound address
    o  BND.PORT       server bound port in network octet order
7. If the reply indicates a failure, the SOCKS server will terminate the connection after sending the reply. If it indicates a success, the client should start passing data. And the server will send data to SOCKS server and then passed to client.

**CMD**

- CONNECT: SOCKS server will reply with the port number that server assigned to connect to the target host and the associated IP address.
- BIND: Used in protocols which require client to accept connections from the server side.(FTP) use the BIND request only to establish secondary connections after aprimary connection is established using CONNECT.

**Two replies** will be sent when using BIND.

First is sent after the SOCKS server binds a new socket for listening incoming connections with the port number and IP address of the socket. 

Client use these info to tell the destination server where to establishes connection with SOCKS server.

The secondary will be sent only after the anticipated incoming connection between SOCKS and dest server succeeds or fails. Reply with port number and address of the connecting host.

> 为什么BIND有两次回复? 为什么SOCKS服务器不直接把新连接的端口直接发送给目标服务器, 而是发给客户端, 再让客户端通过主连接发送给目标服务器?
> 灵活性和控制：客户端可能需要在通知应用服务器之前执行一些操作，比如日志记录、额外的安全检查或更新用户界面。通过先通知客户端，客户端可以根据具体情况进行处理。
> 统一的通信通道：SOCKS协议设计目的是提供一个统一的代理机制。所有通信都通过SOCKS服务器中转，确保安全和一致性。如果SOCKS服务器直接通知应用服务器，会破坏这种统一性，并可能导致安全问题。
> 复杂性和适应性：直接通知应用服务器会增加SOCKS服务器的复杂性，因为它需要适应各种不同的应用协议和通信模式。通过客户端中转，SOCKS服务器保持简单，只需处理基本的连接和转发任务。

## socketServer in Python

`class socketserver.TCPServer(server_address, RequestHandlerClass, bind_and_activate=True)`
This uses the internet TCP protocol, which provides for continuous streams of data between the client and server. If `bind_and_activate` is true, the constructor automatically attempts to invoke server_bind() and server_activate(). The other parameters are passed to the BaseServer base class.

本身是同步处理, 如果需要异步处理需要使用`ThreadingMixIn`类

创建server步骤:
1. create a request handler class by subclassing `BaseRequestHndler` and overriding the `handle()` method.
2. instantiate a serverSocket object, and then call the `serve_forever()` or `handle_request()` method.
> handle_request process only a single request;
> serve_forever will handle requests until `shutdown()` is called.

**异步处理:**

创建一个server类同时继承`ThreadingMixIn`和`TCPServer`, **注意**要按照这个顺序继承, 因为ThreadingMixIn重写了TCPServer里的方法

```py
class ThreadingTCPServer(ThreadingMixIn, TCPServer):
    pass
```

ThreadingMixIn中两个关键属性:
- daemon_threads: True则当主线程退出时, 会直接退出, 不会因为其他线程还在处理而等待, 默认为false 控制线程生命周期
- block_on_close: True则服务器会在关闭时先等待所有线程处理完请求再退出, 默认为false 控制请求的处理

**server class:**

**attributes**: 
- server_address:(ipaddres, portnumber)
- RequestHndlerClass: user-provided request handler class

**methods:**
- handle_request(): process a single request, use the `handle()` provided by `RequestHandlerClass`
- serve_forever(): handle requests until `shutdown()` is called. 
- shutdown(): tell the serve_forever() loop to stop and wait until it does. shutdown() must be called while serve_forever() is running in a different thread otherwise it will deadlock.

**handler class: **

**methods:**
- handle(): do all the work requered to service a request. subclass must implement this method.

for `StreamRequestHandler` and `DatagramRequestHandler`:
- rfile: file object used to receive request
- wfile: file object used to write a reply

相比于Base handler, 这两个subclass handler提供流式处理, base就只能像普通socket一样使用recv和send
eg.
```py
import socketserver

class MyTCPHandler(socketserver.BaseRequestHandler):
    """
    The request handler class for our server.

    It is instantiated once per connection to the server, and must
    override the handle() method to implement communication to the
    client.
    """

    def handle(self):
        # self.request is the TCP socket connected to the client
        self.data = self.request.recv(1024).strip()
        print("Received from {}:".format(self.client_address[0]))
        print(self.data)
        # just send back the same data, but upper-cased
        self.request.sendall(self.data.upper())

if __name__ == "__main__":
    HOST, PORT = "localhost", 9999

    # Create the server, binding to localhost on port 9999
    with socketserver.TCPServer((HOST, PORT), MyTCPHandler) as server:
        # Activate the server; this will keep running until you
        # interrupt the program with Ctrl-C
        server.serve_forever()
```
with `StreamRequestHandler`:
```py
class MyTCPHandler(socketserver.StreamRequestHandler):

    def handle(self):
        # self.rfile is a file-like object created by the handler;
        # we can now use e.g. readline() instead of raw recv() calls
        self.data = self.rfile.readline().strip()
        print("{} wrote:".format(self.client_address[0]))
        print(self.data)
        # Likewise, self.wfile is a file-like object used to write back
        # to the client
        self.wfile.write(self.data.upper())
```

Using MixIn for asynchronous handler:

```py


```

# Procedure for UDP