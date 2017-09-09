#!/usr/bin/python

import signal
signal.signal(signal.SIGPIPE, signal.SIG_DFL)

import generate_dependency_graph
import subprocess as sp
import os
import re
import sys

rootdir  = os.path.realpath("res")
builddir = os.path.join(rootdir, "build")

excludes = [ re.compile(r"/ThirdParty/"), re.compile("^/usr/") ]


# change makefiles s.t. timeshell wraps each compiler run
if False:
    oldpwd = os.path.realpath(os.getcwd())
    timeshell = os.path.join(oldpwd, "timeshell.sh")

    os.chdir(builddir)

    sp.run(["cmake", "."])

    assert ":" not in timeshell
    # cmd = [ "find", builddir, "-name", "*.make", "-exec",
    #     "sed", "-i", "-e", "s:^SHELL = .*$:SHELL = "+timeshell+":", "{}", ";" ]
    # sp.run(cmd)
    cmd = [ "find", builddir, "-name", "*.make", "-exec",
            "sed", "-i", "-e", "s:/usr/bin/c++:"+timeshell+" &:", "{}", ";" ]
    sp.run(cmd)
    cmd = [ "find", builddir, "-name", "*.make", "-exec",
            "sed", "-i", "-e", "s:/usr/bin/cc:"+timeshell+" &:", "{}", ";" ]
    sp.run(cmd)
    # TODO: linker, do not always rebuild from scratch

    with open(os.path.join(oldpwd, "make.log"), "w") as fh:
        sp.run(["make", "-j1"], stderr=fh)


depgraph = generate_dependency_graph.generate(builddir, excludes)

if True:

    # parse timing output
    line_prefix = "TIMING DATA "

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

        if not l.startswith(line_prefix): continue
        l = l[len(line_prefix):]

        parts=l.split("@@@")
        # print(" ".join(parts[0:3]))
        time_sys  = float(parts[1][4:])
        time_user = float(parts[2][5:])


        pwd = parts[3].split("=", 2)[1]
        # print("  "+pwd)

        del parts[0:4]

        outfile = os.path.realpath(os.path.join(pwd, get_output(parts)))

        path_prefix = os.path.join(rootdir, "")
        if outfile.startswith(path_prefix): outfile = outfile[len(path_prefix):]
        # print("{:6.2f} {}".format(time_sys+time_user, outfile))

        if outfile in map_path_v:
            depgraph.vs[map_path_v[outfile]]["cputime"] = time_sys + time_user

    total_cputime = 0.0

    # accumulate compile times
    for v in depgraph.vs:
        if "cputime" not in v.attributes() or v["cputime"] is None: continue

        cpu = v["cputime"]
        total_cputime += cpu

        for nid in depgraph.neighbors(v.index, mode="out"):
            nv = depgraph.vs[nid]
            if "cputime_dep" in nv.attributes() and nv["cputime_dep"] is not None:
                # print(nv.attributes())
                nv["cputime_dep"] += cpu
            else:
                nv["cputime_dep"] = cpu

    print("total cputime: {:7.2f}s".format(total_cputime))


    if True:
        print()
        print("CPU time taken to compile certain object files")
        print("----------------------------------------------")
        for v in sorted(depgraph.vs.select(_outdegree_gt = 0),
                key=lambda v: v["cputime"],
                reverse=True):
            print("{:6.2f}s | {:3}".format(
                v["cputime"], v["path"]))

        print()
        print("Percentage of total compile time triggered by changes in certain source files")
        print("-----------------------------------------------------------------------------")

        for v in sorted(depgraph.vs.select(_indegree_gt = 0),
                key=lambda v: v["cputime_dep"],
                reverse=True):
            print("{:6.2f}% | {:3}".format(
                v["cputime_dep"]/total_cputime*100.0, v["path"]))

    # print graph
    if False:
        print()
        print("Percentage of total CPU time taken to compile certain object files")
        print("-------------------------------------------------------------------------")
        print("lines starting with `>' indicate headers that the object file depends on.")
        print("the percentages in the header lines indicate the percentage of total")
        print("compile time needed when changing the respecitve header file.")

        for v in sorted(depgraph.vs.select(_outdegree_gt = 0),
                key=lambda v: v["cputime"],
                reverse=True):
            print("{:6.2f}%     | {:3}".format(v["cputime"]/total_cputime*100.0, v["path"]))

            for nid in sorted(depgraph.neighbors(v.index, mode="out"),
                    key=lambda v: depgraph.vs[v]["cputime_dep"], reverse=True):
                nv = depgraph.vs[nid]
                print("  > {:6.2f}% | {}".format(
                    nv["cputime_dep"]/total_cputime*100.0, nv["path"]))

    # print graph
    if True:
        print()
        print("Percentage of total compile time triggered by changes in certain source files")
        print("-----------------------------------------------------------------------------")
        print("lines starting with `<' indicate object files that depend on the respective")
        print("header file.")

        for v in sorted(depgraph.vs.select(_indegree_gt = 0),
                key=lambda v: v["cputime_dep"],
                reverse=True):
            print("{:6.2f}%     | {:3}".format(
                v["cputime_dep"]/total_cputime*100.0, v["path"]))

            for nid in sorted(depgraph.neighbors(v.index, mode="in"),
                    key=lambda v: depgraph.vs[v]["cputime"], reverse=True):
                nv = depgraph.vs[nid]
                print("  < {:6.2f}s | {:6.2f}% | {}".format(
                    nv["cputime"], nv["cputime"]/total_cputime*100.0, nv["path"]))

