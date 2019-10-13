import enum


class LayerType(enum.Enum):
    B_CU = 'b_cu'
    F_CU = 'f_cu'
    EDGE_CUTS = 'edge_cuts'
    DRILL = 'drill'


class FlatcamLayer(enum.Enum):
    B_CU = 'b_cu'
    B_CU_PATH = 'b_cu_path'
    B_CU_CNC = 'b_cu_cnc'
    F_CU = 'f_cu'
    F_CU_PATH = 'f_cu_path'
    F_CU_CNC = 'f_cu_cnc'
    ALIGNMENT = 'edge_cuts_aligndrill'
    ALIGNMENT_PATH = 'edge_cuts_aligndrill_path'
    ALIGNMENT_CNC = 'edge_cuts_aligndrill_cnc'
    EDGE_CUTS = 'edge_cuts'
    EDGE_CUTS_PATH = 'edge_cuts_cutout'
    EDGE_CUTS_CNC = 'edge_cuts_cnc'
    DRILL = 'drill'
