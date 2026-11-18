"""API-ready image cohort viewer payload, designed for Lovable/React.

The client supplies observed feature matrices or its own coordinates. No
patient image content is stored by this endpoint. Do not expose to the public
without authentication, authorization, quotas and deployment security controls.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from mbsi.visualization.mistic_imaging import image_cohort_embedding, image_cohort_layout


class ImagingLayoutRequest(BaseModel):
    image_ids: list[str] = Field(min_length=1, max_length=10000)
    coordinates: list[list[float]]
    metadata: dict[str, dict] = Field(default_factory=dict)


class ImagingEmbeddingRequest(BaseModel):
    image_ids: list[str] = Field(min_length=3, max_length=500)
    features: list[list[float]]
    metadata: dict[str, dict] = Field(default_factory=dict)
    method: str = "pca"
    perplexity: float = Field(default=30.0, gt=0.0, lt=500.0)
    random_state: int = 42


router = APIRouter(prefix="/api/v1/imaging", tags=["imaging"])


@router.post("/layout")
def imaging_layout(body: ImagingLayoutRequest):
    try:
        result = image_cohort_layout(body.image_ids, body.coordinates,
                                     metadata=body.metadata)
        return {"status": "complete", "source": result.source,
                "coordinates": result.records()}
    except (ValueError, TypeError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/embedding")
def imaging_embedding(body: ImagingEmbeddingRequest):
    try:
        result = image_cohort_embedding(
            body.image_ids, body.features,
            metadata=body.metadata, method=body.method,
            random_state=body.random_state, perplexity=body.perplexity,
        )
        return {"status": "complete", "source": result.source,
                "coordinates": result.records()}
    except (ValueError, TypeError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
