import asyncore, socket, time, sys, string, struct, random, time;
from array import array;

def hexdump (Data):
    Counter = 0;
    Div = 4;
    Buffer = "";
    LineData = ""
    for Ch in Data:
        if (Counter % 16) == 0:
            Buffer += (hex (Counter) + " ").rjust (7) + " ";
        Div -= 1;
        Buffer += string.zfill ((hex ( ord(Ch)) [2:]), 2) + " ";
        if (ord (Ch) >= 32) & (ord (Ch) < 127):
            LineData += Ch;
        else:
            LineData += ".";
        if Div == 0:
            Div = 4;
            Buffer += " ";
        if (Counter % 16) == 15:
            Buffer += " " + LineData + "\n";
            LineData = "";
        Counter += 1;
    Length = Counter % 16;
    return Buffer + LineData.rjust (53 - ((Length * 3) + int(Length / 4)) + len (LineData));

def debug (Object, Message):
    Pieces = string.split (`Object`[1:-1], ' ');
    Module, Name = string.split (Pieces [0], '.');
    print time.strftime("%a, %d %b %Y %H:%M:%S %Z", time.localtime()) + " " + Name + "@" + Pieces [len (Pieces) - 1] + ": " + Message; 
    
def address (Addr):
    return Addr [0] + ":" + `Addr [1]`;

def resolve (Addr):
    return (socket.gethostbyname (Addr[0]), Addr [1]);

class protocol:
    def __init__ (Self):
        Self.Packets = {};
        Self.Transformations = {"uint16":"H", "int16":"h", "str8":"8s", "str4": "4s", "str2": "2s"};
    
    def load_protocol (Self, Packets):
        Self.Packets = Packets;
    
    def make (Self, Message, Parameters):
        Buffer = Message + ":";
        Bits = string.split (Self.Packets [Message], ' ');
        for Bit in Bits:
            Name, Type = string.split (Bit, ':');
            if Type == '':
                Buffer += Name
            else:
                Buffer += struct.pack ("!" + Self.Transformations [Type], Parameters [Name])
            
        return Buffer + "\x00";
    
    def interpret (Self, Message):
        Msg = Message [0: string.find (Message, ":")];
        Data = Message [string.find (Message, ":") + 1: len (Message) - 1];
        UnpackString = "";
        Names = [];
        Bits = string.split (Self.Packets [Msg], ' ');
        for Bit in Bits:
            Name, Type = string.split (Bit, ':');
            UnpackString += Self.Transformations [Type];
            Names.append (Name)
        Parameters = {};
        Unpackage = struct.unpack ("!" + UnpackString, Data);
        if len (Names) != len (Unpackage):
            debug (Self, "oh my god something crazy has happened!");
        Ln = 0;
        while (Ln < len (Unpackage)):
            Parameters [Names [Ln]] = Unpackage [Ln];
            Ln += 1
        return (Msg, Parameters);

class interaction (asyncore.dispatcher):
    STREAM = socket.SOCK_STREAM;
    PACKET = socket.SOCK_DGRAM;

    def __init__ (Self, Typ, OnRead, OnWrite = 0, OnConnect = 0, OnDisconnect = 0):
        Self.Host = ();
        Self.Connected = 0;
        if Typ is interaction.STREAM or Typ is interaction.PACKET:
            asyncore.dispatcher.__init__ (Self);
            Self.create_socket (socket.AF_INET, Typ);
        else:
            asyncore.dispatcher.__init__ (Self, Typ);
            try:
                Self.Host = Typ.getpeername ();
                Self.Connected = 1;
            except:
                pass;
        Self.SocketBuffer = "";
        Self.OnRead = OnRead;
        Self.OnWrite = OnWrite;
        Self.OnConnect = OnConnect;
        Self.OnDisconnect = OnDisconnect;
        Self.BufferSize = 256;

    
    def host (Self, Address = 0):
        if (Self.Connected == 0) & (Address != 0):
            Self.Host = Address;
            Self.Host = (socket.gethostbyname (Self.Host [0]), Self.Host [1]);
        return Self.Host;

    def listen (Self, Addr, Port, N = 1):
        Self.bind ((Addr, Port));
        asyncore.dispatcher.listen (Self, N);
    
    def write (Self, Buffer):
        Self.SocketBuffer += Buffer;
    
    def writable (Self):
        if (Self.OnWrite != 0) | len (Self.SocketBuffer):
            return 1;
        return 0;
            
    def readable (Self):
        if Self.OnRead or Self.OnConnect:
            return 1;
        return 0;
    
    def connect_state (Self, OnConnect):
        Self.OnConnect = OnConnect;

    def disconnect_state (Self, OnDisconnect):
        Self.OnDisconnect = OnDisconnect;

    def write_state (Self, State):
        Self.OnWrite = State;
    
    def read_state (Self, State):
        Self.OnRead = State;
    
    def connect (Self, To):
        asyncore.dispatcher.connect (Self, To);
        Self.Connected = 1;
        Self.Host = To;
    
    def handle_write (Self):
        if len (Self.SocketBuffer) > 0:
            if Self.Connected:
                Sent = Self.send (Self.SocketBuffer);
            else:
                Sent = Self.sendto (Self.SocketBuffer, Self.Host);
            Self.SocketBuffer = Self.SocketBuffer [Sent:];
        if (Self.OnWrite != 0):
            New = Self.OnWrite ();
            if New.__class__.__name__ != "NoneType":
                Self.OnWrite = New;
    
    def handle_read (Self):
        if (Self.Connected):
            Data = Self.recv (Self.BufferSize);
            Address = Self.Host;
        else:
            Data, Address = Self.recvfrom (Self.BufferSize);
        New = Self.OnRead (Data, Address);
        if New.__class__.__name__ != "NoneType":
            Self.OnRead = New;

    def close (self):
        if len (Self.SocketBuffer) > 0:
            if Self.Connected:
                Sent = Self.send (Self.SocketBuffer);
            else:
                Sent = Self.sendto (Self.SocketBuffer, Self.Host);
        asyncore.dispatcher.close (self);
      
    def handle_close (Self):
        Self.close ();
        if (Self.OnDisconnect):
            Self.OnDisconnect ();

    def handle_accept (Self):
        if Self.OnConnect:
            Con, Addr = Self.accept ();
            Self.OnConnect (Con, Addr);

def run ():
    asyncore.loop ();
