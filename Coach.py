from collections import deque
from Arena import Arena
from MCTS import MCTS
import numpy as np
from pytorch_classification.utils import Bar, AverageMeter
import time
from achess.ChessGame import idx2act

class Coach():
    """
    This class executes the self-play + learning. It uses the functions defined
    in Game and NeuralNet. args are specified in main.py.
    """
    def __init__(self, game, nnet, args):
        self.game = game
        self.board = game.getInitBoard()
        self.nnet = nnet
        self.args = args
        self.mcts = MCTS(self.game, self.nnet, self.args)

    def executeEpisode(self):
        """
        This function executes one episode of self-play, starting with player 1.
        As the game is played, each turn is added as a training example to
        trainExamples. The game is played till the game ends. After the game
        ends, the outcome of the game is used to assign values to each example
        in trainExamples.

        It uses a temp=1 if episodeStep < tempThreshold, and thereafter
        uses temp=0.

        Returns:
            trainExamples: a list of examples of the form (canonicalBoard,pi,v)
                           pi is the MCTS informed policy vector, v is +1 if
                           the player eventually won the game, else -1.
        """
        trainExamples = []
        self.board = self.game.getInitBoard()
        self.curPlayer = 1
        episodeStep = 0

        while True:
            episodeStep += 1
            canonicalBoard = self.game.getCanonicalForm(self.board,self.curPlayer)
            temp = int(episodeStep < self.args.tempThreshold)

            pi = self.mcts.getActionProb(canonicalBoard, temp=temp)
            #print(len(np.where(np.array(pi) > 0)[0]))
            sym = self.game.getSymmetries(canonicalBoard, pi)
            for b,p in sym:
                trainExamples.append([b, self.curPlayer, p, None])

            action = np.random.choice(len(pi), p=pi)

            #print(self.board.fen())
            #self.print_possible_moves(pi)
            #print('Move:{}'.format(idx2act[action]))
            #print('\n')

            self.board, self.curPlayer = self.game.getNextState(self.board, self.curPlayer, action)

            r = self.game.getGameEnded(self.board, self.curPlayer)

            if r!=0:
                import pdb; pdb.set_trace()
                print(self.board.fen())
                return [(x[0],x[2],r*((-1)**(x[1]!=self.curPlayer))) for x in trainExamples]

    def print_possible_moves(self, pi):
        #print(np.array(pi)[np.array(pi) > 0])
        print('Possible:'+','.join([idx2act[i] for i in np.where(np.array(pi) > 0)[0]]))

    def learn(self):
        """
        Performs numIters iterations with numEps episodes of self-play in each
        iteration. After every iteration, it retrains neural network with
        examples in trainExamples (which has a maximium length of maxlenofQueue).
        It then pits the new neural network against the old one and accepts it
        only if it wins >= updateThreshold fraction of games.
        """

        trainExamples = deque([], maxlen=self.args.maxlenOfQueue)
        for i in range(self.args.numIters):
            # bookkeeping
            print('------ITER ' + str(i+1) + '------')
            eps_time = AverageMeter()
            bar = Bar('Self Play', max=self.args.numEps)
            end = time.time()

            for eps in range(self.args.numEps):
                self.mcts = MCTS(self.game, self.nnet, self.args)   # reset search tree
                trainExamples += self.executeEpisode()                

                # bookkeeping + plot progress
                eps_time.update(time.time() - end)
                end = time.time()
                bar.suffix  = '({eps}/{maxeps}) Eps Time: {et:.3f}s | Total: {total:} | ETA: {eta:}'.format(eps=eps+1, maxeps=self.args.numEps, et=eps_time.avg,
                                                                                                           total=bar.elapsed_td, eta=bar.eta_td)
                bar.next()
            bar.finish()

            # training new network, keeping a copy of the old one
            self.nnet.save_checkpoint(folder=self.args.checkpoint, filename='temp.pth.tar')
            pnet = self.nnet.__class__(self.game)
            pnet.load_checkpoint(folder=self.args.checkpoint, filename='temp.pth.tar')
            pmcts = MCTS(self.game, pnet, self.args)
            self.nnet.train(trainExamples)
            nmcts = MCTS(self.game, self.nnet, self.args)

            print('PITTING AGAINST PREVIOUS VERSION')
            arena = Arena(lambda x: np.argmax(pmcts.getActionProb(x, temp=0)),
                          lambda x: np.argmax(nmcts.getActionProb(x, temp=0)), self.game)
            pwins, nwins, draws = arena.playGames(self.args.arenaCompare)

            print('NEW/PREV WINS : ' + str(nwins) + '/' + str(pwins) + ' ; DRAWS : ' + str(draws))
            if pwins+nwins > 0 and float(nwins)/(pwins+nwins) < self.args.updateThreshold:
                print('REJECTING NEW MODEL')
                self.nnet = pnet

            else:
                print('ACCEPTING NEW MODEL')
                self.nnet.save_checkpoint(folder=self.args.checkpoint, filename='checkpoint_' + str(i) + '.pth.tar')
                self.nnet.save_checkpoint(folder=self.args.checkpoint, filename='best.pth.tar')


