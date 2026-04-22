import uuid

import structlog
from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlmodel import Session

from app.api.deps import get_current_user
from app.core.db import get_session
from app.models.org import OrgRole
from app.models.user import User
from app.schemas.files import FileResponse, PresignedUrlResponse
from app.services.files import files_service
from app.services.orgs import org_service

router = APIRouter(prefix="/api/v1/files", tags=["files"])
logger = structlog.get_logger()


@router.post("/", response_model=FileResponse, status_code=201)
async def upload_file(
    org_id: uuid.UUID,
    file: UploadFile,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    membership = org_service.get_membership(
        session, org_id=org_id, user_id=current_user.id
    )
    if not membership:
        raise HTTPException(status_code=403, detail="Not a member of this organization")

    # Use file.size if available (FastAPI 0.95+), otherwise we might need to seek
    size = file.size
    if size is None:
        # Fallback if size is not populated
        file.file.seek(0, 2)
        size = file.file.tell()
        file.file.seek(0)

    storage_key = f"{org_id}/{uuid.uuid4()}/{file.filename}"
    content_type = file.content_type or "application/octet-stream"

    # Stream the file directly
    files_service.upload(
        data=file.file,
        length=size,
        storage_key=storage_key,
        content_type=content_type
    )

    f = files_service.save_metadata(
        session,
        org_id=org_id,
        uploaded_by=current_user.id,
        filename=file.filename or "unnamed",
        storage_key=storage_key,
        content_type=content_type,
        size_bytes=size,
    )

    session.commit()
    session.refresh(f)

    return FileResponse.model_validate(f)


@router.get("/{file_id}/url", response_model=PresignedUrlResponse)
def get_file_url(
    file_id: uuid.UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    f = files_service.get_active_file(session, file_id=file_id)
    if not f:
        raise HTTPException(status_code=404, detail="File not found")

    membership = org_service.get_membership(
        session, org_id=f.org_id, user_id=current_user.id
    )
    if not membership:
        raise HTTPException(status_code=403, detail="Not a member of this organization")

    url = files_service.presigned_url(f.storage_key)
    return PresignedUrlResponse(url=url)


@router.delete("/{file_id}", status_code=204)
def delete_file(
    file_id: uuid.UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    f = files_service.get_active_file(session, file_id=file_id)
    if not f:
        raise HTTPException(status_code=404, detail="File not found")

    membership = org_service.get_membership(
        session, org_id=f.org_id, user_id=current_user.id
    )
    if not membership:
        raise HTTPException(status_code=403, detail="Not a member of this organization")

    if f.uploaded_by != current_user.id and membership.role not in (
        OrgRole.owner,
        OrgRole.admin,
    ):
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    files_service.soft_delete(session, file=f)
    session.commit()
