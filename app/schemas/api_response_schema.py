from typing import Generic, TypeVar, Optional
from pydantic.generics import GenericModel

T = TypeVar('T')

class APIResponse(GenericModel, Generic[T]):
    message: str
    status: int
    success: bool
    data: Optional[T]
