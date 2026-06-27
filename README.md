# MBSI Studio

Morpho-Biophysical Sheaf Integration (MBSI) platform for physics-aware super-resolution of spatial transcriptomics data.

## Overview

MBSI Studio implements a reproducible scientific pipeline for reconstructing single-cell resolution expression from spatial transcriptomics spot data (e.g., 10x Visium, Xenium). The platform combines:

- **Anisotropic diffusion modeling** using tissue morphology
- **Unbalanced optimal transport** for expression deconvolution
- **Sheaf-based regularization** respecting tissue compartment boundaries
- **Comprehensive validation** using pseudo-Visium benchmarks

## Installation

### Local Installation

```bash
# Clone repository
git clone <repository-url>
cd mbsi-studio

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e .
```

### Docker Installation

```bash
# Build and start services
docker compose up --build

# Access Streamlit UI at http://localhost:8501
# Access FastAPI at http://localhost:8000
```

## Quick Demo

```bash
# Generate synthetic demo dataset
python scripts/run_demo.py

# Run Streamlit UI
streamlit run app/streamlit_app.py

# Or run benchmark suite
python scripts/run_benchmark.py
```

## Input Formats

MBSI Studio supports multiple input formats:

1. **10x Visium folder**: Contains `filtered_feature_bc_matrix.h5` and spatial coordinates
2. **h5ad file**: AnnData object with spatial coordinates in `adata.obsm['spatial']`
3. **CSV count matrix**: Gene expression matrix with cells/spots as rows
4. **Spatial coordinate CSV**: X,Y coordinates for each cell/spot
5. **H&E image**: Optional tissue image for morphology features
6. **Cell segmentation mask**: Optional segmentation for cell-level validation
7. **Xenium/CosMx single-cell table**: Ground truth for validation

### Required AnnData Structure

```python
adata.X  # Gene expression matrix (spots x genes)
adata.obsm['spatial']  # Spatial coordinates (n x 2)
adata.var_names  # Gene names
adata.obs_names  # Spot/cell identifiers
```

## MBSI Theory Summary

The MBSI reconstruction solves:

```
min_{T, X}  OT_ε,ρ(a, b, T) + λ_sheaf * R_sheaf(X)
```

where:
- `T` is the transport plan from spots to cells
- `X` is the reconstructed cell-level expression
- `OT_ε,ρ` is entropy-regularized unbalanced optimal transport
- `R_sheaf` is sheaf regularization enforcing boundary consistency
- The diffusion kernel uses anisotropic tensors derived from tissue morphology

### Key Components

1. **Diffusion Kernel**: Anisotropic Gaussian kernel using local diffusion tensors
2. **Unbalanced OT**: Sinkhorn algorithm with marginal relaxation parameters
3. **Sheaf Laplacian**: Graph-based regularization respecting tissue compartments
4. **Reconstruction**: Iterative solver combining OT and sheaf constraints

## Validation Workflow

1. **Pseudo-Visium Generation**: Aggregate single-cell data to spot-level
2. **Reconstruction**: Apply MBSI to recover cell-level expression
3. **Benchmarking**: Compare reconstruction against ground truth using:
   - Pearson/Spearman correlation
   - RMSE
   - Marker localization score
   - Boundary leakage score
   - Moran's I preservation
   - Cell-type classification accuracy

## Expected Outputs

### Reconstruction Output
- `reconstructed.h5ad`: AnnData with reconstructed expression
- `spatial_coords.csv`: Cell spatial coordinates
- `parameters.json`: Reconstruction parameters
- `convergence_log.json`: Optimization convergence

### Benchmark Output
- `benchmark_metrics.csv`: Performance metrics
- `ablation_comparison.csv`: Ablation study results
- `figures/`: Spatial plots, scatter plots, radar plots

### Report Output
- `report.html`: Interactive HTML report
- `report.pdf`: Static PDF report

## API Usage

### Python API

```python
from mbsi.reconstruction.solver import run_mbsi
from mbsi.io.loaders import load_h5ad

# Load data
adata = load_h5ad("data/visium.h5ad")

# Run reconstruction
reconstructed = run_mbsi(
    spot_adata=adata,
    n_cells_per_spot=5,
    gamma=1.0,
    epsilon=0.05,
    lambda_sheaf=0.1
)

# Save results
reconstructed.write_h5ad("data/outputs/reconstructed.h5ad")
```

### FastAPI Endpoints

```bash
# Health check
GET /health

# Upload data
POST /upload

# Run MBSI reconstruction
POST /run-mbsi

# Validate reconstruction
POST /validate

# Run benchmarks
POST /benchmark

# Download results
GET /download/{job_id}
```

## Streamlit UI

The web interface provides tabs for:
- **Upload Data**: Upload and preview spatial transcriptomics data
- **Run MBSI**: Configure parameters and run reconstruction
- **Validation**: Compare reconstruction against ground truth
- **Benchmarks**: Run ablation studies and performance metrics
- **Figures**: Generate and export visualization figures
- **Export Report**: Download comprehensive analysis report

## Testing

```bash
# Run all tests
pytest tests/

# Run specific test
pytest tests/test_kernel.py

# Run with coverage
pytest --cov=mbsi tests/
```

## Project Structure

```
mbsi-studio/
├── README.md
├── pyproject.toml
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── data/
│   ├── demo/
│   ├── uploads/
│   └── outputs/
├── mbsi/
│   ├── io/              # Data loading and validation
│   ├── morphology/      # Image features and diffusion tensors
│   ├── diffusion/       # Diffusion kernels and PDE solvers
│   ├── transport/       # Optimal transport algorithms
│   ├── sheaf/           # Graph construction and sheaf Laplacian
│   ├── reconstruction/  # Main reconstruction solver
│   ├── benchmarks/      # Validation and ablation studies
│   ├── visualization/   # Plotting and reporting
│   └── api/             # FastAPI backend
├── app/
│   └── streamlit_app.py # Streamlit UI
├── scripts/
│   ├── run_demo.py
│   ├── run_benchmark.py
│   └── export_figures.py
└── tests/
    └── test_*.py
```

## Dependencies

- Python 3.11+
- scanpy
- anndata
- numpy
- scipy
- pandas
- scikit-learn
- torch (optional GPU)
- POT (optimal transport)
- networkx
- squidpy
- plotly
- matplotlib
- fastapi
- uvicorn
- streamlit

## Citation

If you use MBSI Studio in your research, please cite:

```
[Add citation when published]
```

## License

MIT License

## Contact

For questions and support, please open an issue on GitHub.
