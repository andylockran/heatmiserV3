
from . import constants

# Believe this is known as CCITT (0xFFFF)
# This is the CRC function converted directly from the Heatmiser C code
# provided in their API

class CRC16:
    """This is the CRC hashing mechanism used by the V3 protocol."""

    LookupHigh = [
        0x00,
        0x10,
        0x20,
        0x30,
        0x40,
        0x50,
        0x60,
        0x70,
        0x81,
        0x91,
        0xA1,
        0xB1,
        0xC1,
        0xD1,
        0xE1,
        0xF1,
    ]
    LookupLow = [
        0x00,
        0x21,
        0x42,
        0x63,
        0x84,
        0xA5,
        0xC6,
        0xE7,
        0x08,
        0x29,
        0x4A,
        0x6B,
        0x8C,
        0xAD,
        0xCE,
        0xEF,
    ]

    def __init__(self):
        self.high = constants.BYTEMASK
        self.low = constants.BYTEMASK

    def extract_bits(self, val):
        """Extras the 4 bits, XORS the message data, and does table lookups."""
        # Step one, extract the Most significant 4 bits of the CRC register
        thisval = self.high >> 4
        # XOR in the Message Data into the extracted bits
        thisval = thisval ^ val
        # Shift the CRC Register left 4 bits
        self.high = (self.high << 4) | (self.low >> 4)
        self.high = self.high & constants.BYTEMASK  # force char
        self.low = self.low << 4
        self.low = self.low & constants.BYTEMASK  # force char
        # Do the table lookups and XOR the result into the CRC tables
        self.high = self.high ^ self.LookupHigh[thisval]
        self.high = self.high & constants.BYTEMASK  # force char
        self.low = self.low ^ self.LookupLow[thisval]
        self.low = self.low & constants.BYTEMASK  # force char

    def update(self, val):
        """Updates the CRC value using bitwise operations."""
        self.extract_bits(val >> 4)  # High nibble first
        self.extract_bits(val & 0x0F)  # Low nibble

    def run(self, message):
        """Calculates a CRC"""
        for value in message:
            self.update(value)
        return [self.low, self.high]

