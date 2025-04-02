import os
from geojson_pydantic import Point
from pydantic import BaseModel, Field, model_validator
from typing import Any, Literal, Optional, Self
from uuid import UUID
from datetime import datetime, timedelta, timezone


from eusi.models import (
    FeasibilityAsyncResponse,
    FeasibilitySyncResponse,
    TaraOrderResponse,
    FeasibilityRequest,
    TaraParametersRequest,
    TaraProductionParametersRequest,
    TaraQuote,
    TaraSubOrderResponse,
    TaraSuborder,
    TaraOrderParameters,
    TaraSuborderRequest,
    TimeWindow,
    MaxarConstraints,
    MaxarOpportunityProperties,
    MaxarOrderParameters
)
from eusi.backends import get_opportunity_search_record, search_opportunities_async, create_order
from stapi_fastapi.models.shared import Link
from stapi_fastapi.models.opportunity import (
    Opportunity,
    OpportunityCollection,
    OpportunityProperties,
    OpportunitySearchRecord,
    OpportunityPayload,
    OpportunitySearchStatus,
    OpportunitySearchStatusCode
)
from stapi_fastapi.models.order import (
    Order,
    OrderPayload,
    OrderProperties,
    OrderParameters,
    OrderStatus,
    OrderStatusCode,
    OrderSearchParameters
)
from stapi_fastapi.models.product import (
    Product,
    Provider,
    ProviderRole,
)

from stapi_fastapi.models.constraints import (
    Constraints
)

from stapi_fastapi.types.datetime_interval import DatetimeInterval




    

feasibility_status_map = {
    "CALCULATING": "in_progress",
    "FINISHED": "completed",
    "FAILED": "failed",
    "CANCELLED": "canceled"
}

order_status_map = {
    "QUOTED":"received",
    "ACTIVE":"accepted",
    "PROCESSING":"accepted",
    "DELIVERING":"processing",
    "COMPLETE":"completed",
    "CANCELLED":"user_canceled",
    "FAILED":"canceled",
    "REJECTED":"canceled"
}

eusi = Provider(
    name="EUSI",
    description="Provides Maxar Imagery",
    roles=[ProviderRole.processor],  # Example role
    url="https://www.euspaceimaging.com",  # Must be a valid URL
)

maxar = Provider(
    name="Maxar",
    description="Provides Maxar Imagery",
    roles=[ProviderRole.host],  # Example role
    url="https://www.euspaceimaging.com",  # Must be a valid URL
)

maxar_product = Product(
    id="maxar",
    title="Maxar Optical",
    description="Optical Imagary from the Maxar constellation",
    license="proprietary",
    keywords=["eo","optical","WorldView","Legion"],
    providers=[eusi],
    create_order=create_order,
    search_opportunities=None,
    search_opportunities_async=search_opportunities_async,
    get_opportunity_collection=get_opportunity_search_record,
    constraints=MaxarConstraints,
    opportunity_properties=MaxarOpportunityProperties,
    order_parameters=MaxarOrderParameters
)


def tara_order_to_order(order_response: TaraSubOrderResponse, product_id: str) -> Order:
    order_url = f"{os.environ['TARA_BASEURL']}/api/v1/order/{order_response.orderId}"
    if order_response.parameters.orderType == 'archiveOrder':
        #TODO: fix times and archive values
        opportunity_datetime = (datetime.now(timezone.utc),datetime.now(timezone.utc))
        min_ona = 0
        max_ona = 45
        max_cc = 100
        sensors=["WV02","WV03"]
    else:
        opportunity_datetime = (order_response.taskingWindows[0].startDateTime,order_response.taskingWindows[0].endDateTime)
        min_ona = order_response.parameters.taskingParameters.minOffNadirAngle
        max_ona = order_response.parameters.taskingParameters.maxOffNadirAngle
        max_cc = order_response.parameters.taskingParameters.maxCloudCover
        sensors = order_response.parameters.taskingParameters.sensors
    return Order(
        id=str(order_response.suborderId),
        geometry=order_response.parameters.aoi,
        properties=OrderProperties(
            product_id=product_id,
            created=order_response.createTime,
            status=OrderStatus(
                status_code=OrderStatusCode("accepted"),
                timestamp=order_response.suborderStatusHistory[-1].changeDateTime
            ),
            search_parameters=OrderSearchParameters(
                datetime=opportunity_datetime,
                geometry=order_response.parameters.aoi
            ),
            opportunity_properties=dict(MaxarOpportunityProperties(
                datetime=opportunity_datetime,
                product_id=product_id,
                maxCloudCover=max_cc,
                minOffNadirAngle=min_ona,
                maxOffNadirAngle=max_ona,
                sensors=sensors,
            )),
            order_parameters=dict(MaxarOrderParameters(
                customerReference=order_response.subreference,
                endUseCode=order_response.parameters.endUseCode,
                endUserIds=str(order_response.parameters.endUsers[0].id)
            ))
        ),
        links=[Link(
            href=order_url,
            rel="order"
        )]
    )


