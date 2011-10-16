#!/usr/bin/env python

# Usage: robotfindskitten.py [port]
# Starts a robotfindskitten on the given port (by default 2468).

# To play game, connect using `telnet localhost {port}`

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

import sys, metal, random, string;

# {attr} 0 Reset All Attributes (return to normal mode) 1 Bright (Usually turns on BOLD)
#  2 Dim 3 Underline 5 Blink 7 Reverse 8 Hidden
# {fg} 30 Black 31 Red 32 Green 33 Yellow 34 Blue 35 Magenta 36 Cyan 37 White
# {bg} 40	Black 41 Red 42 Green 43 Yellow 44 Blue 45 Magenta 46 Cyan 47 White

def mkc(attr, olda =[]):
    newattr =[];
    for e in attr:
        if e not in olda: newattr.append(e);
    if len(newattr):
        buf = "\x1b[";
        for atr in newattr:
            buf += `atr` + ";";
        return buf[:-1] + "m", attr;
    return "", attr;

class TermColour:
    def __init__(self):
        self.enable = True;
        self.attributes =[0];
        self.stack =[];

    def enabled(self, yes = True):
        self.enable = yes;

    def push(self, attr =[]):
        if self.enable:
            bf, natr = mkc(attr, self.attributes);
            self.stack.append(self.attributes);
            self.attributes = natr;
            return bf;
        return "";

    def make(self, attr):
        if self.enable:
            bf, natr = mkc(attr, self.attributes);
            self.attributes = natr;
            return bf;
        return "";

    def pop(self):
        if self.enable:
            bf, natr = mkc(self.stack.pop(), self.attributes);
            self.attributes = natr;
            return bf;
        return "";

class RobotServer(metal.interaction):
    def __init__(self, host = "localhost", port = 0):
        if port is 0:
            port = random.randint(2468, 51015);
        metal.interaction.__init__(self, metal.interaction.STREAM, 0, 0, self.connect);
        self.listen(host, port, 10);
        metal.debug(self, "listening on " + host + ":" + `port`);

    def connect(self, conn, address):
        metal.debug(self, "got connect request from " + metal.address(address));
        KittenClient(conn);

def read_flat_rfk_data(file, append = "\r\n"):
    bfr = "";
    f = open(file);
    for line in f.readlines():
        bfr += line[:-1] + append;
    return bfr;

def read_list_rfk_data(file, append = "\r\n"):
    bfr =[];
    f = open(file);
    for line in f.readlines():
        bfr.append(line[:-1] + append);
    return bfr;

hello_strings = read_list_rfk_data("greetings.rfk", "");
goodbye_strings = read_list_rfk_data("goodbyes.rfk");
story = read_flat_rfk_data("story.rfk");
help = read_flat_rfk_data("help.rfk");
findkitten = read_flat_rfk_data("win.rfk");
messages = read_list_rfk_data("messages.rfk");

class KittenClient(metal.interaction):
    def __init__(self, socket):
        metal.interaction.__init__(self, socket, self.incoming, self.hello, 0, self.disconnect);
        self.restart();
        self.color = TermColour();
        self.input = ""

    def restart(self):
        size = random.randint(10, 25);
        self.game = GameState(2 * size, size);

    def win(self):
        self.write(findkitten);
        self.restart();

    def hello(self):
        self.write("version: kittenfindsrobot/0.2[" + random.choice(hello_strings) + "]\r\n");
        self.write("words: help story quit color\r\n");
        self.write("press any key to start..\r\n");
        self.write("\r\nUse characters E(up) C(down) S(left) F(right) for navigation.\r\n")
        return 0;

    def incoming(self, data, address):
        self.input += data;
        if len(self.input) == 0 or self.input[-1] != "\n":
            return;
        try:
            command = string.split(string.strip(self.input), " ");
            self.input = "";
            if command[0] == "story":
                self.write(self.color.push([35]) + "\r\n");
                self.write(story);
                self.write(self.color.pop() + "\r\n");
                return;
            if command[0] == "quit":
                self.write(self.color.push([35]) + "\r\n");
                self.write(random.choice(goodbye_strings));
                self.write(self.color.pop() + "\r\n");
                self.close();
                return;
            elif command[0] == "help":
                self.write(self.color.push([35]) + "\r\n");
                self.write(help);
                self.write(self.color.pop() + "\r\n");
                return;
            elif command[0] == "color":
                if command[1] == "on":
                    self.color.enabled(True);
                    self.write("color enabled\r\n");
                else:
                    self.color.enabled(False);
                    self.write("color disabled\r\n");
                return;
            elif command[0] == "restart":
                self.restart();
                return;
            status = self.game.move(command[0]);
            if status == 0:
                self.write(self.game.draw_field(self.color));
                self.win();
                return;
            elif status > 0:
                self.write(messages[status]);
            else:
                self.write("okay\r\n");
            self.write(self.game.draw_field(self.color));
        except KeyboardInterrupt:
            self.write("bad input\r\n");
            pass;

    def disconnect(self):
        metal.debug(self, "client " + metal.address(self.host()) + " disconnected");

class GameState:
    def __init__(self, wid, hei):
        self.width, self.height = wid, hei;
        self.rx, self.ry = int(wid/2), int(hei/2);
        self.field =[];
        for i in range(0, self.height):
            row =[];
            for j in range(0, self.width):
                #color, status, displaychar
                #status = -1(no message) = 0(kitten here) = >0 item not kitten msg with number
                row.append(([0], -1, " "));
            self.field.append(row);
        placedkitten = False;
        for p in range(0, int((self.width * self.height) / 32)):
            x, y = random.randint(0, self.width-1), random.randint(0, self.height-1);
            kittensymb = random.randint(1, len(messages) - 1);
            if not placedkitten:
                print "kitten=" + `x` + " " + `y`;
                kittensymb = 0;
                placedkitten = True;
            charr = chr(random.randint(32, 127));
            while charr == " ":
                charr = chr(random.randint(32, 127));
            self.field[y][x] =([random.randint(31,36)], kittensymb, charr);

    def draw_field(self, cl):
        buffer = cl.push([37]);
        buffer += "+" +('-' * self.width) + "+\r\n";
        for y in range(0, self.height):
            buffer += cl.make([37]) + "|";
            for x in range(0, self.width):
                data = self.field[y][x];
                if(self.rx == x) and(self.ry == y):
                    buffer += cl.make([0, 37]) + "#";
                else:
                    buffer += cl.make(data[0]) + data[2];
            buffer += cl.make([37]) + "|\r\n";
        buffer += cl.make([37]) + "+" +('-' * self.width) + "+\r\n";
        buffer += cl.pop() + "\r\n";
        return buffer;

    def move(self, str):
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
            data = self.field[self.ry][self.rx];
            if data[1] != -1:
                return data[1];
        return -1;

try:
    port = 2468
    
    if len(sys.argv) == 2:
        port = int(sys.argv[1])
    
    server = RobotServer("0.0.0.0", port);
    metal.run();
except KeyboardInterrupt:
    server.close();
