import os
import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from pydantic_settings import BaseSettings
import uvicorn

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from stapi_fastapi.models.conformance import CORE,ASYNC_OPPORTUNITIES
from stapi_fastapi.routers.root_router import RootRouter

from eusi.shared import maxar_product
from eusi.client import TARAClient
from eusi.backends import (
    get_order,
    get_orders,
    get_order_statuses,
    get_opportunity_search_record,
    get_opportunity_search_records
)
root_router = RootRouter(
    get_orders=get_orders,
    get_order=get_order,
    get_order_statuses=get_order_statuses,
    get_opportunity_search_records=get_opportunity_search_records,
    get_opportunity_search_record=get_opportunity_search_record,
    conformances=[CORE,ASYNC_OPPORTUNITIES]
)

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[dict[str, Any]]:
    try:
        yield {
            "_TARA": TARAClient(os.environ['TARA_BASEURL']),
        }
    finally:
        pass

root_router.add_product(maxar_product)

class ProdSettings(BaseSettings):
    port: int = int(os.environ['PORT'])
    host: str = os.environ['HOST']
    root: str = os.environ['ROOT_PATH']

settings = ProdSettings()
app: FastAPI = FastAPI(lifespan=lifespan,root_path=settings.root)
app.include_router(root_router, prefix="")

if __name__ == "__main__":
    uvicorn.run(app=app,port=settings.port,host=settings.host)