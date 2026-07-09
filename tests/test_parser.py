import pytest
from flask_serial.parser import parse_line
from flask_serial.models import Role

# Helper to build a 26-field CSI line matching firmware output format
# 25 comma-separated metadata fields + 1 bracketed CSI data field
def _make_csi_line(
    role="AP",
    mac="AA:BB:CC:DD:EE:FF",
    rssi="-65",
    rate="1",
    sig_mode="0",
    mcs="1",
    bandwidth="1",
    smoothing="0",
    not_sounding="0",
    aggregation="0",
    stbc="0",
    fec_coding="0",
    sgi="0",
    noise_floor="-90",
    ampdu_cnt="0",
    channel="6",
    secondary_channel="0",
    local_timestamp="12345678",
    ant="0",
    sig_len="100",
    rx_state="0",
    real_time_set="1",
    real_timestamp="1712345678.500",
    data_len="128",
    csi_data="[]",
):
    fields = [
        "CSI_DATA",
        role, mac, rssi, rate, sig_mode, mcs, bandwidth,
        smoothing, not_sounding, aggregation, stbc, fec_coding,
        sgi, noise_floor, ampdu_cnt, channel, secondary_channel,
        local_timestamp, ant, sig_len, rx_state, real_time_set,
        real_timestamp, data_len,
    ]
    return ",".join(fields) + "," + csi_data


def test_parse_valid_line():
    raw = _make_csi_line(csi_data="[12 -5 34 -8 0 127 -64 33]")
    line = parse_line(raw)
    assert line.type == "CSI_DATA"
    assert line.role == Role.AP
    assert line.mac == "AA:BB:CC:DD:EE:FF"
    assert line.rssi == -65
    assert line.rate == 1
    assert line.sig_mode == 0
    assert line.mcs == 1
    assert line.bandwidth == 1
    assert line.smoothing is False
    assert line.not_sounding is False
    assert line.aggregation is False
    assert line.stbc is False
    assert line.fec_coding is False
    assert line.sgi is False
    assert line.noise_floor == -90
    assert line.ampdu_cnt == 0
    assert line.channel == 6
    assert line.secondary_channel == 0
    assert line.local_timestamp == 12345678
    assert line.ant == 0
    assert line.sig_len == 100
    assert line.rx_state == 0
    assert line.real_time_set is True
    assert line.real_timestamp == 1712345678.500
    assert line.len == 128
    assert line.csi_data == [12, -5, 34, -8, 0, 127, -64, 33]


def test_parse_empty_csi():
    raw = _make_csi_line(csi_data="[]")
    line = parse_line(raw)
    assert line.csi_data == []


def test_parse_invalid_prefix():
    raw = "BAD_DATA,AP," + ",".join(["0"] * 24)
    with pytest.raises(ValueError, match="Invalid prefix"):
        parse_line(raw)


def test_parse_too_few_fields():
    with pytest.raises(ValueError, match=">=26 fields"):
        parse_line("CSI_DATA,AP")


def test_parse_missing_brackets():
    raw = _make_csi_line(csi_data="12 -5 34")
    with pytest.raises(ValueError, match="bracket-delimited"):
        parse_line(raw)


def test_parse_role_sta():
    raw = _make_csi_line(role="STA", csi_data="[12 -5 34]")
    line = parse_line(raw)
    assert line.role == Role.STA


def test_parse_role_passive():
    raw = _make_csi_line(role="PASSIVE", csi_data="[12 -5 34]")
    line = parse_line(raw)
    assert line.role == Role.PASSIVE


def test_parse_csi_single_value():
    raw = _make_csi_line(csi_data="[42]")
    line = parse_line(raw)
    assert line.csi_data == [42]


def test_parse_csi_negative_values():
    raw = _make_csi_line(csi_data="[-128 -64 0 64 127]")
    line = parse_line(raw)
    assert line.csi_data == [-128, -64, 0, 64, 127]


def test_parse_csi_whitespace():
    raw = _make_csi_line(csi_data="[  12  -5  34  ]")
    line = parse_line(raw)
    assert line.csi_data == [12, -5, 34]
