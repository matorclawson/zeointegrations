"""MIT port of VeyraX provider operations; custody removed.
Source: VeyraX/veyrax-platform@1cdddde9d5d76b9891896ca78a95e069647e81df
Path: aci_server/integrations/dropbox/client.py
Copyright VeyraX contributors. See NOTICE and VeyraX-LICENSE.
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel


class DropboxFile(BaseModel):
    id: str
    name: str
    path_display: str
    path_lower: str
    mime_type: str | None
    size: int | None
    is_folder: bool
    created_time: datetime
    modified_time: datetime
    shared_link: str | None = None
    component: dict[str, Any] | None = None


class FileList(BaseModel):
    files: list[DropboxFile]
    cursor: str | None
    has_more: bool


class FileUpload(BaseModel):
    path: str
    mode: str | None = "add"


class FolderCreate(BaseModel):
    path: str


class FileMove(BaseModel):
    from_path: str
    to_path: str

    class Config:
        json_schema_extra = {
            "example": {"from_path": "/example.txt", "to_path": "/folder/example.txt"}
        }


class FileFilters(BaseModel):
    path: str | None = ""
    recursive: bool | None = False
    limit: int | None = 20


class SearchResult(BaseModel):
    files: list[DropboxFile]
    cursor: str | None = None
    has_more: bool


class ApiResponse(BaseModel):
    data: DropboxFile | FileList | SearchResult
    component: dict[str, Any] | list[dict[str, Any]] | None = None


# New parameter classes for routes
class ListFilesParams(BaseModel):
    filters: FileFilters | None = FileFilters()


class GetFileParams(BaseModel):
    path: str


class CreateFolderParams(BaseModel):
    folder: FolderCreate
    autorename: bool | None = False


class UploadFileParams(BaseModel):
    path: str
    file_content: str  # base64 encoded
    mode: str | None = "add"


class DownloadFileParams(BaseModel):
    path: str


class DeleteFileParams(BaseModel):
    path: str


class MoveFileParams(BaseModel):
    from_path: str
    to_path: str


class ReadFileParams(BaseModel):
    path: str


class ListFilesResponse(BaseModel):
    data: FileList
    message: str | None = None


class GetFileResponse(BaseModel):
    data: DropboxFile
    message: str | None = None


class CreateFolderResponse(BaseModel):
    data: DropboxFile
    message: str | None = None


class UploadFileResponse(BaseModel):
    data: DropboxFile
    message: str | None = None


class DownloadFileResponse(BaseModel):
    data: dict[str, Any]
    message: str | None = None


class DeleteFileResponse(BaseModel):
    data: DropboxFile
    message: str | None = None


class MoveFileResponse(BaseModel):
    data: DropboxFile
    message: str | None = None


class ReadFileResponse(BaseModel):
    data: dict[str, Any]
    message: str | None = None


class RequestedVisibility(str, Enum):
    PUBLIC = "public"
    TEAM_ONLY = "team_only"
    PASSWORD = "password"
    TEAM_AND_PASSWORD = "team_and_password"
    SHARED_FOLDER_ONLY = "shared_folder_only"


class Audience(str, Enum):
    PUBLIC = "public"
    TEAM = "team"
    NO_ONE = "no_one"


class Access(str, Enum):
    VIEWER = "viewer"
    EDITOR = "editor"
    MAX = "max"


class SharedLinkSettings(BaseModel):
    requested_visibility: RequestedVisibility | None = RequestedVisibility.PUBLIC
    audience: Audience | None = Audience.PUBLIC
    access: Access | None = Access.VIEWER
    allow_download: bool | None = True


class CreateSharedLinkParams(BaseModel):
    path: str
    settings: SharedLinkSettings | None = None


class CreateSharedLinkResponse(BaseModel):
    data: DropboxFile
    message: str | None = None


# New classes for search functionality
class SearchParams(BaseModel):
    query: str
    path: str | None = ""
    max_results: int | None = 20
    filename_only: bool | None = False
    file_status: str | None = "active"


class SearchContinueParams(BaseModel):
    cursor: str


class SearchResponse(BaseModel):
    data: SearchResult
    message: str | None = None


class SearchContinueResponse(BaseModel):
    data: SearchResult
    message: str | None = None
