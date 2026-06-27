"""
Status tracking and display components.
"""

import streamlit as st
import time
from typing import Dict, Any, Optional
from datetime import datetime


class JobStatus:
    """Track job status across pages."""
    
    def __init__(self):
        if 'job_status' not in st.session_state:
            st.session_state.job_status = {}
    
    def set_status(self, job_id: str, status: str, message: str, progress: float = 0.0):
        """Set job status."""
        if 'job_status' not in st.session_state:
            st.session_state.job_status = {}
        
        st.session_state.job_status[job_id] = {
            'status': status,
            'message': message,
            'progress': progress,
            'timestamp': datetime.now().isoformat()
        }
    
    def get_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job status."""
        if 'job_status' not in st.session_state:
            return None
        return st.session_state.job_status.get(job_id)
    
    def update_progress(self, job_id: str, progress: float, message: str):
        """Update job progress."""
        if job_id in st.session_state.job_status:
            st.session_state.job_status[job_id]['progress'] = progress
            st.session_state.job_status[job_id]['message'] = message


def progress_bar_with_steps(steps: list, current_step: int):
    """
    Display a progress bar with labeled steps.
    
    Parameters
    ----------
    steps : list
        List of step names
    current_step : int
        Current step index
    """
    progress = (current_step + 1) / len(steps)
    st.progress(progress)
    
    # Display steps
    cols = st.columns(len(steps))
    for i, (col, step) in enumerate(zip(cols, steps)):
        if i <= current_step:
            col.markdown(f"✅ {step}")
        else:
            col.markdown(f"⭕ {step}")


def run_status_display(status: Dict[str, Any]):
    """
    Display run status information.
    
    Parameters
    ----------
    status : dict
        Status dictionary
    """
    status_type = status.get('status', 'unknown')
    message = status.get('message', '')
    progress = status.get('progress', 0.0)
    
    # Color coding
    if status_type == 'running':
        color = "blue"
        icon = "🔄"
    elif status_type == 'completed':
        color = "green"
        icon = "✅"
    elif status_type == 'error':
        color = "red"
        icon = "❌"
    elif status_type == 'warning':
        color = "orange"
        icon = "⚠️"
    else:
        color = "gray"
        icon = "ℹ️"
    
    st.markdown(f"""
    <div style="
        background: white;
        padding: 15px;
        border-radius: 8px;
        border-left: 4px solid {color};
        margin: 10px 0;
    ">
        <div style="font-size: 18px;">{icon} {status_type.upper()}</div>
        <div style="margin-top: 5px;">{message}</div>
    </div>
    """, unsafe_allow_html=True)
    
    if progress > 0:
        st.progress(progress)


def recent_runs_display(runs: list):
    """
    Display recent runs.
    
    Parameters
    ----------
    runs : list
        List of run dictionaries
    """
    if not runs:
        st.info("No recent runs")
        return
    
    st.subheader("Recent Runs")
    
    for run in runs[:5]:  # Show last 5
        status = run.get('status', 'unknown')
        timestamp = run.get('timestamp', '')
        job_id = run.get('job_id', '')
        
        status_icon = {
            'completed': '✅',
            'running': '🔄',
            'error': '❌',
            'pending': '⏳'
        }.get(status, 'ℹ️')
        
        st.markdown(f"""
        <div style="
            background: #f8f9fa;
            padding: 10px;
            border-radius: 5px;
            margin: 5px 0;
            display: flex;
            justify-content: space-between;
            align-items: center;
        ">
            <span>{status_icon} {job_id[:8]}</span>
            <span style="color: #666; font-size: 12px;">{timestamp}</span>
        </div>
        """, unsafe_allow_html=True)


def dataset_status_card(adata):
    """
    Display dataset status card.
    
    Parameters
    ----------
    adata : AnnData
        AnnData object
    """
    if adata is None:
        st.warning("No dataset loaded")
        return
    
    n_obs = adata.n_obs
    n_vars = adata.n_vars
    has_spatial = 'spatial' in adata.obsm
    has_image = 'image' in adata.uns or 'tissue_image' in adata.uns
    
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    ">
        <div style="font-size: 18px; font-weight: bold;">📊 Dataset Status</div>
        <div style="margin-top: 15px; display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px;">
            <div>
                <div style="font-size: 12px; opacity: 0.8;">Spots</div>
                <div style="font-size: 20px; font-weight: bold;">{n_obs:,}</div>
            </div>
            <div>
                <div style="font-size: 12px; opacity: 0.8;">Genes</div>
                <div style="font-size: 20px; font-weight: bold;">{n_vars:,}</div>
            </div>
            <div>
                <div style="font-size: 12px; opacity: 0.8;">Spatial Coords</div>
                <div style="font-size: 20px; font-weight: bold;">{'✅' if has_spatial else '❌'}</div>
            </div>
            <div>
                <div style="font-size: 12px; opacity: 0.8;">Image</div>
                <div style="font-size: 20px; font-weight: bold;">{'✅' if has_image else '❌'}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def reconstruction_status_card(reconstructed_adata):
    """
    Display reconstruction status card.
    
    Parameters
    ----------
    reconstructed_adata : AnnData
        Reconstructed AnnData object
    """
    if reconstructed_adata is None:
        st.warning("No reconstruction available")
        return
    
    n_cells = reconstructed_adata.n_obs
    n_genes = reconstructed_adata.n_vars
    
    convergence = reconstructed_adata.uns.get('convergence', {})
    converged = convergence.get('converged', False)
    iterations = convergence.get('iterations', 0)
    objective = convergence.get('objective', 0)
    
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        color: white;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    ">
        <div style="font-size: 18px; font-weight: bold;">🔬 Reconstruction Status</div>
        <div style="margin-top: 15px; display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px;">
            <div>
                <div style="font-size: 12px; opacity: 0.8;">Cells</div>
                <div style="font-size: 20px; font-weight: bold;">{n_cells:,}</div>
            </div>
            <div>
                <div style="font-size: 12px; opacity: 0.8;">Genes</div>
                <div style="font-size: 20px; font-weight: bold;">{n_genes:,}</div>
            </div>
            <div>
                <div style="font-size: 12px; opacity: 0.8;">Converged</div>
                <div style="font-size: 20px; font-weight: bold;">{'✅' if converged else '❌'}</div>
            </div>
            <div>
                <div style="font-size: 12px; opacity: 0.8;">Iterations</div>
                <div style="font-size: 20px; font-weight: bold;">{iterations}</div>
            </div>
        </div>
        <div style="margin-top: 10px; font-size: 12px; opacity: 0.8;">
            Final Objective: {objective:.4f}
        </div>
    </div>
    """, unsafe_allow_html=True)


def error_display(error: str, suggestion: str = ""):
    """
    Display error with suggestion.
    
    Parameters
    ----------
    error : str
        Error message
    suggestion : str
        Suggested fix
    """
    st.markdown(f"""
    <div style="
        background: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
        padding: 15px;
        border-radius: 8px;
        margin: 10px 0;
    ">
        <div style="font-weight: bold; margin-bottom: 5px;">❌ Error</div>
        <div>{error}</div>
        {f'<div style="margin-top: 10px; font-style: italic;">💡 Suggestion: {suggestion}</div>' if suggestion else ''}
    </div>
    """, unsafe_allow_html=True)


def warning_display(warning: str):
    """
    Display warning message.
    
    Parameters
    ----------
    warning : str
        Warning message
    """
    st.markdown(f"""
    <div style="
        background: #fff3cd;
        border: 1px solid #ffeaa7;
        color: #856404;
        padding: 15px;
        border-radius: 8px;
        margin: 10px 0;
    ">
        <div style="font-weight: bold; margin-bottom: 5px;">⚠️ Warning</div>
        <div>{warning}</div>
    </div>
    """, unsafe_allow_html=True)
