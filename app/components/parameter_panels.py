"""
Parameter panel components for configuring MBSI runs.
"""

import streamlit as st
from typing import Dict, Any


def mbsi_parameter_panel() -> Dict[str, Any]:
    """
    MBSI reconstruction parameter panel.
    
    Returns
    -------
    params : dict
        Dictionary of parameters
    """
    st.subheader("MBSI Parameters")
    
    with st.expander("Basic Parameters", expanded=True):
        n_cells_per_spot = st.slider(
            "Cells per spot",
            min_value=1,
            max_value=20,
            value=5,
            help="Number of pseudo-cells to generate per spot"
        )
        
        gamma = st.slider(
            "Gamma (kernel scale)",
            min_value=0.1,
            max_value=10.0,
            value=1.0,
            step=0.1,
            help="Diffusion kernel scale parameter"
        )
        
        epsilon = st.slider(
            "Epsilon (OT regularization)",
            min_value=0.01,
            max_value=1.0,
            value=0.05,
            step=0.01,
            help="Optimal transport entropy regularization"
        )
    
    with st.expander("Advanced Parameters"):
        lambda_sheaf = st.slider(
            "Lambda sheaf",
            min_value=0.0,
            max_value=10.0,
            value=0.1,
            step=0.1,
            help="Sheaf regularization strength"
        )
        
        rho1 = st.slider(
            "Rho1 (unbalanced OT)",
            min_value=0.1,
            max_value=100.0,
            value=1.0,
            step=0.1,
            help="Unbalanced OT penalty parameter"
        )
        
        rho2 = st.slider(
            "Rho2 (unbalanced OT)",
            min_value=0.1,
            max_value=100.0,
            value=1.0,
            step=0.1,
            help="Unbalanced OT penalty parameter"
        )
        
        k_graph = st.slider(
            "K neighbors (graph)",
            min_value=3,
            max_value=20,
            value=8,
            help="Number of neighbors for cell graph"
        )
        
        max_iter = st.slider(
            "Max iterations",
            min_value=10,
            max_value=1000,
            value=300,
            help="Maximum optimization iterations"
        )
    
    with st.expander("Model Options"):
        use_sheaf = st.checkbox("Use sheaf regularization", value=True)
        use_anisotropic = st.checkbox("Use anisotropic diffusion", value=True)
        use_gpu = st.checkbox("Use GPU (if available)", value=False)
    
    with st.expander("Reproducibility"):
        random_seed = st.number_input(
            "Random seed",
            min_value=0,
            max_value=9999,
            value=42,
            help="Random seed for reproducibility"
        )
    
    return {
        'n_cells_per_spot': n_cells_per_spot,
        'gamma': gamma,
        'epsilon': epsilon,
        'lambda_sheaf': lambda_sheaf,
        'rho1': rho1,
        'rho2': rho2,
        'k_graph': k_graph,
        'max_iter': max_iter,
        'use_sheaf': use_sheaf,
        'use_anisotropic': use_anisotropic,
        'use_gpu': use_gpu,
        'random_seed': random_seed
    }


def preprocessing_parameter_panel() -> Dict[str, Any]:
    """
    Preprocessing parameter panel.
    
    Returns
    -------
    params : dict
        Dictionary of preprocessing parameters
    """
    st.subheader("Preprocessing Parameters")
    
    with st.expander("Gene Filtering"):
        min_genes = st.slider(
            "Min genes per spot",
            min_value=0,
            max_value=1000,
            value=200,
            help="Minimum number of genes per spot"
        )
        
        min_spots = st.slider(
            "Min spots per gene",
            min_value=0,
            max_value=100,
            value=3,
            help="Minimum number of spots per gene"
        )
        
        max_genes = st.slider(
            "Max genes to keep",
            min_value=100,
            max_value=20000,
            value=2000,
            help="Maximum number of highly variable genes"
        )
    
    with st.expander("Normalization"):
        log_normalize = st.checkbox("Log normalize", value=True)
        scale = st.checkbox("Scale to unit variance", value=True)
        
        filter_mt = st.checkbox("Filter mitochondrial genes", value=False)
        filter_rb = st.checkbox("Filter ribosomal genes", value=False)
    
    with st.expander("Image Processing"):
        downsample_factor = st.slider(
            "Downsample factor",
            min_value=1,
            max_value=10,
            value=1,
            help="Image downsampling factor"
        )
        
        smoothing_sigma = st.slider(
            "Smoothing sigma",
            min_value=0.0,
            max_value=5.0,
            value=1.0,
            step=0.1,
            help="Gaussian smoothing sigma"
        )
    
    return {
        'min_genes': min_genes,
        'min_spots': min_spots,
        'max_genes': max_genes,
        'log_normalize': log_normalize,
        'scale': scale,
        'filter_mt': filter_mt,
        'filter_rb': filter_rb,
        'downsample_factor': downsample_factor,
        'smoothing_sigma': smoothing_sigma
    }


