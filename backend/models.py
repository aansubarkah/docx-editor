from typing import List, Optional, Literal
from pydantic import BaseModel

# Operation types, now supporting stable anchors by paragraph_id
OpType = Literal["add_heading", "add_paragraph", "replace_text", "insert_table", "edit_table", "remove_table", "remove_paragraph"]

class Operation(BaseModel):
    type: OpType
    text: Optional[str] = None
    level: Optional[int] = None  # for add_heading
    after_paragraph_id: Optional[str] = None  # stable anchor from outline
    after_heading_text: Optional[str] = None  # fallback (legacy)
    find: Optional[str] = None
    replace: Optional[str] = None
    rows: Optional[int] = None
    cols: Optional[int] = None
    data: Optional[List[List[str]]] = None
    table_index: Optional[int] = None  # for edit_table (0-based index)
    cell_row: Optional[int] = None  # for edit_table cell editing
    cell_col: Optional[int] = None  # for edit_table cell editing
    cell_text: Optional[str] = None  # for edit_table cell editing
    add_header_row: Optional[bool] = None  # for insert_table styling

class PlanOpsRequest(BaseModel):
    file_id: Optional[str] = None
    instruction: str

class ApplyOpsRequest(BaseModel):
    file_id: str
    operations: List[Operation]

class CreateDocRequest(BaseModel):
    title: str = "New Document"
    body: Optional[str] = None

class OutlineItem(BaseModel):
    paragraph_id: str
    text: str
    level: int  # 0 for body para, 1..6 for headings
