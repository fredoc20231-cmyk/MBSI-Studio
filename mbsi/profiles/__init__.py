"""Analysis profiles for platform-specific workflows."""

from mbsi.profiles.stereo_seq import (
    STEREO_SEQ_PROFILE,
    STEREO_SEQ_SCALES,
    get_stereo_seq_profile,
    pipeline_steps_for_scale,
)
from mbsi.profiles.seurat_like import WORKFLOW_PRESETS, get_workflow_preset, list_workflow_presets
from mbsi.profiles.spatial_platforms import SPATIAL_PLATFORM_WORKFLOWS, get_platform_workflow
from mbsi.profiles.multimodal import MULTIMODAL_PRESETS, get_multimodal_preset
from mbsi.profiles.scalability import SCALABILITY_CONFIG, scalability_mode, should_use_sketch

__all__ = [
    "STEREO_SEQ_PROFILE",
    "STEREO_SEQ_SCALES",
    "get_stereo_seq_profile",
    "pipeline_steps_for_scale",
    "WORKFLOW_PRESETS",
    "get_workflow_preset",
    "list_workflow_presets",
    "SPATIAL_PLATFORM_WORKFLOWS",
    "get_platform_workflow",
    "MULTIMODAL_PRESETS",
    "get_multimodal_preset",
    "SCALABILITY_CONFIG",
    "scalability_mode",
    "should_use_sketch",
]
