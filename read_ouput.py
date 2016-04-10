#!/usr/bin/python

import os

prefix = "TIMING DATA "

def get_output(cmd):
    is_output = False
    for s in cmd:
        if s == "-o":
            is_output = True
            continue
        if is_output:
            is_output = False
            return s
    return None

for l in open("make.log"):

    if not l.startswith(prefix): continue
    l = l[len(prefix):]

    parts=l.split("@@@")
    print(" ".join(parts[0:3]))

    pwd=parts[3].split("=", 2)[1]
    print("  "+pwd)

    del parts[0:4]

    outfile = os.path.realpath(os.path.join(pwd, get_output(parts)))
    print("  "+outfile)

