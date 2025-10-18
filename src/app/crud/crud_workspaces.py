"""CRUD operations for Workspaces"""
from fastcrud import FastCRUD

from ..models.rag.workspace import Workspace
from ..schemas.rag.workspace import WorkspaceCreate, WorkspaceRead, WorkspaceUpdate

CRUDWorkspace = FastCRUD[Workspace, WorkspaceCreate, WorkspaceUpdate, WorkspaceUpdate, WorkspaceRead, WorkspaceRead]
crud_workspaces = CRUDWorkspace(Workspace)
