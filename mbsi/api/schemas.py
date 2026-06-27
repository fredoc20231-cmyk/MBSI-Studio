"""
Pydantic schemas for API request/response validation.
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str


class UploadResponse(BaseModel):
    """File upload response."""
    job_id: str
    filename: str
    file_type: str
    n_spots: Optional[int] = None
    n_genes: Optional[int] = None


class MBSIRequest(BaseModel):
    """MBSI reconstruction request."""
    job_id: str
    n_cells_per_spot: int = Field(default=5, ge=1, le=20)
    gamma: float = Field(default=1.0, ge=0.1, le=10.0)
    epsilon: float = Field(default=0.05, ge=0.01, le=1.0)
    lambda_sheaf: float = Field(default=0.1, ge=0.0, le=10.0)
    rho1: float = Field(default=1.0, ge=0.1, le=100.0)
    rho2: float = Field(default=1.0, ge=0.1, le=100.0)
    max_iter: int = Field(default=300, ge=10, le=1000)
    use_sheaf: bool = True
    use_anisotropic: bool = True
    k_graph: int = Field(default=8, ge=3, le=20)
    random_state: Optional[int] = None


class MBSIResponse(BaseModel):
    """MBSI reconstruction response."""
    job_id: str
    status: str
    n_cells: int
    n_genes: int
    parameters: Dict[str, Any]
    convergence: Dict[str, Any]


class ValidationRequest(BaseModel):
    """Validation request."""
    job_id: str
    true_adata_path: Optional[str] = None


class ValidationResponse(BaseModel):
    """Validation response."""
    job_id: str
    metrics: Dict[str, Any]


class BenchmarkRequest(BaseModel):
    """Benchmark request."""
    job_id: str
    run_ablation: bool = False


class BenchmarkResponse(BaseModel):
    """Benchmark response."""
    job_id: str
    metrics: Dict[str, Any]
    ablation_results: Optional[Dict[str, Any]] = None


class ErrorResponse(BaseModel):
    """Error response."""
    error: str
    detail: Optional[str] = None


class JobRequest(BaseModel):
    job_id: str


class SegmentResponse(BaseModel):
    job_id: str
    n_compartments: int
    status: str


class CopilotRequest(BaseModel):
    query: str
    analysis_state: Dict[str, Any] = Field(default_factory=dict)


class CopilotResponse(BaseModel):
    query: str
    answer: str


class TreatmentRequest(BaseModel):
    job_id: str
    treatment: str = "PD-1 blockade"


class CausalInterveneRequest(BaseModel):
    job_id: str
    target: str = "compartment"
    value: float = 0.0
