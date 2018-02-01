from Coach import Coach
from achess.ChessGame import ChessGame as Game
from achess.pytorch.NNet import NNetWrapper as nn
from utils import *

args = dotdict({
    'numIters': 1000,
    'numEps': 1,
    'tempThreshold': 15,
    'updateThreshold': 0.6,
    'maxlenOfQueue': 200000,
    'numMCTSSims': 25,
    'arenaCompare': 40,
    'cpuct': 1,
    'checkpoint': './temp/',
    'load_model': False,
    'load_folder_file': ('/dev/models/8x100x50','best.pth.tar'),
})

if __name__=="__main__":
    g = Game()
    nnet = nn(g)

    if args.load_model:
        nnet.load_checkpoint(args.load_folder_file[0], args.load_folder_file[1])

    t = []
    for i in range(10):
        c = Coach(g, nnet, args)
        t.append(c.learn())
    import numpy as np
    print(np.mean(t))
