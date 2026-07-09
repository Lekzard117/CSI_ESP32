import pytest
from unittest.mock import MagicMock, patch

from flask_serial.reader import SerialReader, create_readers, RECONNECT_DELAY, TIMEOUT_SECONDS
from flask_serial.models import CsiLine, Role


from serial.serialutil import SerialException

SINGLE_LINE = (
    b"CSI_DATA,AP,AA:BB:CC:DD:EE:FF,-65,1,0,1,1,0,0,0,0,0,0,"
    b"-90,0,6,0,12345678,0,100,0,1,1712345678.500,128,[12 -5 34]\n"
)


@pytest.fixture
def mock_serial():
    with patch("flask_serial.reader.serial.Serial") as mock_cls:
        instance = MagicMock()
        instance.is_open = True
        mock_cls.return_value = instance
        yield instance


class TestSerialReader:
    def test_connect_success(self, mock_serial):
        reader = SerialReader("/dev/ttyUSB0")
        assert reader.connect() is True
        assert reader.is_connected is True

    def test_connect_failure(self, mock_serial):
        with patch("flask_serial.reader.serial.Serial") as mock_cls:
            mock_cls.side_effect = SerialException("port not found")
            reader = SerialReader("/dev/ttyUSB0")
            assert reader.connect() is False
            assert reader.is_connected is False

    def test_disconnect(self, mock_serial):
        reader = SerialReader("/dev/ttyUSB0")
        reader.connect()
        reader.disconnect()
        assert reader.is_connected is False
        mock_serial.close.assert_called_once()

    def test_disconnect_already_closed(self, mock_serial):
        reader = SerialReader("/dev/ttyUSB0")
        reader.disconnect()
        assert reader.is_connected is False

    def test_is_connected_property(self, mock_serial):
        reader = SerialReader("/dev/ttyUSB0")
        assert reader.is_connected is False
        reader.connect()
        assert reader.is_connected is True
        reader.disconnect()
        assert reader.is_connected is False

    def test_lines_requires_connection(self, mock_serial):
        reader = SerialReader("/dev/ttyUSB0")
        with pytest.raises(RuntimeError, match="Not connected"):
            next(reader.lines())

    def test_lines_yields_parsed_lines(self, mock_serial):
        mock_serial.read.side_effect = [SINGLE_LINE, RuntimeError("stop")]
        reader = SerialReader("/dev/ttyUSB0")
        reader.connect()
        gen = reader.lines()
        line = next(gen)
        assert isinstance(line, CsiLine)
        assert line.role == Role.AP
        assert line.mac == "AA:BB:CC:DD:EE:FF"
        assert line.rssi == -65
        assert line.csi_data == [12, -5, 34]
        assert reader.line_count == 1
        assert reader.error_count == 0

    def test_lines_multiple_lines_in_one_read(self, mock_serial):
        two_lines = SINGLE_LINE + SINGLE_LINE
        mock_serial.read.side_effect = [two_lines, RuntimeError("stop")]
        reader = SerialReader("/dev/ttyUSB0")
        reader.connect()
        gen = reader.lines()
        line1 = next(gen)
        line2 = next(gen)
        assert line1.role == Role.AP
        assert line2.role == Role.AP
        assert reader.line_count == 2

    def test_lines_skips_empty_lines(self, mock_serial):
        mock_serial.read.side_effect = [b"\n\n", RuntimeError("stop")]
        reader = SerialReader("/dev/ttyUSB0")
        reader.connect()
        gen = reader.lines()
        with pytest.raises(RuntimeError, match="stop"):
            next(gen)
        assert reader.line_count == 0
        assert reader.error_count == 0

    def test_lines_handles_malformed_lines(self, mock_serial):
        mock_serial.read.side_effect = [b"BAD_DATA\n", RuntimeError("stop")]
        reader = SerialReader("/dev/ttyUSB0")
        reader.connect()
        gen = reader.lines()
        with pytest.raises(RuntimeError, match="stop"):
            next(gen)
        assert reader.error_count == 1
        assert reader.line_count == 0

    def test_lines_partial_line_in_buffer(self, mock_serial):
        partial = b"CSI_DATA,AP,AA:BB:CC:DD:EE:FF,-65,1,0,1,1,0,0,0,0,0,0,"
        complete = b"-90,0,6,0,12345678,0,100,0,1,1712345678.500,128,[12 -5 34]\n"
        mock_serial.read.side_effect = [partial, complete, RuntimeError("stop")]
        reader = SerialReader("/dev/ttyUSB0")
        reader.connect()
        gen = reader.lines()
        line = next(gen)
        assert line.role == Role.AP
        assert line.csi_data == [12, -5, 34]
        assert reader.line_count == 1

    def test_lines_timeout_triggers_reconnect(self, mock_serial):
        mock_serial.read.side_effect = [b"", RuntimeError("break")]
        reader = SerialReader("/dev/ttyUSB0")
        reader.connect()
        reader.last_rx = 0.0
        with patch.object(reader, "reconnect") as mock_reconnect:
            with patch("flask_serial.reader.time.time", return_value=TIMEOUT_SECONDS + 1):
                with patch("flask_serial.reader.time.sleep"):
                    gen = reader.lines()
                    with pytest.raises(RuntimeError, match="break"):
                        next(gen)
                    mock_reconnect.assert_called_once()

    def test_lines_serial_exception_triggers_reconnect(self, mock_serial):
        mock_serial.read.side_effect = [SerialException("port lost"), RuntimeError("break")]
        reader = SerialReader("/dev/ttyUSB0")
        reader.connect()
        with patch.object(reader, "reconnect") as mock_reconnect:
            with patch("flask_serial.reader.time.sleep"):
                gen = reader.lines()
                with pytest.raises(RuntimeError, match="break"):
                    next(gen)
                mock_reconnect.assert_called_once()


class TestCreateReaders:
    def test_default_port(self):
        with patch.dict("os.environ", {}, clear=True):
            readers = create_readers()
            assert len(readers) == 1
            assert readers[0].port == "/dev/ttyUSB0"
            assert readers[0].baud == 921600

    def test_multi_port(self):
        with patch.dict("os.environ", {"SERIAL_PORTS": "/dev/ttyUSB0,/dev/ttyUSB1"}):
            readers = create_readers()
            assert len(readers) == 2
            assert readers[0].port == "/dev/ttyUSB0"
            assert readers[1].port == "/dev/ttyUSB1"

    def test_trailing_comma(self):
        with patch.dict("os.environ", {"SERIAL_PORTS": "/dev/ttyUSB0,"}):
            readers = create_readers()
            assert len(readers) == 1
            assert readers[0].port == "/dev/ttyUSB0"
