from fastapi import APIRouter, HTTPException

from api.schemas import LookupRequest, LookupResponse
from api.services import analytics

router = APIRouter(prefix="/api", tags=["lookup"])


@router.post("/lookup", response_model=LookupResponse)
def lookup(payload: LookupRequest):
    if not payload.barcode1 and not payload.barcode2:
        raise HTTPException(status_code=400, detail="请提供条码1或条码2")
    try:
        result = analytics.lookup_fault_rates(
            barcode1=payload.barcode1,
            barcode2=payload.barcode2,
        )
        return LookupResponse(**result)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
