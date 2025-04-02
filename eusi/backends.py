
from fastapi import Request
from returns.maybe import Maybe, Nothing, Some
from returns.result import Failure, ResultE, Success

from src.stapi_fastapi.models.opportunity import OpportunityPayload, OpportunitySearchRecord
from src.stapi_fastapi.routers.product_router import ProductRouter
from stapi_fastapi.models.order import (
    Order,
    OrderPayload,
    OrderProperties,
    OrderSearchParameters,
    OrderStatus,
    OrderStatusCode,
)



async def get_order(order_id: str, request: Request) -> ResultE[Maybe[Order]]:
    """
    Show details for order with `order_id`.
    """
    try:
        return Success(
            Maybe.from_optional(request.state._TARA.get_order(request.headers['Authorization'], order_id))
        )
    except Exception as e:
        return Failure(e)

async def get_orders(
    next: str | None, limit: int, request: Request
) -> ResultE[tuple[list[Order], Maybe[str]]]:
    try:
        start = 0
        limit = min(limit, 100)
        orders = request.state._TARA.get_orders(request.headers['Authorization'],limit)
        print(orders)
        if orders is None:
            return Success(Nothing)

        if next:
            start = int(next)
        end = start + limit
        ords = orders[start:end]

        if end > 0 and end < len(orders):
            return Success(Some((ords, Some(str(end)))))
        return Success(Some((ords, Nothing)))
    except Exception as e:
        return Failure(e)
    
async def get_order_statuses(
    order_id: str, next: str | None, limit: int, request: Request
) -> ResultE[Maybe[tuple[list[OrderStatus], Maybe[str]]]]:
    try:
        start = 0
        limit = min(limit, 100)
        statuses = request.state._TARA.get_order_statuses(request.headers['Authorization'],order_id,limit)
        if statuses is None:
            return Success(Nothing)

        if next:
            start = int(next)
        end = start + limit
        stati = statuses[start:end]

        if end > 0 and end < len(statuses):
            return Success(Some((stati, Some(str(end)))))
        return Success(Some((stati, Nothing)))
    except Exception as e:
        return Failure(e)
    
async def search_opportunities_async(
    product_router: ProductRouter,
    search: OpportunityPayload,
    request: Request,
) -> ResultE[OpportunitySearchRecord]:
    try:
        return Success(request.state._TARA.get_opportunity_from_feasibility(request.headers['Authorization'],search))

    except Exception as e:
        return Failure(e)

async def create_order(
    product_router: ProductRouter, payload: OrderPayload, request: Request
) -> ResultE[Order]:
    """
    Create a new order.
    """
    try:
        created_order = request.state._TARA.create_order(request.headers['Authorization'],payload)
        print(created_order)
        return Success(
            created_order
        )
    
    except Exception as e:
        return Failure(e)

async def get_opportunity_search_record(
    search_record_id: str, request: Request
) -> ResultE[Maybe[OpportunitySearchRecord]]:
    try:
        return Success(
            Maybe.from_optional(
                request.state._TARA.get_feasibility_result(request.headers['Authorization'],search_record_id)
            )
        )
    except Exception as e:
        return Failure(e) 

async def get_opportunity_search_records(
    next: str | None,
    limit: int,
    request: Request,
) -> ResultE[tuple[list[OpportunitySearchRecord], Maybe[str]]]:
    try:
        start = 0
        limit = min(limit, 100)
        search_records = request.state._TARA.get_feasibility_results(request.headers['Authorization'],limit)

        if next:
            start = int(next)
        end = start + limit
        page = search_records[start:end]

        if end > 0 and end < len(search_records):
            return Success((page, Some(str(end))))
        return Success((page, Nothing))
    except Exception as e:
        return Failure(e)