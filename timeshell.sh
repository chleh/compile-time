#!/bin/sh

# shell needed if this is run as a shell replacement, not needed if only
# wrapping some command
#SHELL="/bin/sh"
SHELL=""
TIME="`which time`"

N='@@@'

args() {
    while [ "$#" -gt 0 ]; do
        echo -n "${1//%/%%}$N"
        shift
    done
}

FORMAT="TIMING DATA real=%E${N}sys=%S${N}user=%U${N}pwd=$(pwd)${N}$(args $SHELL "$@")"

"$TIME" -f "$FORMAT" $SHELL "$@"
