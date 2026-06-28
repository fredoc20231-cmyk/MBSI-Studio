"""Benchmark method adapters."""

from mbsi.benchmarks.adapters.base import BaseBenchmarkAdapter, AdapterResult
from mbsi.benchmarks.adapters.mbsi import MBSIAdapter
from mbsi.benchmarks.adapters.tangram import TangramAdapter
from mbsi.benchmarks.adapters.cell2location import Cell2locationAdapter
from mbsi.benchmarks.adapters.graphst import GraphSTAdapter
from mbsi.benchmarks.adapters.stagate import STAGATEAdapter
from mbsi.benchmarks.adapters.bayespace import BayesSpaceAdapter
from mbsi.benchmarks.adapters.spahdmap import SpaHDmapAdapter

DEFAULT_ADAPTERS = {
    "mbsi": MBSIAdapter,
    "tangram": TangramAdapter,
    "cell2location": Cell2locationAdapter,
    "graphst": GraphSTAdapter,
    "stagate": STAGATEAdapter,
    "bayespace": BayesSpaceAdapter,
    "spahdmap": SpaHDmapAdapter,
}


def get_adapter(name: str) -> BaseBenchmarkAdapter:
    key = name.lower().replace("-", "").replace("_", "")
    mapping = {k.replace("_", ""): v for k, v in DEFAULT_ADAPTERS.items()}
    if key not in mapping:
        raise ValueError(f"Unknown adapter: {name}")
    return mapping[key]()


def list_adapters() -> list:
    return list(DEFAULT_ADAPTERS.keys())
