#!/usr/bin/bash
BOOTSTRAP_NODE="node304"
CHORD_NODES="node305 node306 node307"

start_bootstrap_node() {
    CMD="cd a2 && python main.py --ip $BOOTSTRAP_NODE"
    echo "$CMD"
}

start_chord_nodes() {
    for node in $CHORD_NODES
    do
        CMD="cd a2 && python main.py --ip $node --bootstrap $BOOTSTRAP_NODE"
        echo "$CMD"
    done
}

stop_bootstrap_node() {
    echo "Not Implemented Yet"
}

stop_chord_nodes() {
    echo "Not Implemented Yet"
}

run() {
    OPERATION=$1
    if [ "START" = "$OPERATION" ]
    then
        start_bootstrap_node
        start_chord_nodes
    elif [ "STOP" = "$OPERATION" ]
    then
        stop_bootstrap_node
        stop_chord_nodes
    else
        if [ "HELP" != "$OPERATION" ];
        then
            echo "UNKOWN OPERATION '$OPERATION'"
        else
            echo "Supported Operations:"
            echo "START: Start Chord Ring"
            echo "STOP: Stop Chord Ring"
        fi
    fi
}

if [ $# -lt 1 ];
then
  run "HELP"
else
  while [ $# -gt 0 ];
  do
    run "$1"
    shift
  done
fi

# while read p; do
#     p=$(echo "$p" | xargs)
#     echo "P is $p"
#     CMD="python main.py --ip $p"
#     if [[ ! $BOOTSTRAP_NODE ]]
#     then
#         BOOTSTRAP_NODE="$p"
#     else
#         CMD="$CMD --boootstrap $BOOTSTRAP_NODE"
#     fi
#     echo "$CMD"
        
#     # i=$((i+1))
# done <resources/nodes