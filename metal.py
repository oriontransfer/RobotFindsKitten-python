
# metal is a simple python network library I wrote years ago.

# Copyright (c) 2003, 2011 by Samuel Williams.
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import asyncore, socket, time, sys, string, struct, random, time;
from array import array;

def hexdump(Data):
    Counter = 0;
    Div = 4;
    Buffer = "";
    LineData = ""
    for Ch in Data:
        if(Counter % 16) == 0:
            Buffer +=(hex(Counter) + " ").rjust(7) + " ";
        Div -= 1;
        Buffer += string.zfill((hex( ord(Ch)) [2:]), 2) + " ";
        if(ord(Ch) >= 32) &(ord(Ch) < 127):
            LineData += Ch;
        else:
            LineData += ".";
        if Div == 0:
            Div = 4;
            Buffer += " ";
        if(Counter % 16) == 15:
            Buffer += " " + LineData + "\n";
            LineData = "";
        Counter += 1;
    Length = Counter % 16;
    return Buffer + LineData.rjust(53 -((Length * 3) + int(Length / 4)) + len(LineData));

def debug(Object, Message):
    Pieces = string.split(`Object`[1:-1], ' ');
    Module, Name = string.split(Pieces [0], '.');
    print time.strftime("%a, %d %b %Y %H:%M:%S %Z", time.localtime()) + " " + Name + "@" + Pieces [len(Pieces) - 1] + ": " + Message; 
    
def address(Addr):
    return Addr [0] + ":" + `Addr [1]`;

def resolve(Addr):
    return(socket.gethostbyname(Addr[0]), Addr [1]);

class protocol:
    def __init__(self):
        self.Packets = {};
        self.Transformations = {"uint16":"H", "int16":"h", "str8":"8s", "str4": "4s", "str2": "2s"};
    
    def load_protocol(self, Packets):
        self.Packets = Packets;
    
    def make(self, Message, Parameters):
        Buffer = Message + ":";
        Bits = string.split(self.Packets [Message], ' ');
        for Bit in Bits:
            Name, Type = string.split(Bit, ':');
            if Type == '':
                Buffer += Name
            else:
                Buffer += struct.pack("!" + self.Transformations [Type], Parameters [Name])
            
        return Buffer + "\x00";
    
    def interpret(self, Message):
        Msg = Message [0: string.find(Message, ":")];
        Data = Message [string.find(Message, ":") + 1: len(Message) - 1];
        UnpackString = "";
        Names = [];
        Bits = string.split(self.Packets [Msg], ' ');
        for Bit in Bits:
            Name, Type = string.split(Bit, ':');
            UnpackString += self.Transformations [Type];
            Names.append(Name)
        Parameters = {};
        Unpackage = struct.unpack("!" + UnpackString, Data);
        if len(Names) != len(Unpackage):
            debug(self, "oh my god something crazy has happened!");
        Ln = 0;
        while(Ln < len(Unpackage)):
            Parameters [Names [Ln]] = Unpackage [Ln];
            Ln += 1
        return(Msg, Parameters);

class interaction(asyncore.dispatcher):
    STREAM = socket.SOCK_STREAM;
    PACKET = socket.SOCK_DGRAM;

    def __init__(self, Typ, OnRead, OnWrite = 0, OnConnect = 0, OnDisconnect = 0):
        self.Host =();
        self.Connected = 0;
        if Typ is interaction.STREAM or Typ is interaction.PACKET:
            asyncore.dispatcher.__init__(self);
            self.create_socket(socket.AF_INET, Typ);
        else:
            asyncore.dispatcher.__init__(self, Typ);
            try:
                self.Host = Typ.getpeername();
                self.Connected = 1;
            except:
                pass;
        self.SocketBuffer = "";
        self.OnRead = OnRead;
        self.OnWrite = OnWrite;
        self.OnConnect = OnConnect;
        self.OnDisconnect = OnDisconnect;
        self.BufferSize = 256;

    
    def host(self, Address = 0):
        if(self.Connected == 0) &(Address != 0):
            self.Host = Address;
            self.Host =(socket.gethostbyname(self.Host [0]), self.Host [1]);
        return self.Host;

    def listen(self, Addr, Port, N = 1):
        self.bind((Addr, Port));
        asyncore.dispatcher.listen(self, N);
    
    def write(self, Buffer):
        self.SocketBuffer += Buffer;
    
    def writable(self):
        if(self.OnWrite != 0) | len(self.SocketBuffer):
            return 1;
        return 0;
            
    def readable(self):
        if self.OnRead or self.OnConnect:
            return 1;
        return 0;
    
    def connect_state(self, OnConnect):
        self.OnConnect = OnConnect;

    def disconnect_state(self, OnDisconnect):
        self.OnDisconnect = OnDisconnect;

    def write_state(self, State):
        self.OnWrite = State;
    
    def read_state(self, State):
        self.OnRead = State;
    
    def connect(self, To):
        asyncore.dispatcher.connect(self, To);
        self.Connected = 1;
        self.Host = To;
    
    def handle_write(self):
        if len(self.SocketBuffer) > 0:
            if self.Connected:
                Sent = self.send(self.SocketBuffer);
            else:
                Sent = self.sendto(self.SocketBuffer, self.Host);
            self.SocketBuffer = self.SocketBuffer [Sent:];
        if(self.OnWrite != 0):
            New = self.OnWrite();
            if New.__class__.__name__ != "NoneType":
                self.OnWrite = New;
    
    def handle_read(self):
        if(self.Connected):
            Data = self.recv(self.BufferSize);
            Address = self.Host;
        else:
            Data, Address = self.recvfrom(self.BufferSize);
        New = self.OnRead(Data, Address);
        if New.__class__.__name__ != "NoneType":
            self.OnRead = New;

    def close(self):
        if len(self.SocketBuffer) > 0:
            if self.Connected:
                Sent = self.send(self.SocketBuffer);
            else:
                Sent = self.sendto(self.SocketBuffer, self.Host);
        asyncore.dispatcher.close(self);
      
    def handle_close(self):
        self.close();
        if(self.OnDisconnect):
            self.OnDisconnect();

    def handle_accept(self):
        if self.OnConnect:
            Con, Addr = self.accept();
            self.OnConnect(Con, Addr);

def run():
    asyncore.loop();
