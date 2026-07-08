from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class Role(Enum):
    AP = "AP"
    PASSIVE = "PASSIVE"
    STA = "STA"


@dataclass
class CsiLine:
    type: str = "CSI_DATA"
    role: Optional[Role] = None
    mac: Optional[str] = None
    rssi: Optional[int] = None
    rate: Optional[int] = None
    sig_mode: Optional[int] = None
    mcs: Optional[int] = None
    bandwidth: Optional[int] = None
    smoothing: Optional[bool] = None
    not_sounding: Optional[bool] = None
    aggregation: Optional[bool] = None
    stbc: Optional[bool] = None
    fec_coding: Optional[bool] = None
    sgi: Optional[bool] = None
    noise_floor: Optional[int] = None
    ampdu_cnt: Optional[int] = None
    channel: Optional[int] = None
    secondary_channel: Optional[int] = None
    local_timestamp: Optional[int] = None
    ant: Optional[int] = None
    sig_len: Optional[int] = None
    rx_state: Optional[int] = None
    real_time_set: Optional[bool] = None
    real_timestamp: Optional[float] = None
    len: Optional[int] = None
    csi_data: List[int] = field(default_factory=list)
