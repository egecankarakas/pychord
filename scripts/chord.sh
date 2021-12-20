#!/usr/bin/bash
BOOTSTRAP_NODE="node335 node336 node337 node338"
CHORD_NODES="node335 node336 node337 node338"
CHORD_NODES_arry=( $CHORD_NODES )
CHORD_SIZE=${#CHORD_NODES_arry[@]}
removeLog="removed.log"
max_itteration=15



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

test_chord_removal_nodes() {
    max_nodes_todisable=$(expr $CHORD_SIZE / 2)
    echo "Max Nodes to Disable" $max_nodes_todisable
    #creating a test folder 
    folder_name="test_chord_removal_CordSize${CHORD_SIZE}_MaxDisabled_${max_nodes_todisable}_its_${max_itteration}"

    CMD="mkdir ./a2/test/${folder_name}"
    echo "$CMD"
    

    #used to generate a list of randome nodes
    nodes_used=()
    for i in {0..$max_nodes_todisable};
    do
      nodes_used+=$(( $RANDOM % $CHORD_SIZE ))
    done

    #echo nodes_used


    for i in {1..$max_nodes_todisable};
    do
      for n in {1..$max_itteration};
      do
        CMD="mkdir /test/${folder_name}/iter_${n}"
        echo $CMD
        start_bootstrap_node &
        start_chord_nodes & 
        #sleep 60 
        echo "Starting to Remove Nodes $nodes_used"
        for node in $CHORD_NODES;
        do
          echo "disabling:" $node
          tm=$(date '+%T.%3N')
          CMD="./a2/scripts/chord.sh STOP_LOCAL_NODE" &
          ("${node} is has been stoped @ ${tm} ") > "./a2/test/${folder_name }/${removeLog}"
          ssh -f "$node" $CMD
          echo "Node $node disabled @" $tm
        done
        sleep 240 
        stop_bootstrap_node
        stop_chord_nodes
        CMD "mv node3* node4* node2* node1* chord.log /test/${folder_name}/iter_${n}/ "
        echo $CMD 
      done
    done
}

test_chord_add_nodes() {

    #creating a test folder 
    folder_name="test_chord_added_CordSize${CHORD_SIZE}_MaxDisabled_${max_nodes_todisable}_its_${max_itteration}}"

    CMD="mkdir ./a2/test/${folder_name}"
    echo "$CMD"


    for j in {1..$max_nodes_todisable};
    do
      for n in {1..$max_itteration};
      do
        CMD="mkdir /test/${folder_name}/iter_${n}"
        echo $CMD
        start_bootstrap_node &
        sleep 20
        echo "Starting to Remove Nodes $nodes_used"
        for node in $CHORD_NODES;
        do
          echo "enabling:" $node
          tm=$(date '+%T.%3N')
          CMD="cd a2 && python main.py --ip $node --bootstrap $BOOTSTRAP_NODE"
          ssh -f "$node" $CMD &

          ("${node} has been started @ ${tm} ") > "./a2/test/${folder_name }/${removeLog}"
          echo "Node $node disabled @" $tm

        done
        sleep 240 
        stop_bootstrap_node
        stop_chord_nodes
        CMD "mv node3* node4* node2* node1* chord.log /test/${folder_name}/iter_${n}/ "
        echo $CMD 
      done
    done

    # no so i have no idea waht to do 
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
    elif [ "TEST_NODE_REMOVAL" = "$OPERATION" ]
    then 
        test_chord_removal_nodes

    elif [ "TEST_NODE_ADD" = "$OPERATION" ]
    then 
        test_chord_add_nodes
    elif [ "TEST_ADD_REMOVE_NODE" = "$OPERATION" ]
    then 
        test_chord_removal_nodes
        test_chord_add_nodes
  
    else
        if [ "HELP" != "$OPERATION" ];
        then
            echo "UNKOWN OPERATION '$OPERATION'"
        else
            echo "Supported Operations:"
            echo "START: Start Chord Ring"
            echo "STOP: Stop Chord Ring"
            echo "STOP_LOCAL_NODE: Stop Chord Node running in local"
            echo "START_LOCAL_NODE: Starts Chord Node running in local"
            echo "TEST_NODE_REMOVAL: Must use an even number of Chord Nodes"
            echo "TEST_NODE_ADDITION: Must use an even number of Chord Nodes"
            echo "TEST_ADD_REMOVE_NODE: Comp to rune both removal and aditional test with nodes hard coded in file"
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
