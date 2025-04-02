from pydantic import AwareDatetime, BaseModel, Field
from geojson_pydantic import Polygon
from uuid import UUID
from typing import List, Literal, Optional, Union

from src.stapi_fastapi.models.constraints import Constraints
from src.stapi_fastapi.models.opportunity import OpportunityProperties
from src.stapi_fastapi.models.order import OrderParameters

MAXAR_SATELLITES = ["WV01","WV02","WV03","GE01"]


class TaraStatusHistory(BaseModel):
    oldStatus: str
    newStatus: str
    changeDateTime: AwareDatetime


class TaraTaskingParameters(BaseModel):
    taskingScheme: str
    taskingPriority: str
    maxCloudCover: int
    minOffNadirAngle: int
    maxOffNadirAngle: int
    sensors: list[str]

class TimeWindow(BaseModel):
    successRate: Optional[int] = None
    taskingWindowId: Optional[UUID] = None
    startDateTime: AwareDatetime
    endDateTime: AwareDatetime

class TaraEndUser(BaseModel):
    id: UUID

class TaraParametersResponse(BaseModel):
    orderType: str
    aoiName: str
    aoi: Polygon
    endUseCode: str
    endUsers: list[TaraEndUser]
    taskingParameters: TaraTaskingParameters


class TaraSubOrderResponse(BaseModel):
    orderId: UUID
    suborderId: UUID
    createTime: str
    subreference: str
    provider: str
    suborderStatus: str
    suborderStatusHistory: list[TaraStatusHistory]
    parameters: Optional[TaraParametersResponse] = None
    taskingWindows: Optional[List[TimeWindow]] = None


class TaraOrderResponse(BaseModel):
    orderId: UUID
    orderType: str
    createTime: Optional[AwareDatetime] = None
    customerReference: str
    purchaseOrderNo: str
    deliverySitePathPrefix: str | None
    timeQuoted: AwareDatetime
    deliverySiteId: str | None
    orderStatus: str
    orderStatusHistory: list[TaraStatusHistory]
    suborders: Optional[list[TaraSubOrderResponse]] = None
    suborderIds: Optional[list[UUID]] = None

class TaraOrdersResponse(BaseModel):
    orderId: UUID
    orderType: str
    customerReference: str
    purchaseOrderNo: str
    deliverySitePathPrefix: str | None
    timeQuoted: AwareDatetime
    deliverySiteId: str | None
    orderStatus: str
    orderStatusHistory: list[TaraStatusHistory]
    suborderIds: Optional[list[str]]



class FeasibilityRequest(BaseModel):
    resolution: float
    maxCloudCover: int
    sensors: list[str]
    isStereo: bool
    taskingPriority: str
    timeWindows: list[TimeWindow]
    areaOfInterest: Polygon

class FeasibilitySyncResponse(BaseModel):
    feasibility_request_id: UUID
    message: str

class FeasibilityAsyncResponse(BaseModel):
    feasibility_request_id: UUID
    taskingWindows: list[TimeWindow]
    status: str

class TaraTaskingParametersRequest(BaseModel):
    taskingScheme: Optional[str] = "single_window"
    taskingPriority: Optional[str] =  "Select"
    maxCloudCover: int
    startDateTime: AwareDatetime
    endDateTime: AwareDatetime
    scanDirection: Optional[str] = "Any"
    singleSensor: Optional[bool] = False
    sensors: list[Literal["WV01", "WV02", "WV03", "GE01", "LG01", "LG02"]]
    isStereo: Optional[bool] = False

class TaraProductionParametersRequest(BaseModel):
    productLevel: str = "OR2A"
    bandCombination: str = "4BB"
    resolution: float = 0.5
    bitDepth: int = 16
    resamplingKernel: Optional[str] = "CC"
    dra: Optional[bool] = False
    acomp: Optional[bool] = False
    projection: Optional[str] = "UTM_WGS84_Meter"
    priority: Optional[str] = "Standard"
    format: Optional[str] = "GeoTIFF"
    tiling: Optional[str] = "16kx16k"
    fullStrip: Optional[bool] = False
    stereo: Optional[bool] = False
    fullOverlap: Optional[bool] = False