def morphology_parameter_panel() -> Dict[str, Any]:
    """
    Morphology analysis parameter panel.
    
    Returns
    -------
    params : dict
        Dictionary of morphology parameters
    """
    st.subheader("Morphology Parameters")
    
    with st.expander("Anisotropy"):
        anisotropy_strength = st.slider(
            "Anisotropy strength",
            min_value=0.0,
            max_value=2.0,
            value=1.0,
            step=0.1,
            help="Strength of anisotropic diffusion"
        )
        
        smoothing_radius = st.slider(
            "Smoothing radius",
            min_value=1,
            max_value=20,
            value=5,
            help="Radius for smoothing operations"
        )
    
    with st.expander("Boundary Detection"):
        boundary_threshold = st.slider(
            "Boundary threshold",
            min_value=0.0,
            max_value=1.0,
            value=0.5,
            step=0.05,
            help="Threshold for boundary detection"
        )
        
        use_image_morphology = st.checkbox(
            "Use image-based morphology",
            value=True,
            help="Use image features for morphology"
        )
        
        use_coordinate_fallback = st.checkbox(
            "Use coordinate-only fallback",
            value=False,
            help="Fallback to coordinate-based if image unavailable"
        )
    
    with st.expander("Feature Extraction"):
        compute_gradient = st.checkbox("Compute gradient", value=True)
        compute_texture = st.checkbox("Compute texture", value=True)
        compute_density = st.checkbox("Compute density", value=True)
    
    return {
        'anisotropy_strength': anisotropy_strength,
        'smoothing_radius': smoothing_radius,
        'boundary_threshold': boundary_threshold,
        'use_image_morphology': use_image_morphology,
        'use_coordinate_fallback': use_coordinate_fallback,
        'compute_gradient': compute_gradient,
        'compute_texture': compute_texture,
        'compute_density': compute_density
    }


def run_mode_selector() -> str:
    """
    Select run mode (Fast Preview, Standard, Publication-Quality).
    
    Returns
    -------
    mode : str
        Selected run mode
    """
    st.subheader("Run Mode")
    
    mode = st.radio(
        "Select run mode",
        ["Fast Preview", "Standard Reconstruction", "Publication-Quality Run"],
        help="Fast Preview: quick results with default parameters\nStandard: balanced speed and quality\nPublication-Quality: maximum accuracy"
    )
    
    # Set parameters based on mode
    if mode == "Fast Preview":
        st.info("Fast Preview: 50 iterations, isotropic kernel")
    elif mode == "Standard Reconstruction":
        st.info("Standard: 300 iterations, anisotropic kernel")
    elif mode == "Publication-Quality Run":
        st.info("Publication-Quality: 1000 iterations, full sheaf regularization")
    
    return mode


def benchmark_parameter_panel() -> Dict[str, Any]:
    """
    Benchmark parameter panel.
    
    Returns
    -------
    params : dict
        Dictionary of benchmark parameters
    """
    st.subheader("Benchmark Parameters")
    
    with st.expander("Methods to Compare"):
        compare_mbsi = st.checkbox("MBSI Full Model", value=True)
        compare_euclidean = st.checkbox("Euclidean Baseline", value=True)
        compare_isotropic = st.checkbox("Isotropic Diffusion", value=True)
        compare_no_sheaf = st.checkbox("No Sheaf Regularization", value=True)
        compare_balanced_ot = st.checkbox("Balanced OT", value=True)
        compare_graph_laplacian = st.checkbox("Graph Laplacian Baseline", value=False)
    
    with st.expander("External Methods (Placeholder)"):
        compare_tangram = st.checkbox("Tangram", value=False)
        compare_cell2location = st.checkbox("cell2location", value=False)
        compare_bayesspace = st.checkbox("BayesSpace", value=False)
        compare_stagate = st.checkbox("STAGATE", value=False)
    
    with st.expander("Benchmark Settings"):
        n_iterations = st.slider(
            "Benchmark iterations",
            min_value=1,
            max_value=10,
            value=3,
            help="Number of iterations for stability"
        )
        
        use_gpu = st.checkbox("Use GPU for benchmarks", value=False)
    
    return {
        'compare_mbsi': compare_mbsi,
        'compare_euclidean': compare_euclidean,
        'compare_isotropic': compare_isotropic,
        'compare_no_sheaf': compare_no_sheaf,
        'compare_balanced_ot': compare_balanced_ot,
        'compare_graph_laplacian': compare_graph_laplacian,
        'compare_tangram': compare_tangram,
        'compare_cell2location': compare_cell2location,
        'compare_bayesspace': compare_bayesspace,
        'compare_stagate': compare_stagate,
        'n_iterations': n_iterations,
        'use_gpu': use_gpu
    }
