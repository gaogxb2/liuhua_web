import os

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from api.schemas import AnalyzeRequest, AnalyzeResponse, FilterOptionsResponse
from api.services import analytics

router = APIRouter(prefix="/api", tags=["analyze"])


@router.get("/default-folder")
def default_folder():
    return {"folder_path": analytics.get_default_folder()}


@router.post("/analyze", response_model=AnalyzeResponse)
def analyze(payload: AnalyzeRequest):
    folder_path = payload.folder_path or analytics.get_default_folder()
    try:
        result = analytics.analyze_folder(folder_path, extract_zip=payload.extract_zip)
        return AnalyzeResponse(
            total_boards=result["total_boards"],
            folder_path=result["folder_path"],
            filters=FilterOptionsResponse(**result["filters"]),
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/export")
def export_excel():
    try:
        output_path = analytics.export_excel()
        filename = os.path.basename(output_path)
        return FileResponse(
            output_path,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename=filename,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
