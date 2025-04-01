import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI

from stapi_fastapi.models.conformance import CORE,ASYNC_OPPORTUNITIES
from stapi_fastapi.routers.root_router import RootRouter

from src.eusi.shared import maxar_product
from src.eusi.client import TARAClient
from src.eusi.backends import (
    get_order,
    get_orders,
    get_order_statuses,
    get_opportunity_search_record,
)
root_router = RootRouter(
    get_orders=get_orders,
    get_order=get_order,
    get_order_statuses=get_order_statuses,
    get_opportunity_search_records=get_opportunity_search_record,
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
app: FastAPI = FastAPI(lifespan=lifespan)
app.include_router(root_router, prefix="")