import multiprocessing
from achess.ChessGame import ChessGame as Game


class MCoach():
    def __init__(self, game, nnet, args):
        self.game = game
        self.board = game.getInitBoard()
        self.nnet = nnet
        self.args = args

    @staticmethod
    def executeEpisode(args_list):
        nnet = args_list[0]
        args = args_list[1]
        seed = args_list[2]
        start = time.time()
        np.random.seed(seed)
        game = Game()
        mcts = MCTS(game, nnet, args)   # reset search tree
        trainExamples = []
        board = game.getInitBoard()
        curPlayer = 1
        episodeStep = 0

        while True:
            episodeStep += 1
            canonicalBoard = game.getCanonicalForm(board, curPlayer)
            temp = int(episodeStep < args.tempThreshold)

            pi = mcts.getActionProb(canonicalBoard, temp=temp)
            #print(len(np.where(np.array(pi) > 0)[0]))
            sym = game.getSymmetries(canonicalBoard, pi)
            for b,p in sym:
                trainExamples.append([b, curPlayer, p, None])

            action = np.random.choice(len(pi), p=pi)

            #print(board.fen())
            #self.print_possible_moves(pi)
            #print('Move:{}'.format(idx2act[action]))
            #print('\n')

            board, curPlayer = game.getNextState(board, curPlayer, action)

            r = game.getGameEnded(board, curPlayer)

            if r!=0:
                print(board.fen())
                print(time.time()-start)
                return [(x[0],x[2],r*((-1)**(x[1]!=curPlayer))) for x in trainExamples]

    def learn(self):
        # TODO: play episodes in processes
        multiprocessing.set_start_method('spawn')
        pool = multiprocessing.Pool(processes=multiprocessing.cpu_count())
        start = time.time()
        pool_args = zip([self.nnet]*self.args.numEps, [self.args]*self.args.numEps,
                        range(self.args.numEps))
        res = pool.map(self.executeEpisode, pool_args)
        print('Total: {}'.format(time.time()-start))

        trainExamples = [i for sl in res for i in sl]
        self.nnet.save_checkpoint(folder=self.args.checkpoint, filename='temp.pth.tar')
        pnet = self.nnet.__class__(self.game)
        pnet.load_checkpoint(folder=self.args.checkpoint, filename='temp.pth.tar')
        pmcts = MCTS(self.game, pnet, self.args)
        self.nnet.train(trainExamples)
        nmcts = MCTS(self.game, self.nnet, self.args)

        print('PITTING AGAINST PREVIOUS VERSION')
        arena = Arena(lambda x: np.argmax(pmcts.getActionProb(x, temp=0)),
                      lambda x: np.argmax(nmcts.getActionProb(x, temp=0)), self.game)
        pwins, nwins, draws = arena.playGames(self.args.arenaCompare)

        print('NEW/PREV WINS : ' + str(nwins) + '/' + str(pwins) + ' ; DRAWS : ' + str(draws))
        if pwins+nwins > 0 and float(nwins)/(pwins+nwins) < self.args.updateThreshold:
            print('REJECTING NEW MODEL')
            self.nnet = pnet

        else:
            print('ACCEPTING NEW MODEL')
            #self.nnet.save_checkpoint(folder=self.args.checkpoint, filename='checkpoint_' + str(i) + '.pth.tar')
            self.nnet.save_checkpoint(folder=self.args.checkpoint, filename='best.pth.tar')

def test(a):
    import os
    print(os.getpid())

