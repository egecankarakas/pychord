# pychord
Implementation of Chord Protocol in Python.
Start the first node with providing hostname or ip
```
python main.py --ip X.X.X.1
```

Start other nodes by giving an arbitrary node in chord ring
```
python main.py --ip X.X.X.2 --bootstrap X.X.X.1
```

# DAS-5 setup
1-) Make sure python virtual environment is set to python3.6 and added to .bashrc. Such that python --version outputs 3.6 when you check after login
2-) Edit scripts/chord.sh for bootstrap node and other chord nodes in cluster
## To Start the cluster
```
scripts/chord.sh START
```
## To Stop the cluster
```
scripts/chord.sh STOP
```