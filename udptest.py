import metal, random, string, socket;

# {attr} 0 Reset All Attributes (return to normal mode) 1 Bright (Usually turns on BOLD)
#  2 Dim 3 Underline 5 Blink 7 Reverse 8 Hidden
# {fg} 30 Black 31 Red 32 Green 33 Yellow 34 Blue 35 Magenta 36 Cyan 37 White
# {bg} 40	Black 41 Red 42 Green 43 Yellow 44 Blue 45 Magenta 46 Cyan 47 White


class termcolor:
    def __init__ (self):
        self.color_enable = True;
        self.color_attributes = [[0]];
        self.color_stack = [];

def mkc (olda, attr):
    newattr = [];
    for e in attr:
        if e not in olda: newattr.append(e);
    if len(newattr):
        buf = "\x1b[";
        for atr in newattr:
            buf += `atr` + ";";
        print metal.hexdump (buf[:-1] + "m");
        return buf[:-1] + "m", attr;
    return "", attr;

def color_push (attr):
    global color_enable, color_attributes, color_stack;
    if color_enable:
        bf, natr = mkc (color_attributes, attr);
        color_stack.append (color_attributes);
        color_attributes = natr;
        return bf;
    return "";

def col (attr):
    global color_enable, color_attributes, color_stack;
    if color_enable:
        bf, natr = mkc (color_attributes, attr);
        color_attributes = natr;
        return bf;
    return "";

def color_pop ():
    global color_enable, color_attributes, color_stack;
    if color_enable:
        newattr = color_stack.pop();
        bf, natr = mkc (color_attributes, newattr);
        color_attributes = natr;
        return bf;
    return "";

class server (metal.interaction):
    def __init__ (self, host = "localhost", port = 2468):
        metal.interaction.__init__ (self, metal.interaction.STREAM, 0, 0, self.connect);
        self.listen (host, port, 10);
        metal.debug (self, "listening on " + host + ":" + `port`);

    def connect (self, conn, address):
        metal.debug (self, "got connect request from " + metal.address (address));
        conn.send ("kitten and robot/0.1 (Sami <ioquatix@oriontransfer.mine.nu>)\r\n");
        conn.send ("if your terminal supports vt100 color sequences, write con\r\n");
        conn.send ("or coff to turn color support on or off.\r\n");
        conn.send ("if you see weird looking characters, you should write coff.\r\n");
        conn.send ("(you can do this at any time)\r\n"):
        conn.send ("press return to begin (or write help for help)..\r\n");
        debugger (conn);

class kittenrobotgame:
    def __init__ (self):
        hei = random.randint (10, 25);
        wid = 2 * hei;
        self.width, self.height = wid, hei;
        self.rx, self.ry = int(wid/2), int (hei/2);
        self.field = [];
        for i in range (0, self.height):
            row = [];
            for j in range (0, self.width):
                row.append ("0e ");
            self.field.append (row);
        placedkitten = False;
        for p in range (0, int((self.width * self.height) / 32)):
            x, y = random.randint (0, self.width-1), random.randint (0, self.height-1);
            kittensymb = "e";
            if not placedkitten:
                kittensymb = "k";
                placedkitten = True;
            charr = chr (random.randint (32, 127));
            while charr == " ":
                charr = chr (random.randint (32, 127));
            self.field [y] [x] = `random.randint (1,6)` + kittensymb + charr;

    def draw_field (self):
        buffer = color_push ([37, 40]);
        buffer += "+" + ('-' * self.width) + "+\r\n";
        for y in range (0, self.height):
            buffer += col ([37, 40]) + "|";
            for x in range (0, self.width):
                data = self.field [y] [x];
                if (self.rx == x) and (self.ry == y):
                    buffer += col ([0, 37, 41]) + "#";
                else:
                    buffer += col ([int(data[0]) + 30, 40]) + data[2];
            buffer += col ([37, 40]) + "|\r\n";
        buffer += col ([37, 40]) + "+" + ('-' * self.width) + "+\r\n";
        buffer += color_pop () + "\r\n";
        return buffer;

    def move (self, str):
        for c in str:
            if c == "e":
                self.ry -= 1;
            elif c == "c":
                self.ry += 1;
            elif c == "f":
                self.rx += 1;
            elif c == "s":
                self.rx -= 1;
            self.rx = self.rx % self.width;
            self.ry = self.ry % self.height;
            data = self.field [self.ry] [self.rx];
            if data [1] == "k":
                return 1; #found kitten
            elif data [2] != " ":
                return 2;
        return 0;

class debugger (metal.interaction):
    def __init__ (self, socket):
        metal.interaction.__init__ (self, socket, self.incoming, 0, 0);
        self.game = kittenrobotgame();

    def help (self):
        self.write (color_push ([0, 34]));
        self.write ("you are robot.\r\n" + col([35]) + col([35]) + "must find kitten.\r\n" + col([34]));
        self.write ("to move wheels enter a sequence of these characters followed by\r\n<cr><lf> (typically, return key)\r\n");
        self.write ("e - up\r\ns - left\r\nf - right\r\nc - down\r\n");
        self.write (color_pop() + "\r\n");

    def win (self):
        self.write (found_kitten);
        print metal.address(self.host()) + " found kitten!";

    def incoming (self, data, address):
        global color_enable;
        data = string.strip (data);
        if data == "help":
            self.help();
            return;
        if data == "color on":
            color_enable = True;
            self.write ("color enabled\r\n");
            return;
        if data == "color off":
            color_enable = False;
            self.write ("color disabled\r\n");
            return;
        if data == "restart":
            self.game = kittenrobotgame();
            self.write (self.game.draw_field());
            return;
        res = self.game.move (string.strip(data));
        if res == 1:
            self.win ();
            self.game = kittenrobotgame();
        else:
            if res == 2: self.write ("no kitten\r\n");
            else: self.write ("ok\r\n");
            self.write (self.game.draw_field());

