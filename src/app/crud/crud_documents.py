"""CRUD operations for Documents"""
from fastcrud import FastCRUD

from ..models.rag.document import Document
from ..schemas.rag.document import DocumentRead

CRUDDocument = FastCRUD[Document, DocumentRead, DocumentRead, DocumentRead, DocumentRead, DocumentRead]
crud_documents = CRUDDocument(Document)
