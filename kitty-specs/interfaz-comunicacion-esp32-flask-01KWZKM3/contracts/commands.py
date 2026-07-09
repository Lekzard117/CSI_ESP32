from flask_serial.reader import SerialReader


def send_settime(reader: SerialReader, unix_seconds: int):
    cmd = f"SETTIME:{unix_seconds}\n"
    reader._ser.write(cmd.encode("utf-8"))


def send_reset(reader: SerialReader):
    cmd = "RESET\n"
    reader._ser.write(cmd.encode("utf-8"))
