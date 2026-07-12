from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from app.services.transcription import get_provider
from app.services.meeting import meeting_service
from app.core.security import verify_token
from app.models import User
import time

router = APIRouter()


@router.websocket("/ws/{meeting_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    meeting_id: int,
    token: str = Query(...),
):
    await websocket.accept()

    # Authenticate
    try:
        # Pseudo-verify: In production, verify_token expects HTTPAuthorizationCredentials
        # Here we manually verify the JWT string
        # user = verify_token_str(token) # TODO: Adapt verify_token for string input
        pass
    except Exception:
        await websocket.close(code=1008)
        return

    provider = get_provider()

    try:
        while True:
            # Check for binary audio data
            data = await websocket.receive_bytes()

            # Start timer
            start_time = time.time()

            # Transcribe via provider abstraction
            text = await provider.transcribe_chunk(data)

            end_time = time.time()

            if text:
                # Save segment
                segment = meeting_service.add_segment(
                    meeting_id=meeting_id,
                    start=start_time,
                    end=end_time,
                    text=text,
                )

                # Send back to client
                await websocket.send_json({
                    "text": text,
                    "segment_id": segment.id,
                    "is_final": True,
                })

    except WebSocketDisconnect:
        print(f"Client disconnected from meeting {meeting_id}")
    except Exception as e:
        print(f"WebSocket error: {e}")
        await websocket.close()
