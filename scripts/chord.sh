#!/usr/bin/bash
BOOTSTRAP_NODE="" # Bootstrap Node Goes Here
CHORD_NODES="" # Chord Nodes other than stable bootstrap node goes here
chord_array=($CHORD_NODES)
TEST_SIZE=32

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
    CMD="cd a2 && python main.py --ip $BOOTSTRAP_NODE >> chord_test.log 2>&1"
    echo "Starting Bootstrap Node $BOOTSTRAP_NODE with command: $CMD"
    # echo "$CMD"
    ssh -f "$BOOTSTRAP_NODE" $CMD
    sleep 2
}

start_chord_nodes() {
    for node in $CHORD_NODES
    do
        CMD="cd a2 && python main.py --ip $node --bootstrap $BOOTSTRAP_NODE >> chord_test.log 2>&1"
        echo "Starting $node with command: $CMD"
        ssh -f "$node" $CMD
    done
}

stop_bootstrap_node() {
    CMD="cd a2 && scripts/chord.sh STOP_LOCAL_NODE"
    echo "Stopping Bootstrap Node $node with command: $CMD"
    ssh -f "$BOOTSTRAP_NODE" $CMD
}

stop_chord_nodes() {
    for node in $CHORD_NODES
    do
        CMD="cd a2 && scripts/chord.sh STOP_LOCAL_NODE"
        echo "Stopping $node with command: $CMD"
        ssh -f "$node" $CMD
    done
}

periodically_back_up_finger_tables() {
    TEST_PATH="$1"
    # Test running for 300 seconds
    sleep 5
    for ((i=0;i<300;i++));
    do
        TIMESTAMP=$(date +%s)
        mkdir "$TEST_PATH/backup_fingers_$TIMESTAMP"
        cp *.json "$TEST_PATH/backup_fingers_$TIMESTAMP/"
        sleep 1
    done
}

run_scalability_test() {
    for ((i=0;i<20;i++));
    do
        rm -rf chord.log
        rm -rf chord_test.log
        rm -rf "*.json"
        echo "Running Scalability Test Iteration $i for $TEST_SIZE nodes"
        TEST_PATH="test/scalability_$TEST_SIZE/iter_$i"
        mkdir -p "$TEST_PATH"
        periodically_back_up_finger_tables "$TEST_PATH" &
        echo "Starting Bootstrap Node: $BOOTSTRAP_NODE"
        start_bootstrap_node
        echo "Starting Other Nodes"
        start_chord_nodes
        # Test running for 300 seconds
        sleep 315
        echo "Stopping Bootstrap Node: $BOOTSTRAP_NODE"
        stop_bootstrap_node
        echo "Stopping Other Nodes"
        stop_chord_nodes
        sleep 30 # Necessary to wait a bit
        cp *.json "$TEST_PATH/"
        cp "chord.log" "$TEST_PATH/"
        cp "chord_test.log" "$TEST_PATH/"
        echo "Finished Test Iteration $i for $TEST_SIZE nodes !!!"
    done
}

run_recoverability_test() {
    for ((i=0;i<20;i++));
    do
        rm -rf chord.log
        rm -rf chord_test.log
        rm -rf "*.json"
        echo "Running Recoverability Test Iteration $i for $TEST_SIZE nodes"
        TEST_PATH="test/recoverability_$TEST_SIZE/iter_$i"
        mkdir -p "$TEST_PATH"
        periodically_back_up_finger_tables "$TEST_PATH" &
        echo "Starting Bootstrap Node: $BOOTSTRAP_NODE"
        start_bootstrap_node
        echo "Starting Other Nodes"
        start_chord_nodes
        # Let Chord Stabilize for 60 seconds
        sleep 60
        drop_count=$((TEST_SIZE/2))
        array=( $(echo "$CHORD_NODES" | sed -r 's/(.[^;]*;)/ \1 /g' | tr " " "\n" | shuf | tr -d " " ) )
        for ((j=0;j<$drop_count;j++));
        do
            node=${array[$j]}
            CMD="cd a2 && scripts/chord.sh STOP_LOCAL_NODE"
            echo "Stopping $node with command: $CMD"
            TIMESTAMP=$(date +%s)
            echo "Stopping $node at $TIMESTAMP" >> "$TEST_PATH/actions.log"
            ssh -f "$node" $CMD
        done
        # Let Chord Stabilize after chrash of half of the nodes
        sleep 120
        for ((j=0;j<$drop_count;j++));
        do
            node=${array[$j]}
            CMD="cd a2 && python main.py --ip $node --bootstrap $BOOTSTRAP_NODE >> chord_test.log 2>&1"
            echo "Starting $node with command: $CMD"
            TIMESTAMP=$(date +%s)
            echo "Starting $node at $TIMESTAMP" >> "$TEST_PATH/actions.log"
            ssh -f "$node" $CMD
        done
        # Let Chord Stabilize after recover of half of the nodes
        sleep 120
        echo "Stopping Bootstrap Node: $BOOTSTRAP_NODE"
        stop_bootstrap_node
        echo "Stopping Other Nodes"
        stop_chord_nodes
        sleep 30 # Necessary to wait a bit
        cp *.json "$TEST_PATH/"
        cp "chord.log" "$TEST_PATH/"
        cp "chord_test.log" "$TEST_PATH/"
        echo "Finished Test Iteration $i for $TEST_SIZE nodes !!!"
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
    elif [ "RUN_SCALABILITY_TEST" = "$OPERATION" ]
    then
        run_scalability_test
    elif [ "RUN_RECOVERABILITY_TEST" = "$OPERATION" ]
    then
        run_recoverability_test
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