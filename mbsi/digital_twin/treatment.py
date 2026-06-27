"""Treatment definitions for digital twin."""

TREATMENTS = {
    "untreated": {"immune_boost": 0.0, "tumor_kill": 0.0, "resistance_change": 0.0},
    "cisplatin": {"immune_boost": -0.05, "tumor_kill": 0.15, "resistance_change": 0.05},
    "PARP inhibitor": {"immune_boost": 0.0, "tumor_kill": 0.10, "resistance_change": 0.08},
    "PD-1 blockade": {"immune_boost": 0.20, "tumor_kill": 0.05, "resistance_change": -0.02},
    "CAR-T placeholder": {"immune_boost": 0.25, "tumor_kill": 0.12, "resistance_change": 0.03},
}
