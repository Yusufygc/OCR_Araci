from typing import Dict, List
from src.core.strategies.scan_strategy_interface import IScanStrategy
from src.core.strategies.line_scan_strategy import LineScanStrategy
from src.core.strategies.block_scan_strategy import BlockScanStrategy
from src.core.strategies.multi_region_strategy import MultiRegionStrategy


class ScanStrategyFactory:
    """
    Pluggable Factory for OCR Scanning Strategies.
    Provides decoupled registry to register and retrieve scanning modes without tight coupling.
    """

    _registry: Dict[str, IScanStrategy] = {}

    @classmethod
    def _initialize_defaults(cls):
        """Populates default core scanning strategies."""
        if not cls._registry:
            cls.register_strategy(LineScanStrategy())
            cls.register_strategy(BlockScanStrategy())
            cls.register_strategy(MultiRegionStrategy())

    @classmethod
    def register_strategy(cls, strategy: IScanStrategy):
        """Registers a new scanning strategy dynamically (Pluggable / Tak-Çıkar)."""
        cls._registry[strategy.mode_id] = strategy

    @classmethod
    def get_strategy(cls, mode_id: str) -> IScanStrategy:
        """Retrieves strategy instance by mode_id, falling back to LineScanStrategy."""
        cls._initialize_defaults()
        if mode_id not in cls._registry:
            return cls._registry["line"]
        return cls._registry[mode_id]

    @classmethod
    def list_strategies(cls) -> List[Dict[str, str]]:
        """Returns metadata list of available scanning modes for UI selectors."""
        cls._initialize_defaults()
        return [
            {"id": s.mode_id, "name": s.display_name}
            for s in cls._registry.values()
        ]
