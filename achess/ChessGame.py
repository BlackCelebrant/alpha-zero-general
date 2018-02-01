
import sys
sys.path.append('..')
import numpy as np
import chess

from Game import Game
from achess.ChessUtils import create_uci_labels, canon_input_planes, flip_fen

labels = create_uci_labels()
idx2act = {k:v for k, v in enumerate(labels)}
act2idx = {v:k for k,v in idx2act.items()}
n_actions = len(labels)
board_size = (18, 8, 8)


class ChessGame(Game):
    
    def __init__(self):
        pass
    
    def getInitBoard(self):
        """
        Here we create initial chess board. This function is executed by Coach class 
        every time new episode is launched.
        White is Player 1, Black is Player -1.
        """
        return chess.Board()
    
    def getBoardSize(self):
        return board_size
    
    def getActionSize(self):
        return n_actions
    
    def getNextState(self, board, player, action):
        if player == 1:
            b = chess.Board(board.fen())
        else:
            b = chess.Board(flip_fen(board.fen(), flip=True))
        b.push_uci(idx2act[action])
        if player == 1:
            b = chess.Board(b.fen())
        else:
            b = chess.Board(flip_fen(b.fen(), flip=True))
        return (b, -player)
        
    def getValidMoves(self, board, player):
        valid = [str(a) for a in board.legal_moves]
        mask = np.zeros(n_actions)
        for action in valid:
            mask[act2idx[action]] = 1
        return mask
    
    def getGameEnded(self, board, player):
        """
        Return 0 if not ended, 1 if player 1 won, -1 if player 1 lost.
        TODO: check condition for draw..
        """
        result = board.result(claim_draw = True)
        if result == '1-0':
            return 1
        elif result == '0-1':
            return -1
        elif result == '1/2-1/2':
            return 0.001
        else:
            return 0
        
    def getCanonicalForm(self, board, player):
        """
        Return instance of Board class that is flipped for Black.
        """
        if player == -1:
            board = chess.Board(flip_fen(board.fen(), flip=True))
        return board
    
    def getSymmetries(self, board, pi):
        return [[board, pi]]
    
    def stringRepresentation(self, board):
        """
        Converting board to string (they will be keys in dictionary).
        """
        return board.fen()
