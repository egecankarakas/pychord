#!/usr/bin/bash
BOOTSTRAP_NODE="node302"
CHORD_NODES="node303 node304 node305"

pid_match() {
   local VAL=`ps -aef | grep "$1" | grep -v grep | awk '{print $2}' | head -n 1`
   echo $VAL
}

stop_if_needed() {
  local match="$1"
  local name="$2"
  local PID=`pid_match "$match"`
  if [[ "$PID" -ne "" ]];
  then
    kill "$PID"
    sleep 1
    local CHECK_AGAIN=`pid_match "$match"`
    if [[ "$CHECK_AGAIN" -ne "" ]];
    then
      kill -9 "$CHECK_AGAIN"
    fi
  else
    echo "No $name instance found to stop"
  fi
}

start_bootstrap_node() {
    CMD="cd a2 && python main.py --ip $BOOTSTRAP_NODE"
    echo "$CMD"
    ssh -f "$BOOTSTRAP_NODE" $CMD
    sleep 2
}

start_chord_nodes() {
    for node in $CHORD_NODES
    do
        CMD="cd a2 && python main.py --ip $node --bootstrap $BOOTSTRAP_NODE"
        echo "$CMD"
        ssh -f "$node" $CMD
    done
}

stop_bootstrap_node() {
    CMD="cd a2 && scripts/chord.sh STOP_LOCAL_NODE"
    ssh -f "$BOOTSTRAP_NODE" $CMD
}

stop_chord_nodes() {
    for node in $CHORD_NODES
    do
        CMD="cd a2 && scripts/chord.sh STOP_LOCAL_NODE"
        echo "$CMD"
        ssh -f "$node" $CMD
    done
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
    elif [ "STOP_LOCAL_NODE" = "$OPERATION" ]
    then
        stop_if_needed "main.py" "Chord Node"
    else
        if [ "HELP" != "$OPERATION" ];
        then
            echo "UNKOWN OPERATION '$OPERATION'"
        else
            echo "Supported Operations:"
            echo "START: Start Chord Ring"
            echo "STOP: Stop Chord Ring"
            echo "STOP_LOCAL_NODE: Stop Chord Node running in local"
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