def tara_order_to_order_status(order_response: TaraSubOrderResponse, product_id: str) -> list[OrderStatus]:
    statuslist = []
    for status in order_response.suborderStatusHistory:
        statuslist.append(OrderStatus(
            timestamp=status.changeDateTime,
            status_code=OrderStatusCode(order_status_map[status.newStatus])
        ))
    return statuslist

def opportunity_request_to_feasibility(search: OpportunityPayload):
    return FeasibilityRequest(
        sensors=["WV02","WV03","GE01"],
        resolution=0.5,
        maxCloudCover=100,
        taskingPriority="Select",
        isStereo=False,
        areaOfInterest=search.geometry,
        timeWindows=[TimeWindow(
            startDateTime=search.datetime[0],
            endDateTime=search.datetime[1]
        )]
    )

def order_to_tara_order(order_request: Order):

    return TaraQuote(
        customerReference=order_request.customerReference,
        purchaseOrderNo=order_request.purchaseOrderNo,
        suborders=[
            TaraSuborder(
                subreference='stapi_test',
                provider='Maxar',
                parameters=TaraParametersRequest(
                    aoi=order_request.geometry,
                    aoiName='stapi_test',
                    orderType='taskingOrder'
                ),
            )
        ]

    )

'''
def tara_status_code_to_stapi_code(order_status: str) -> str:

'''

def tara_feasibility_response_to_search_record(search: OpportunityPayload,feasibility_request_response: FeasibilitySyncResponse) -> OpportunitySearchRecord:
    feasibility_url = f"{os.environ['TARA_BASEURL']}/api/v1/order/{feasibility_request_response.feasibility_request_id}"
    received_status = OpportunitySearchStatus(
            timestamp=datetime.now(timezone.utc),
            status_code=OpportunitySearchStatusCode.received,
        )
    search_record = OpportunitySearchRecord(
        id=str(feasibility_request_response.feasibility_request_id),
        product_id="maxar",
        opportunity_request=search,
        status=received_status,
        links=[Link(
            href=feasibility_url,
            rel="feasibility"
        )],
    )
    return search_record

def tara_feasibility_to_search_record(feasibility_id: UUID, feasibility_response: FeasibilityAsyncResponse, product_id:str) -> OpportunitySearchRecord:
    feasibility_url = f"{os.environ['TARA_BASEURL']}/api/v1/feasibility/{feasibility_id}"
    search_record = OpportunitySearchRecord(
        id=feasibility_id,
        product_id=product_id,
        opportunity_request=OpportunityPayload(
            datetime=(datetime.now(timezone.utc),datetime.now(timezone.utc)),
            geometry=Point(
                type="Point",
                coordinates=(0,0)
            )
        ),
        status=OpportunitySearchStatus(
            timestamp=datetime.now(timezone.utc),
            status_code=OpportunitySearchStatusCode(feasibility_status_map[feasibility_response.status])
        ),
        links=[Link(
            href=feasibility_url,
            rel="feasibility"
        )]
    )
    return search_record

def order_request_to_tara_quote_request(order_request: OrderPayload):
    quote = TaraQuote(
        customerReference="STAPI Test",
        purchaseOrderNo="STAPI Test",
        suborders=[
            TaraSuborderRequest(
                subreference="",
                provider="Maxar",
                parameters=TaraParametersRequest(
                    orderType='taskingOrder',
                    aoi=order_request.geometry,
                    feasibilityId=order_request.order_parameters.opportunityRequestId,
                    endUseCode=order_request.order_parameters.endUseCode,
                    endUserIds=[order_request.order_parameters.endUserIds],
                    productionParameters=TaraProductionParametersRequest(
                        productLevel=order_request.order_parameters.productLevel,
                        bandCombination=order_request.order_parameters.bandCombination,
                        resolution=order_request.order_parameters.resolution,
                    )

                )
            )]
        
    )
    return quote
