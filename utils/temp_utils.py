"""Code for temperature collection."""

import collections
import datetime
import logging
import random
import threading
import time

ROAST_STAGES = ["City", "City+", "Full City", "Full City+", "Vienna"]
ROAST_TEMPS = [422, 432, 441, 450, 463]  # °F

ROAST_EVENTS = ["1st Crack Start", "2nd Crack Start"]


class MockThermocouple:
    """Mock thermocouple for local testing."""
    @property
    def temperature(self):
        """Randomly generate a temperature."""
        return 200 + random.random() * 100


def continually_read_temperature(
    data_lock: threading.Lock,
    temp_plot: collections.deque,
    time_plot: collections.deque,
    temp_recorded: collections.deque,
    time_recorded: collections.deque,
    recording: threading.Event,
    force_stop_recording: threading.Event,
    pi: bool = False,
    interval: float = 1.0,
    fahrenheit: bool = True,
) -> None:
    """
    Continually read temperature from thermocouple.
    
    Args:
        data_lock (threading.Lock): The lock to protect shared data.
        temp_plot (collections.deque): Deque for plotting temperature.
        time_plot (collections.deque): Deque for plotting time.
        temp_recorded (collections.deque): Deque for recording temperature.
        time_recorded (collections.deque): Deque for recording time.
        recording (threading.Event): Event to mark if currently recording.
        force_stop_recording (threading.Event): Event to mark if the recording maxlen is reached.
        interval (float): Seconds between readings.
        fahrenheit (bool): Option to convert readings to fahrenheit.
    """
    thermocouple = initialize_thermocouple(pi)

    while True:
        try:
            reading_time = datetime.datetime.now()
            temp = thermocouple.temperature
            if fahrenheit:
                temp = c_to_f(temp)

            with data_lock:
                temp_plot.append(temp)
                time_plot.append(reading_time)

                if recording.is_set():
                    record_data(
                        temp, reading_time, temp_recorded, time_recorded, force_stop_recording
                    )

            time.sleep(interval)

        except Exception as e:
            logging.error(f"Error reading temperature: {e}")
            time.sleep(interval)


def initialize_thermocouple(pi: bool = False):
    """Initialize the thermocouple connection."""
    if not pi:
        return MockThermocouple()

    import adafruit_max31856
    import board
    import digitalio

    spi = board.SPI()
    cs = digitalio.DigitalInOut(board.D5)
    cs.direction = digitalio.Direction.OUTPUT
    return adafruit_max31856.MAX31856(spi, cs)


def record_data(
    temp: float,
    reading_time: datetime.datetime,
    temp_recorded: collections.deque,
    time_recorded: collections.deque,
    force_stop_recording: threading.Event,
) -> None:
    """Record temperature data."""
    temp_recorded.append(temp)
    time_recorded.append(reading_time)

    if temp_recorded.maxlen and len(temp_recorded) >= temp_recorded.maxlen:
        logging.warning("maxlen reached for recording, writing to database.")
        force_stop_recording.set()


def c_to_f(temp: float) -> float:
    """Convert celsius to fahrenheit"""
    return temp * 9/5 + 32


def f_to_c(temp: float) -> float:
    """Convert fahrenheit to celsius"""
    return (temp - 32) * 5/9
