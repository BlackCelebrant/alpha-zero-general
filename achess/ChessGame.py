
import sys
sys.path.append('..')
import numpy as np
import chess

from Game import Game
from achess.chess_utils import create_uci_labels


N_ACTIONS = len(create_uci_labels())
BOARD_SIZE = (8, 8, 18)


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
        return BOARD_SIZE
    
    def getActionSize(self):
        return N_ACTIONS
    
    def getNextState(self, board, player, action):
        board.push_uci(action)
        return (board, -player)
        
    def getValidMoves(self, board, player):
        return [str(a) for a in board.legal_moves]
    
    def getGameEnded(self, board, player):
        """
        Return 0 if not ended, 1 if player 1 won, -1 if player 1 lost.
        TODO: check condition for draw.
        """
        result = self.board.result(claim_draw = True)
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
        TODO: convert "fen" to actual state.
        """
        flip = player == -1
        return np.zeros((8, 8, 18))
    
    def getSymmetries(self, board, pi):
        return None
    
    def stringRepresentation(self, board):
        return board.fen()
        
        
        
        
        
        
    