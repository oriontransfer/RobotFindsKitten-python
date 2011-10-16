#!/usr/bin/env python
import socket, sys, string, select;

# (tcp|udp)://(client|server)@192.168.2.1:2828
type = socket.SOCK_STREAM
host = "127.0.0.1"
port = 1313
lval, rval = string.split (sys.argv[1], ":", 1)

if lval is "udp":
	type = socket.SOCK_DGRAM

if lval == "tcp" or lval == "udp":
    lval, rval = string.split (rval[2:], ":", 1)

connection, host = string.split(lval, "@")
port = int(rval)

if connection == "server":
    print "listening on " + host + ":" + `port`
    ssoc = socket.socket (socket.AF_INET, type)
    ssoc.bind ((host, port))
    ssoc.listen (1)
    soc, addr = ssoc.accept()
    ssoc.close();
else:
    print "connecting to " + host + ":" + `port`
    soc = socket.socket (socket.AF_INET, type)
    soc.connect ((host, port))

try:
    run = True
    while run:
        check = select.select ([soc.fileno(), sys.stdin.fileno()], [], [soc.fileno()])
        if len(check[2]):
            sys.stderr.write ("a remote exception occurred");
            sys.exit(1)
        if check[0][0] == soc.fileno():
            buf = soc.recv (1024)
            if len(buf) == 0:
                sys.stderr.write ("the remote host closed the socket")
                soc.close()
                sys.exit (0)
            sys.stdout.write(buf);
        if len(check[0]) == 2 or check[0][0] == sys.stdin.fileno():
            bf = string.strip(sys.stdin.readline()) + "\r\n";
            soc.send (bf);
except KeyboardInterrupt:
    print sys.stderr.write("disconnecting..");

soc.close();