## uvicorn main:app --reload

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dlgo.gotypes import Point, Player
from dlgo.goboard_fast import Move, GameState
from dlgo.utils import print_board
from typing import List, Optional

app = FastAPI()

origins = [
    "http://localhost:5173",    # Vite 개발 서버
    "http://localhost:3000",    # 다른 포트를 사용할 경우를 대비
    "http://127.0.0.1:5173",   # localhost 대신 IP를 사용하는 경우
]

# CORS 미들웨어 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,      # 위에서 정의한 origins 사용
    allow_credentials=True,
    allow_methods=["*"],        # 모든 HTTP 메서드 허용
    allow_headers=["*"],        # 모든 헤더 허용
)

game_state = GameState.new_game(19)

class MoveRequest(BaseModel):
    row: int
    col: int

class BoardState(BaseModel):
    status: str
    board: List[List[Optional[int]]]  # None 값을 허용하도록 Optional 추가
    next_player: int

@app.post("/move")
async def make_move(move: MoveRequest):

    global game_state
    point = Point(row=move.row, col=move.col)
    play = Move.play(point)
    print(f'make_move: {move.row}, {move.col}')
    print("Current board state:")
    print("Next player:", game_state.next_player)
    
    if game_state.is_valid_move(play):
        game_state = game_state.apply_move(play)
        board_state = []
        for row in range(1, game_state.board.num_rows + 1):
            row_state = []
            for col in range(1, game_state.board.num_cols + 1):
                stone = game_state.board.get(Point(row=row, col=col))
                # None -> '', 'black' -> 'B', 'white' -> 'W'로 변환
                if stone is None:
                    row_state.append(None)
                elif stone == Player.black:
                    row_state.append(1)
                else:
                    row_state.append(2)
            board_state.append(row_state)
        
        # 다음 플레이어 정보
        next_player = 1 if game_state.next_player == Player.black else 2
        print_board(game_state.board)   
        return BoardState(
            status="success",
            board=board_state,
            next_player=next_player
        )
    else:
        raise HTTPException(status_code=400, detail="Invalid move")