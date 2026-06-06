from pydantic import BaseModel

class OrderCreate(BaseModel):

    service_name: str

    price: int