from pydantic import BaseModel 
from typing import Optional

class ProcessRequest(BaseModel):

    file_id: Optional[str] = None
    chunk_size: int = 400
    overlap_size: Optional[int] = 20
    do_reset: Optional[int] = 0