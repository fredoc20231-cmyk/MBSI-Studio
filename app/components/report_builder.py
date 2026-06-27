"""
Report building components for generating HTML reports and summaries.
"""

import streamlit as st
from typing import Dict, Any, List
from datetime import datetime
import json


def generate_methods_text(params: Dict[str, Any]) -> str:
    """
    Generate manuscript-ready methods text.
    
    Parameters
    ----------
    params : dict
        MBSI parameters
        
    Returns
    -------
    text : str
        Methods text
    """
    text = f"""
    **MBSI Reconstruction**
    
    Spatial transcriptomics super-resolution was performed using Morpho-Biophysical Sheaf Integration (MBSI). 
    The reconstruction was configured with {params.get('n_cells_per_spot', 5)} pseudo-cells per spot, 
    diffusion kernel scale γ={params.get('gamma', 1.0)}, and optimal transport regularization ε={params.get('epsilon', 0.05)}.
    """
    
    if params.get('use_sheaf', True):
        text += f" Sheaf regularization was applied with λ={params.get('lambda_sheaf', 0.1)}."
    
    if params.get('use_anisotropic', True):
        text += " Anisotropic diffusion modeling was used to incorporate tissue morphology."
    
    text += f" The optimization converged after {params.get('max_iter', 300)} iterations."
    
    return text


def generate_summary_text(adata, metrics: Dict[str, Any]) -> str:
    """
    Generate automated interpretation summary.
    
    Parameters
    ----------
    adata : AnnData
        Reconstructed AnnData
    metrics : dict
        Validation metrics
        
    Returns
    -------
    text : str
        Summary text
    """
    n_cells = adata.n_obs if adata else 0
    n_genes = adata.n_vars if adata else 0
    
    text = f"**Computational Interpretation**\n\n"
    text += f"MBSI reconstructed {n_cells} cells from spot-level data, retaining {n_genes} genes. "
    
    if 'pearson_correlation' in metrics:
        corr = metrics['pearson_correlation']
        text += f"The reconstruction achieved a Pearson correlation of {corr:.3f} "
        
        if corr > 0.8:
            text += "indicating high fidelity to the original expression patterns. "
        elif corr > 0.6:
            text += "indicating moderate fidelity to the original expression patterns. "
        else:
            text += "indicating lower fidelity to the original expression patterns. "
    
    if 'boundary_leakage' in metrics:
        leakage = metrics['boundary_leakage']
        text += f"Boundary leakage score was {leakage:.3f}. "
        
        if leakage < 0.3:
            text += "The reconstruction preserved compartment-specific expression with minimal leakage. "
        else:
            text += "Some compartment leakage was observed in the reconstruction. "
    
    text += "\n\n*Note: This is a computational interpretation based on the provided metrics. "
    text += "Biological validation should be performed with expert domain knowledge.*"
    
    return text


def generate_parameter_json(params: Dict[str, Any]) -> str:
    """
    Generate formatted parameter JSON.
    
    Parameters
    ----------
    params : dict
        Parameters
        
    Returns
    -------
    json_str : str
        Formatted JSON string
    """
    return json.dumps(params, indent=2)


def generate_reproducibility_log(
    job_id: str,
    params: Dict[str, Any],
    data_info: Dict[str, Any],
    results: Dict[str, Any]
) -> str:
    """
    Generate reproducibility log.
    
    Parameters
    ----------
    job_id : str
        Job identifier
    params : dict
        Parameters used
    data_info : dict
        Data information
    results : dict
        Results summary
        
    Returns
    -------
    log : str
        Reproducibility log
    """
    log = {
        'job_id': job_id,
        'timestamp': datetime.now().isoformat(),
        'mbsi_version': '0.1.0',
        'parameters': params,
        'data_info': data_info,
        'results': results
    }
    
    return json.dumps(log, indent=2)


def export_report_section(title: str, content: str, downloadable: bool = True):
    """
    Display a report section with optional download.
    
    Parameters
    ----------
    title : str
        Section title
    content : str
        Section content
    downloadable : bool
        Whether to offer download
    """
    with st.expander(title, expanded=False):
        st.markdown(content)
        
        if downloadable:
            st.download_button(
                f"Download {title}",
                content,
                file_name=f"{title.lower().replace(' ', '_')}.txt",
                mime="text/plain"
            )


def full_report_builder(
    adata,
    metrics: Dict[str, Any],
    params: Dict[str, Any]
):
    """
    Build full report with all sections.
    
    Parameters
    ----------
    adata : AnnData
        Reconstructed AnnData
    metrics : dict
        Validation metrics
    params : dict
        MBSI parameters
    """
    st.header("Report Builder")
    
    # Methods section
    methods_text = generate_methods_text(params)
    export_report_section("Methods Text", methods_text)
    
    # Summary section
    summary_text = generate_summary_text(adata, metrics)
    export_report_section("Interpretation Summary", summary_text)
    
    # Parameters section
    param_json = generate_parameter_json(params)
    export_report_section("Parameters (JSON)", param_json)
    
    # Metrics section
    metrics_json = json.dumps(metrics, indent=2, default=str)
    export_report_section("Metrics (JSON)", metrics_json)
    
    # One-click export buttons
    st.markdown("---")
    st.subheader("One-Click Exports")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Export Full Report"):
            full_report = f"""
            # MBSI Reconstruction Report
            
            ## Methods
            {methods_text}
            
            ## Interpretation
            {summary_text}
            
            ## Parameters
            ```json
            {param_json}
            ```
            
            ## Metrics
            ```json
            {metrics_json}
            ```
            """
            st.download_button(
                "Download Full Report",
                full_report,
                file_name="mbsi_report.md",
                mime="text/markdown"
            )
    
    with col2:
        if st.button("Export Parameters Only"):
            st.download_button(
                "Download Parameters",
                param_json,
                file_name="mbsi_parameters.json",
                mime="application/json"
            )
    
    with col3:
        if st.button("Export Metrics Only"):
            st.download_button(
                "Download Metrics",
                metrics_json,
                file_name="mbsi_metrics.json",
                mime="application/json"
            )