class TaraOrderParameters(BaseModel):
    orderType: Literal['taskingOrder','archiveOrder']
    aoiName: Optional[str] = ''
    aoi: Polygon
    feasibilityId: str


class TaraSuborder(BaseModel):
    subreference: str
    provider: str
    parameters: TaraOrderParameters
    productionParameters: TaraProductionParametersRequest
    taskingParameters: Optional[TaraTaskingParametersRequest] = None
    licenseType: Optional[str] = "Internal"
    licenseTerms: Optional[str] = "Perpetual"
    endUseCode: Optional[str] = "AGR"
    endUserIds: List[str]

class TaraParametersRequest(BaseModel):
    orderType: Literal['taskingOrder','archiveOrder']
    aoiName: Optional[str] = ''
    aoi: Polygon
    feasibilityId: str
    productionParameters: TaraProductionParametersRequest   
    licenseType: Optional[str] = "Internal"
    licenseTerms: Optional[str] = "Perpetual"
    endUseCode: Optional[str] = "AFR"
    endUserIds: List[str]


class TaraSuborderRequest(BaseModel):
    subreference: str
    provider: str
    parameters: TaraParametersRequest 

class TaraQuote(BaseModel):
    customerReference: str
    purchaseOrderNo: str
    suborders: List[TaraSuborderRequest]

class TaraQuoteResponse(BaseModel):
    status: int
    message: str
    orderInformation: TaraOrderResponse

class TaraOrderAcceptRequest(BaseModel):
    orderId: UUID

class TaraOrderAcceptResponse(BaseModel):
    message: str
    orderInformation: TaraOrderResponse

class MaxarConstraints(Constraints):
    offNadirAngle: int
    sensor: str

class MaxarOpportunityProperties(OpportunityProperties):
    sensors: List[Literal["WV01", "WV02", "WV03", "GE01", "LG01", "LG02"]]
    maxCloudCover: int = Field(ge=5, le=100) 
    isStereo: bool = False
    minOffNadirAngle: int = Field(ge=0, le=45)
    maxOffNadirAngle: int = Field(ge=0, le=45)
    

class MaxarOrderParameters(OrderParameters):
    customerReference: str = Field(
        title="Customer Reference",
        description= "Free text parameter containing the client reference to the tasking order",
        default=""
    )
    opportunityRequestId: str = Field(
        title="Opportunity Request Id",
        description="ID returned from an opportunity request. Must be included to place order.",
        default=""
    )
    endUserIds: str = Field(
        title="EUSI Enduser ID",
        description="Parameter containing a list of EUSI assigned UUID for the end users"
    )
    endUseCode: str = Field(
        title="EUSI Enduse Code",
        description="Parameter containing the end use code describing usage of the imagery"
    )
    productLevel: str = Field(
        title="Product Level",
        description="Property containing the production level to apply to delivered product",
        default="OR2A",
        enum=["OR2A","ORTHO","2A"]
    )

    bandCombination: str = Field(
        title="Band combination",
        description="Property containing the band combination to apply to delivered produc",
        default="PAN",
        enum=["PAN","4BB","4PS","8BB"]
    )

    resolution: str = Field(
        title="Bit depth",
        description="Property containing the bit depth to apply to delivered product",
        default="0.50",
        enum=["0.50","0.40","0.30"]
    )

    stereo: bool = Field(
        title="Stereo",
        description="Property describing whether to collect this subOrder as in-track stereo",
        default=False
    )

    vehicle: list[str]= Field(
        title="Selected Vehicles",
        description="Array containing the values of the allowed vehicles for imagery collection",
        default=MAXAR_SATELLITES,
        enum=MAXAR_SATELLITES
    )
    #endUseCode: str = list[Literal["AGR", "DNI", "EDU", "ERM", "FOR", "HUM", "LBS", "MAR", "MIN", "NAT", "DEM", "RED", "RUR", "SIM", "TEL", "URB", "UTL", "SHL"]]

