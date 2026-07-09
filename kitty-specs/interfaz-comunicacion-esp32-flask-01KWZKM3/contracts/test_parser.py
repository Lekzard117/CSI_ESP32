import pytest
from flask_serial.parser import parse_line
from flask_serial.models import Role


def test_parse_valid_line():
    raw = "CSI_DATA,AP,AA:BB:CC:DD:EE:FF,-65,1,0,1,1,0,0,0,0,-90,0,6,0,12345678,0,100,0,1,1712345678.500,128,[12 -5 34 -8 0 127 -64 33]"
    line = parse_line(raw)
    assert line.type == "CSI_DATA"
    assert line.role == Role.AP
    assert line.mac == "AA:BB:CC:DD:EE:FF"
    assert line.rssi == -65
    assert line.channel == 6
    assert line.real_timestamp == 1712345678.500
    assert line.csi_data == [12, -5, 34, -8, 0, 127, -64, 33]


def test_parse_empty_csi():
    raw = "CSI_DATA,AP,AA:BB:CC:DD:EE:FF,-65,1,0,1,1,0,0,0,0,-90,0,6,0,12345678,0,100,0,1,1712345678.500,128,[]"
    line = parse_line(raw)
    assert line.csi_data == []


def test_parse_invalid_prefix():
    with pytest.raises(ValueError, match="Invalid prefix"):
        parse_line("BAD_DATA,...")


def test_parse_too_few_fields():
    with pytest.raises(ValueError, match=">=26 fields"):
        parse_line("CSI_DATA,AP")


def test_parse_missing_brackets():
    with pytest.raises(ValueError, match="bracket-delimited"):
        parse_line("CSI_DATA,AP,00:11:22:33:44:55,-65,1,0,1,1,0,0,0,0,-90,0,6,0,12345678,0,100,0,1,1712345678.500,128,12 -5 34")
