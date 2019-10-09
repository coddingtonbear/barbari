import enum


class LayerType(enum.Enum):
    B_CU = 'b_cu'
    F_CU = 'f_cu'
    ALIGNMENT = 'alignment'
    EDGE_CUTS = 'edge_cuts'
    DRILL = 'drill'
