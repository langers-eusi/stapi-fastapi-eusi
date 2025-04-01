import os
from typing import List
from fastapi import Header
from uuid import UUID

from pydantic import TypeAdapter
import httpx
import json

from stapi_fastapi.models.order import (
    Order,
    OrderParameters,
    OrderPayload,
    OrderStatus,
)

from stapi_fastapi.models.opportunity import OpportunityPayload

from src.eusi.shared import (
    tara_feasibility_response_to_search_record,
    tara_feasibility_to_search_record,
    tara_order_to_order_status,
    tara_order_to_order,
    opportunity_request_to_feasibility,
    order_request_to_tara_quote_request
)
from src.eusi.models import (
    FeasibilityAsyncResponse,
    TaraOrderAcceptResponse,
    TaraSubOrderResponse,
    TaraQuoteResponse,
    TaraOrderAcceptRequest,
    FeasibilityRequest,
    FeasibilitySyncResponse
)

class AuthorizationError(Exception):
    pass

class TARAClient:
    def __init__(self, tara_api_url: str) -> None:
        self.tara_api_url = tara_api_url


    def get_order(self, authtoken: str, order_id: str) -> Order:
        headers = {"Authorization": authtoken}
        try:
            order_id = UUID(order_id)
        except Exception:
            raise ValueError("order_id must be a valid UUID")
        order_url = f'{self.tara_api_url}/api/v1/internal/suborders/{order_id}'
        response = httpx.get(
            url=order_url,
            headers=headers,
        )
        response.raise_for_status()
        order_response = TaraSubOrderResponse.model_validate(response.json())
        print(order_response)
        return tara_order_to_order(order_response,"maxar")

    async def get_orders(self, authtoken: str, limit: int) -> list[Order]:
        headers = {"Authorization": authtoken}
        orders_url = f'{self.tara_api_url}/api/v1/internal/suborders'
        response = httpx.get(
            url=orders_url,
            headers=headers,
        )
        print(response.json())
        orderlist = [tara_order_to_order(TaraSubOrderResponse.model_validate(order),"maxar") for order in response.json()]
    
        print(response.json())
        response.raise_for_status()
        return orderlist

    def get_order_statuses(self, authtoken: str, order_id: str, limit: int) -> list[OrderStatus]:
        headers = {"Authorization": authtoken}
        order_url = f'{self.tara_api_url}/api/v1/internal/suborders/{order_id}'
        response = httpx.get(
            url=order_url,
            headers=headers,
        )
        response.raise_for_status()
        order_response = TaraSubOrderResponse.model_validate(response.json())
        print(order_response)
        return tara_order_to_order_status(order_response,"maxar")

    def get_opportunity_from_feasibility(self, authtoken: str, search: OpportunityPayload):
        headers = {"Authorization": authtoken}
        feasibility_url = f'{self.tara_api_url}/api/v1/feasibility'
        payload: FeasibilityRequest = opportunity_request_to_feasibility(search)
        response = httpx.post(
            url=feasibility_url,
            json=json.loads(payload.model_dump_json()),
            headers=headers,
        )
        feasi_response = FeasibilitySyncResponse.model_validate(response.json())
        return tara_feasibility_response_to_search_record(search,feasi_response)
    
        

    def get_feasibility_result(self, authtoken: str, feasibility_id: UUID):
        headers = {"Authorization": authtoken}
        feasibility_url = f'{self.tara_api_url}/api/v1/feasibility/{feasibility_id}'
        response = httpx.get(
            url=feasibility_url,
            headers=headers,
        )
        response.raise_for_status()
        res = response.json()
        print(res)
        res['feasibility_request_id'] = str(feasibility_id)
        feasi_response = FeasibilityAsyncResponse.model_validate(res)
        print(feasi_response)
        return tara_feasibility_to_search_record(feasibility_id=feasibility_id,feasibility_response=feasi_response,product_id="maxar")
    
    def create_order(self, authtoken: str, order: OrderPayload) -> Order:
        headers = {"Authorization": authtoken}
        quote_url = f'{self.tara_api_url}/api/v1/quote'
        accept_url = f'{self.tara_api_url}/api/v1/order/accept'
        
        payload = order_request_to_tara_quote_request(order)
        print(payload)
        response = httpx.post(
            url=quote_url,
            json=json.loads(payload.model_dump_json()),
            headers=headers
        )
        print(response.json())
        quote_response = TaraQuoteResponse.model_validate(response.json())

        order_accept = TaraOrderAcceptRequest(
            orderId=str(quote_response.orderInformation.orderId)
        )
        print(order_accept)
        response = httpx.put(
            url=accept_url,
            timeout=None,
            json=json.loads(order_accept.model_dump_json()),
            headers=headers,
        ).raise_for_status()

        order_response = TaraOrderAcceptResponse.model_validate(response.json())
        return tara_order_to_order(order_response=order_response.orderInformation.suborders[0],product_id="maxar")




    
    