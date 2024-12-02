from dlgo import gotypes

def board_to_dict(board):
    # 바둑판 상태를 JSON 직렬화 가능한 형태로 변환
    board_dict = {
        'size': board.num_rows,
        'stones': []
    }
    
    for row in range(1, board.num_rows + 1):
        for col in range(1, board.num_cols + 1):
            point = gotypes.Point(row=row, col=col)
            stone = board.get(point)
            if stone is not None:
                board_dict['stones'].append({
                    'row': row,
                    'col': col,
                    'color': 'black' if stone == gotypes.Player.black else 'white'
                })
    
    return board_dict