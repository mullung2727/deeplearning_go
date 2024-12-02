import copy
from dlgo.gotypes import Player


# Move 생성자를 직접 호출하지 않고 Move.play(), Move.pass_turn(), Move.resign()을 호출하여 사용
class Move():
    def __init__(self, point=None, is_pass=False, is_resign=False):
        assert (point is not None) ^ is_pass ^ is_resign
        self.point = point
        self.is_play = (self.point is not None)
        self.is_pass = is_pass 
        self.is_resign = is_resign 
        
    @classmethod
    def play(cls, point): # 이 수는 바둑판에 돌을 놓는다
        return Move(point=point)
    
    @classmethod
    def pass_turn(cls): # 이 수는 차례를 넘긴다
        return Move(is_pass=True)
    
    @classmethod
    def resign(cls, point): # 이 수는 현대 대국을 포기한다
        return Move(is_resign=True)
    
    
class GoString(): # 이음 : 같은 색 돌이 연결된 그룹을 이음이라고 함
    def __init__(self, color, stones, liberties):
        self.color = color
        self.stones = set(stones)
        self.liberties = set(liberties)
        
    def remove_liberty(self, point):
        self.liberties.remove(point)
    
    def add_liberty(self, point):
        self.liberties.add(point)
    
    def merged_with(self, go_string): # 양 선수의 이음의 모든 돌을 저장한 새 이음을 반환
        assert go_string.color == self.color
        combined_stones = self.stones | go_string.stones
        return GoString(
            self.color, 
            combined_stones, 
            (self.liberties | go_string.liberties) - combined_stones)
        
    @property
    def num_liberties(self): # 활로의 개수를 파악
        return len(self.liberties)
    
    def __eq__(self, other):
        return isinstance(other, GoString) and \
            self.color == other.color and \
            self.stones == other.stones and \
            self.liberties == other.liberties
            
            
class Board():
    def __init__(self, num_rows, num_cols):
        self.num_rows = num_rows
        self.num_cols = num_cols
        self._grid = {}
    
    def place_stone(self, player, point):
        assert self.is_on_grid(point) # 점이 바둑판 내에 있는지 확인
        assert self._grid.get(point) is None # 점에 돌이 이미 있는지 확인
        adjacent_same_color = []
        adjacent_opposite_color = []
        liberties=[]
        for neighbor in point.neighbors(): # 우선 이 점과 바로 연결된 이웃을 확인한다.
            if not self.is_on_grid(neighbor):
                continue
            neighbor_string = self._grid.get(neighbor)
            if neighbor_string is None:
                liberties.append(neighbor)
            elif neighbor_string.color == player:
                if neighbor_string not in adjacent_same_color:
                    adjacent_same_color.append(neighbor_string)
            else:
                if neighbor_string not in adjacent_opposite_color:
                    adjacent_opposite_color.append(neighbor_string)
        new_string = GoString(player, [point], liberties)
        for same_color_string in adjacent_same_color: # 같은 색의 근접한 이음을 합친다.
            new_string = new_string.merged_with(same_color_string)
        for new_string_point in new_string.stones:
            self._grid[new_string_point] = new_string
        for other_color_string in adjacent_opposite_color: # 다른 색의 근접한 이음의 활로를 줄인다
            other_color_string.remove_liberty(point)
        for other_color_string in adjacent_opposite_color: # 다른 색 이음의 활로가 0이 되면 그 돌을 제거
            if other_color_string.num_liberties == 0:
                self._remove_string(other_color_string)
    
    def is_on_grid(self, point):
        return 1 <= point.row <= self.num_rows and 1 <=point.col <=self.num_cols
    
    def get(self, point): # 바둑판 위의 점 내용을 반환한다. 만약 돌이 해당 점 위에 있으면 Player를 반환하고, 아니면 None을 반환한다
        string = self._grid.get(point)
        if string is None:
            return None
        return string.color
    
    def get_go_string(self, point): # 해당 점의 돌에 연결된 모든 이음을 반환. 만약 돌이 해당 점 위에 있으면 GoString을 반환하고, 아니면 None을 반환한다. 자충수를 막을 때 유용
        string = self._grid.get(point)
        if string is None:
            return None
        return string
    
    def _remove_string(self, string):
        for point in string.stones:
            for neighbor in point.neighbors():
                neighbor_string = self._grid.get(neighbor)
                if neighbor_string is None:
                    continue
                if neighbor_string is not string:
                     neighbor_string.add_liberty(point)
            self._grid[point] = None
            
class GameState(): # 대국 현황 : 현재 판 상태, 다음 선수, 이전 상태, 직전 수를 기록
    def __init__(self, board, next_player, previous, move):
        self.board = board
        self.next_player = next_player
        self.previous_state = previous
        self.last_move = move
        
    def apply_move(self, move):
        if move.is_play:
            next_board = copy.deepcopy(self.board)
            next_board.place_stone(self.next_player, move.point)
        else:
            next_board = self.board
        return GameState(next_board, self.next_player.other, self, move)
    
    @classmethod
    def new_game(cls, board_size):
        if isinstance(board_size, int):
            board_size =(board_size, board_size)
        board = Board(*board_size)
        return GameState(board, Player.black, None, None)
    
    def is_over(self):
        if self.last_move is None:
            return False
        if self.last_move.is_resign:
            return True
        second_last_move = self.previous_state.last_move
        if second_last_move is None:
            return False
        return self.last_move.is_pass and second_last_move.is_pass
    
    def is_move_self_capture(self, player, move): # 자충수
        if not move.is_play:
            return False
        next_board = copy.deepcopy(self.board)
        next_board.place_stone(player, move.point)
        new_string = next_board.get_go_string(move.point)
        return new_string.num_liberties == 0
    
    @property
    def situation(self):
        return (self.next_player, self.board)
    
    def does_move_violate_ko(self, player, move): # 패 규칙 위반 판단
        if not move.is_play:
            return False
        next_board = copy.deepcopy(self.board)
        next_board.place_stone(player, move.point)
        next_situation = (player.other, next_board)
        past_state = self.previous_state
        while past_state is not None:
            if past_state.situation == next_situation:
                return True
            past_state = past_state.previous_state
        return False
    
    def is_valid_move(self, move):
        if self.is_over():
            return False
        if move.is_pass or move.is_resign:
            return True
        return (
            self.board.get(move.point) is None and
            not self.is_move_self_capture(self.next_player, move) and
            not self.does_move_violate_ko(self.next_player, move)
        )