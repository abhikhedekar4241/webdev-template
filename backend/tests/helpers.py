import uuid

from app.core.security import create_access_token


def get_auth_header(user_id: uuid.UUID) -> dict:
    token = create_access_token(subject=str(user_id))
    return {"Authorization": f"Bearer {token}"}
