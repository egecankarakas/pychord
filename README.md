# pychord
Implementation of Chord Protocol in Python
Start the first node with providing hostname or ip
python main.py --ip X.X.X.1

Start other nodes by giving an arbitrary node in chord ring
python main.py --ip X.X.X.2 --bootstrap X.X.X.1