#!/usr/bin/env python
import metal, sys

def xterm_color (fg = 7, bg = 0, attr = 0):
    return "\x1b[" + `attr` + ";" + `fg + 30` + ";" + `bg + 40` + "m";

sys.stdout.write(metal.hexdump (sys.argv[1]) + "\n");
sys.stdout.write(sys.argv[1] + "\n");
