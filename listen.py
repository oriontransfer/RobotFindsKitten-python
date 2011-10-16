#!/usr/bin/env python
import socket, sys, string, select, metal;

# tcp|udp://192.168.2.1:2828
connect_type = socket.SOCK_STREAM;
connect_host = "127.0.0.1";
connect_port = 2468;
lval, rval = string.split (sys.argv[1], ":", 1)

if lval is "udp":
	connect_type = socket.SOCK_DGRAM;

if lval == "tcp" or lval == "udp":
    lval, rval = string.split (rval[2:], ":", 1);

connect_host = lval;
connect_port = int(rval);

print "connecting to " + connect_host + ":" + `connect_port`;

soc = socket.socket (socket.AF_INET, connect_type);
soc.bind ((connect_host, connect_port));
if (connect_type == socket.SOCK_STREAM):
    soc.listen (10);

soc = soc.accept ()[0];
try:
    run = True;
    while run:
        check = select.select ([soc.fileno(), sys.stdin.fileno()], [], [soc.fileno()]);
        if len(check[2]):
            print "a remote exception occurred";
            sys.exit(1);
        if check[0][0] == soc.fileno():
            buf = soc.recv (1024);
            if len(buf) == 0:
                print "the remote host closed the socket";
                soc.close();
                sys.exit (2);
#            print metal.hexdump (buf);
            sys.stdout.write(buf);
        if len(check[0]) == 2 or check[0][0] == sys.stdin.fileno():
            bf = string.strip(sys.stdin.readline()) + "\r\n";
#            print metal.hexdump (bf);
            soc.send (bf);
except KeyboardInterrupt:
    print "disconnecting..";
    soc.close();
