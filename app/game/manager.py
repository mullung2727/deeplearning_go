from dlgo import goboard_fast, gotypes

class GameManager:
    def __init__(self):
        self.board = goboard_fast.Board(19, 19)
        self.game = goboard_fast.GameState.new_game(19)
    
    # 게임 상태 관리 메서드들