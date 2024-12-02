from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List
from app.game.manager import GameManager

router = APIRouter()

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.game_manager = GameManager()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        # 연결 직후 현재 게임 상태 전송
        await websocket.send_json(self.game_manager.get_game_state())

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, game_state: dict):
        for connection in self.active_connections:
            await connection.send_json(game_state)

manager = ConnectionManager()

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            # 클라이언트로부터 받은 돌 놓기 요청 처리
            if data["type"] == "PLACE_STONE":
                row, col = data["row"], data["col"]
                if manager.game_manager.place_stone(row, col):
                    # 성공적으로 돌을 놓았다면 모든 클라이언트에게 새로운 게임 상태 전송
                    await manager.broadcast(manager.game_manager.get_game_state())
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    