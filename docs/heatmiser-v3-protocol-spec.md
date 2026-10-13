# Heatmiser V3 Network Protocol Specification (v3.9)

This specification documents the Heatmiser V3 protocol for RS485 and Wi-Fi thermostats, based on the official *Heatmiser V3 System Protocol (Version 3.9)*. It serves as the authoritative technical reference for the `heatmiserV3` Python library, unit test suites, and the browser-based digital twin visualizer.

---

## 1. Physical Layer & Network Architecture

### 1.1 RS485 Serial Communications
* **Topology**: Multi-drop half-duplex 2-wire RS485 bus.
* **Baud Rate**: **4800 baud**.
* **Framing**: **8 Data bits, No parity, 1 Stop bit (8-N-1)**.
* **Master Hardware**: Heatmiser UH1 Wiring Centre, NetMonitor (NM), Master Controller (MC), TouchPad / TFT, or a standard USB-to-RS485 serial dongle.

### 1.2 Node Addressing
* **Master Nodes**: `0x81` to `0xA0` (Decimal 129 to 160).
  * `0x81` (129): Default Master Controller / TFT / Software Client (`RW_MASTER_ADDRESS`)
  * `0x82` (130): TR2 V3
  * `0x83` (131): NetMonitor V3
  * `0x91`–`0xA0` (145–160): UHC Wiring Centres
* **Slave Nodes (Thermostats)**: `0x01` to `0x20` (Decimal 1 to 32).
  * Up to 32 addressable thermostats per physical RS485 network segment.
* **Broadcast Address**: `0xFF` (Decimal 255).
  * Accepted by all thermostats for global commands (e.g. frost protect, away, clock sync).
  * **No reply** is sent by slaves to broadcast messages.

### 1.3 Communication Timing & Bus Recovery
* **Read Timeout**: Master must wait up to **1000 ms** for a reply.
* **Inter-frame Bus Recovery**: Master must pause at least **100 ms** between receiving a reply and transmitting the next command frame.
* **Frame Reset Threshold**: If a thermostat receives an incomplete frame fragment, it requires at least **20 ms** of bus silence to reset its UART state machine.
* **Write Wait & Retries**: Thermostats take up to a few hundred milliseconds to commit EEPROM/DCB writes. Master should wait up to 1000 ms and may retry up to 5 times upon failure.
* **Broadcast Repeats**: Because broadcast frames receive no ACKs, masters must repeat broadcast transmissions at least **5 times** with >= **1000 ms** intervals between frames.

### 1.4 Endianness
* **Multi-byte parameters (temperatures, lengths, CRC)** are transmitted in **Big-Endian** format over the wire (MSB first, LSB second), matching the microcontroller's internal storage.
* *Exception (Holiday Hours)*: When reading, High byte precedes Low byte. When writing via individual address `24`, Low byte precedes High byte.

---

## 2. Frame Structures

Every communication exchange consists of a Master request frame followed by a Slave reply frame.

### 2.1 Master -> Slave Read Command Frame (Length = 10 bytes)
Used by master to read full or partial Device Control Block (DCB) data:

| Byte Index | Field | Description | Value |
| :---: | :--- | :--- | :--- |
| `0` | Destination Address | Target thermostat ID | `0x01`–`0x20` (1–32) |
| `1` | Frame Length | Total request length including CRC | `0x0A` (10 bytes) |
| `2` | Source Address | Master node ID | `0x81`–`0xA0` (129–160) |
| `3` | Function Code | Read function | `0x00` (`FUNC_READ`) |
| `4` | Start Address Low | Start offset in DCB (Low byte) | `0x00`–`0xFF` |
| `5` | Start Address High | Start offset in DCB (High byte) | `0x00` |
| `6` | Read Length Low | Number of bytes to read (Low byte) | `0xFF` (for full DCB) |
| `7` | Read Length High | Number of bytes to read (High byte) | `0xFF` (for full DCB: `0xFFFF`) |
| `8` | CRC16 Low | CRC checksum Low byte | Calculated CRC |
| `9` | CRC16 High | CRC checksum High byte | Calculated CRC |

### 2.2 Master -> Slave Write Command Frame (Length = 10 + n bytes)
Used to write one or more contiguous bytes into the thermostat's DCB:

| Byte Index | Field | Description | Value |
| :---: | :--- | :--- | :--- |
| `0` | Destination Address | Target thermostat ID (or `0xFF` broadcast) | `0x01`–`0x20`, `0xFF` |
| `1` | Frame Length | Total request length including CRC | `10 + n` bytes |
| `2` | Source Address | Master node ID | `0x81`–`0xA0` (129–160) |
| `3` | Function Code | Write function | `0x01` (`FUNC_WRITE`) |
| `4` | Start Address Low | Target parameter unique address (Low byte) | Parameter address |
| `5` | Start Address High | Target parameter unique address (High byte) | Usually `0x00` |
| `6` | Write Length Low | Number of payload bytes $n$ (Low byte) | $n$ |
| `7` | Write Length High | Number of payload bytes $n$ (High byte) | `0x00` |
| `8`..`8+n-1`| Payload Data | Parameter data bytes | $n$ data bytes |
| `8+n` | CRC16 Low | CRC checksum Low byte | Calculated CRC |
| `9+n` | CRC16 High | CRC checksum High byte | Calculated CRC |

### 2.3 Slave -> Master Reply to Read Command (Length = 11 + n bytes)
Returned by the thermostat after a valid read command:

| Byte Index | Field | Description | Value |
| :---: | :--- | :--- | :--- |
| `0` | Destination Address | Master node ID | Echoes Master ID (`0x81`..) |
| `1` | Frame Length Low | Total reply length (Low byte) | $(11 + n) \& 0xFF$ |
| `2` | Frame Length High | Total reply length (High byte) | $(11 + n) >> 8$ |
| `3` | Source Address | Responding thermostat ID | `0x01`–`0x20` |
| `4` | Function Code | Read operation echo | `0x00` |
| `5` | Start Address Low | Start offset of returned data | Echoed from request |
| `6` | Start Address High | Start offset of returned data | Echoed from request |
| `7` | Actual Length Low | Payload bytes returned $n$ (Low byte) | $n \& 0xFF$ |
| `8` | Actual Length High | Payload bytes returned $n$ (High byte) | $n >> 8$ |
| `9`..`9+n-1`| DCB Data | Returned DCB telemetry/registers | $n$ bytes |
| `9+n` | CRC16 Low | CRC checksum Low byte | Calculated CRC |
| `10+n` | CRC16 High | CRC checksum High byte | Calculated CRC |

### 2.4 Slave -> Master Reply to Write Command (Length = 7 bytes)
Acknowledgment returned by the thermostat after successfully parsing a write:

| Byte Index | Field | Description | Value |
| :---: | :--- | :--- | :--- |
| `0` | Destination Address | Master node ID | Echoes Master ID (`0x81`..) |
| `1` | Frame Length Low | Frame length Low byte | `0x07` (always 7 bytes) |
| `2` | Frame Length High | Frame length High byte | `0x00` |
| `3` | Source Address | Responding thermostat ID | `0x01`–`0x20` |
| `4` | Function Code | Write operation echo | `0x01` |
| `5` | CRC16 Low | CRC checksum Low byte | Calculated CRC |
| `6` | CRC16 High | CRC checksum High byte | Calculated CRC |

---

## 3. CRC-16 Checksum Algorithm

The protocol uses a 16-bit CRC algorithm (polynomial `0xA001`, initial state `0xFFFF`). The calculated checksum is appended as two bytes: `[Low Byte, High Byte]`.

### Code Reference in `heatmiserv3`
The Python implementation in this repository is located at [`heatmiserv3/heatmiser.py` (lines 26–96)](../heatmiserv3/heatmiser.py#L26-L96) under the [`CRC16`](../heatmiserv3/heatmiser.py#L26-L96) class.

---

### Reference Implementations Across Languages

#### 1. Python (`heatmiserv3/heatmiser.py`)
```python
# heatmiserv3/heatmiser.py lines 26-96
class CRC16:
    """CRC hashing mechanism used by the V3 protocol."""

    LookupHigh = [
        0x00, 0x10, 0x20, 0x30, 0x40, 0x50, 0x60, 0x70,
        0x81, 0x91, 0xA1, 0xB1, 0xC1, 0xD1, 0xE1, 0xF1,
    ]
    LookupLow = [
        0x00, 0x21, 0x42, 0x63, 0x84, 0xA5, 0xC6, 0xE7,
        0x08, 0x29, 0x4A, 0x6B, 0x8C, 0xAD, 0xCE, 0xEF,
    ]

    def __init__(self):
        self.high = 0xFF
        self.low = 0xFF

    def extract_bits(self, val):
        """Extracts 4 bits, XORs message data, and does table lookups."""
        thisval = (self.high >> 4) ^ val
        self.high = ((self.high << 4) | (self.low >> 4)) & 0xFF
        self.low = (self.low << 4) & 0xFF
        self.high = (self.high ^ self.LookupHigh[thisval]) & 0xFF
        self.low = (self.low ^ self.LookupLow[thisval]) & 0xFF

    def update(self, val):
        """Updates the CRC value using bitwise operations."""
        self.extract_bits(val >> 4)    # High nibble first
        self.extract_bits(val & 0x0F)  # Low nibble

    def run(self, message):
        """Calculates CRC-16 over a byte sequence, returning [low, high]."""
        for value in message:
            self.update(value)
        return [self.low, self.high]
```

#### 2. C (Appendix A of Protocol Spec)
```c
/* Heatmiser V3 Protocol Specification - Appendix A */
static const unsigned char CRC16_LookupHigh[16] = {
    0x00, 0x10, 0x20, 0x30, 0x40, 0x50, 0x60, 0x70,
    0x81, 0x91, 0xA1, 0xB1, 0xC1, 0xD1, 0xE1, 0xF1
};
static const unsigned char CRC16_LookupLow[16] = {
    0x00, 0x21, 0x42, 0x63, 0x84, 0xA5, 0xC6, 0xE7,
    0x08, 0x29, 0x4A, 0x6B, 0x8C, 0xAD, 0xCE, 0xEF
};

static unsigned char CRC16_High = 0xFF;
static unsigned char CRC16_Low  = 0xFF;

void CRC16_Init(void) {
    CRC16_High = 0xFF;
    CRC16_Low  = 0xFF;
}

void CRC16_Update4Bits(unsigned char val) {
    unsigned char t = (CRC16_High >> 4) ^ val;
    CRC16_High = (unsigned char)((CRC16_High << 4) | (CRC16_Low >> 4));
    CRC16_Low  = (unsigned char)(CRC16_Low << 4);
    CRC16_High ^= CRC16_LookupHigh[t];
    CRC16_Low  ^= CRC16_LookupLow[t];
}

void CRC16_Update(unsigned char val) {
    CRC16_Update4Bits(val >> 4);   /* High nibble first */
    CRC16_Update4Bits(val & 0x0F); /* Low nibble */
}

void CRC16_Calculate(const unsigned char *data, size_t len, unsigned char *out_low, unsigned char *out_high) {
    CRC16_Init();
    for (size_t i = 0; i < len; ++i) {
        CRC16_Update(data[i]);
    }
    *out_low  = CRC16_Low;
    *out_high = CRC16_High;
}
```

#### 3. JavaScript / TypeScript (Digital Twin & Browser)
```typescript
const CRC16_LOOKUP_HIGH = [
  0x00, 0x10, 0x20, 0x30, 0x40, 0x50, 0x60, 0x70,
  0x81, 0x91, 0xA1, 0xB1, 0xC1, 0xD1, 0xE1, 0xF1
];
const CRC16_LOOKUP_LOW = [
  0x00, 0x21, 0x42, 0x63, 0x84, 0xA5, 0xC6, 0xE7,
  0x08, 0x29, 0x4A, 0x6B, 0x8C, 0xAD, 0xCE, 0xEF
];

export function calculateCRC16(data: Uint8Array | number[]): [number, number] {
  let high = 0xFF;
  let low = 0xFF;

  function update4Bits(val: number) {
    const t = ((high >> 4) ^ val) & 0x0F;
    high = (((high << 4) | (low >> 4)) ^ CRC16_LOOKUP_HIGH[t]) & 0xFF;
    low = ((low << 4) ^ CRC16_LOOKUP_LOW[t]) & 0xFF;
  }

  for (let i = 0; i < data.length; i++) {
    const byte = data[i];
    update4Bits((byte >> 4) & 0x0F); // High nibble first
    update4Bits(byte & 0x0F);        // Low nibble
  }

  return [low, high]; // Returns [Low Byte, High Byte]
}
```

#### 4. Rust
```rust
const CRC16_LOOKUP_HIGH: [u8; 16] = [
    0x00, 0x10, 0x20, 0x30, 0x40, 0x50, 0x60, 0x70,
    0x81, 0x91, 0xA1, 0xB1, 0xC1, 0xD1, 0xE1, 0xF1,
];
const CRC16_LOOKUP_LOW: [u8; 16] = [
    0x00, 0x21, 0x42, 0x63, 0x84, 0xA5, 0xC6, 0xE7,
    0x08, 0x29, 0x4A, 0x6B, 0x8C, 0xAD, 0xCE, 0xEF,
];

pub struct HeatmiserCrc16 {
    high: u8,
    low: u8,
}

impl HeatmiserCrc16 {
    pub fn new() -> Self {
        Self { high: 0xFF, low: 0xFF }
    }

    fn update_4bits(&mut self, val: u8) {
        let t = ((self.high >> 4) ^ val) as usize;
        self.high = (self.high << 4) | (self.low >> 4);
        self.low <<= 4;
        self.high ^= CRC16_LOOKUP_HIGH[t];
        self.low ^= CRC16_LOOKUP_LOW[t];
    }

    pub fn update(&mut self, val: u8) {
        self.update_4bits(val >> 4);
        self.update_4bits(val & 0x0F);
    }

    pub fn calculate(data: &[u8]) -> [u8; 2] {
        let mut crc = Self::new();
        for &b in data {
            crc.update(b);
        }
        [crc.low, crc.high] // [Low Byte, High Byte]
    }
}
```

#### 5. Go
```go
package heatmiserv3

var (
    crcLookupHigh = [16]byte{
        0x00, 0x10, 0x20, 0x30, 0x40, 0x50, 0x60, 0x70,
        0x81, 0x91, 0xA1, 0xB1, 0xC1, 0xD1, 0xE1, 0xF1,
    }
    crcLookupLow = [16]byte{
        0x00, 0x21, 0x42, 0x63, 0x84, 0xA5, 0xC6, 0xE7,
        0x08, 0x29, 0x4A, 0x6B, 0x8C, 0xAD, 0xCE, 0xEF,
    }
)

// CalculateCRC16 computes the Heatmiser V3 CRC-16 checksum returning (low, high).
func CalculateCRC16(data []byte) (byte, byte) {
    high := byte(0xFF)
    low := byte(0xFF)

    update4Bits := func(val byte) {
        t := (high >> 4) ^ val
        high = (high << 4) | (low >> 4)
        low = low << 4
        high ^= crcLookupHigh[t]
        low ^= crcLookupLow[t]
    }

    for _, b := range data {
        update4Bits(b >> 4)    // High nibble first
        update4Bits(b & 0x0F)  // Low nibble
    }

    return low, high
}
```

---

## 4. Thermostat Models & Model IDs

The byte at DCB index `4` identifies the hardware model:

| Model ID (Dec / Hex) | Model Name | Description | DCB Size (Bytes) |
| :---: | :--- | :--- | :---: |
| `00` (`0x00`) | **DT** | Digital Thermostat (Non-programmable) | 36 |
| `01` (`0x01`) | **DT-E** | Digital Thermostat with Floor Sensor (Electric UFH) | 36 |
| `02` (`0x02`) | **PRT** | Programmable Room Thermostat (5/2 or 7 day) | 64 (5/2) / 148 (7d) |
| `03` (`0x03`) | **PRT-E** | Programmable Room Thermostat with Floor Sensor | 64 (5/2) / 148 (7d) |
| `04` (`0x04`) | **PRTHW** | Programmable Room Thermostat + Hot Water Channel | 73 (5/2) / 157 (7d) |
| `05` (`0x05`) | **TM1** | Single/Dual Channel Time Clock / Programmer | 43 (5/2) / 157 (7d) |
| `07` (`0x07`) | **HC-EN** | Heating & Cooling Electronic Network Thermostat | 73 (5/2) / 162 (7d) |
| `20` / `21` (`0x14`/`0x15`) | **OTS** | Outside Temperature Sensor (Fixed Addr `81`) | 11 |
| `22` (`0x16`) | **HTS** | Humidity & Temperature Sensor (Addrs `41`–`72`) | 22 |

---

## 5. Device Control Block (DCB) Memory Maps

### 5.1 DT / DT-E / PRT / PRT-E Telemetry & Configuration Table

| Write Addr | DCB Index | Parameter Name | Format / Range | Default | Notes |
| :---: | :---: | :--- | :--- | :---: | :--- |
| — | `0` | DCB Length High | 1 Byte | — | Total length in bytes |
| — | `1` | DCB Length Low | 1 Byte | — | 36 (DT), 64 (PRT 5/2), 148 (PRT 7d) |
| — | `2` | Vendor ID | `00` = Heatmiser, `01` = OEM | `00` | Read-only |
| — | `3` | Version & Floor Limit | Bit 0–6 = Version, Bit 7 = Floor Limit | — | Bit 7: `1` = Overheat trip active |
| — | `4` | Model ID | `00`=DT, `01`=DT-E, `02`=PRT, `03`=PRT-E | `02` | Read-only |
| `5` | `5` | Temperature Format | `00` = °C, `01` = °F | `00` | R/W |
| `6` | `6` | Switch Differential | `1` to `3` °C | `1` | R/W |
| `7` | `7` | Frost Protect Enable | `0` = Disabled, `1` = Enabled | `1` | Read-only status |
| `8` | `8` | Calibration Offset High | High byte | `0` | Signed 16-bit offset |
| `9` | `9` | Calibration Offset Low | Low byte | `0` | |
| `10` | `10` | Output Delay | `0` to `15` minutes | `0` | Compressor / relay delay |
| `11` | `11` | Thermostat Address | `1` to `32` | `1` | Network ID |
| `12` | `12` | Up/Down Key Limit | `0` to `10` °C | `0` | Front-panel adjustment limit |
| **`13`** | **`13`** | **Sensor Selection** | **`0` to `4`** | **`0`** | **See Section 6 for full details** |
| `14` | `14` | Optimum Start | `0` to `3` hours | `0` | Self-learning warm up |
| `15` | `15` | Rate of Change | Minutes per °C | `20` | Thermal response rate |
| `16` | `16` | Program Mode | `00` = 5/2 mode, `01` = 7-day mode | `00` | Schedule mode |
| `17` | `17` | Frost Protect Temp | `7` to `17` °C | `12` | Setback temp when OFF |
| `18` | `18` | Set Room Temperature | `5` to `35` °C | `16` | Current comfort setpoint |
| `19` | `19` | Floor Max Limit | `20` to `45` °C | `28` | Thermal cutout threshold |
| `20` | `20` | Floor Max Limit Enable | `00` = Disable, `01` = Enable | `01` | Fixed to enable in firmware |
| `21` | `21` | On / Off (Run State) | `00` = Off / Frost, `01` = On | `01` | R/W |
| `22` | `22` | Key Lock | `00` = Unlocked, `01` = Locked | `00` | Front keypad lockout |
| `23` | `23` | Run Mode | `00` = Heating, `01` = Frost Protect | `00` | R/W |
| `24` | `24` | Holiday Hours Low/High | Hours remaining (0–999) | `0` | Low byte when write; High byte when read |
| `25` | `25` | Holiday Hours High/Low | Hours remaining | `0` | High byte when write; Low byte when read |
| `26` | `26` | Temp Hold Mins High | Hold minutes (High byte) | `0` | Read: High byte first; Write: Low byte first |
| `27` | `27` | Temp Hold Mins Low | Hold minutes (Low byte) | `0` | |
| — | `28` | Remote Air Temp High | Temp × 10 (High byte) | `0xFF` | `0xFFFF` if disconnected |
| — | `29` | Remote Air Temp Low | Temp × 10 (Low byte) | `0xFF` | Actual temp = value / 10 |
| — | `30` | Floor Temp High | Temp × 10 (High byte) | `0xFF` | `0xFFFF` if disconnected |
| — | `31` | Floor Temp Low | Temp × 10 (Low byte) | `0xFF` | Actual temp = value / 10 |
| — | `32` | Built-in Air Temp High | Temp × 10 (High byte) | `0xFF` | Internal sensor |
| — | `33` | Built-in Air Temp Low | Temp × 10 (Low byte) | `0xFF` | Actual temp = value / 10 |
| — | `34` | Sensor Error Code | `0`=OK, `0xE0`=Air, `0xE1`=Floor, `0xE2`=Remote | `0` | Error diagnostic flag |
| — | `35` | Current State | `00` = Off, `01` = Heating Active | `0` | Relay 1 state |
| — | `36`..`63` | 5/2 Schedule | 4 Weekday + 4 Weekend periods | — | Time (Hr/Min) + Setpoint |
| — | `64`..`147`| 7-Day Schedule | Mon through Sun (4 periods each) | — | 7 days × 4 periods (12 bytes/day) |

---

### 5.2 PRTHW Telemetry & Hot Water Additions

PRTHW shares the PRT telemetry structure, with the following key differences:
* **Model ID**: `04` (`0x04`).
* **Sensor Selection (Addr 13)**: **Fixed to `00` (Built-in air sensor only)**. Remote and floor sensors are unsupported because terminal relays are assigned to hot water control.
* **Current Hot Water State**: DCB index `36` (Read) / Index `41` (Write Boost). `00` = Hot water off, `01` = Hot water heating on.
* **Dual Channel Programming**: Contains separate 4-period Heating schedule and 4-period Hot Water timer schedule for weekdays and weekends.

---

### 5.3 TM1 Time Clock / Programmer

TM1 operates strictly as a time switch / programmer with no temperature regulation:
* **Model ID**: `05` (`0x05`).
* **Sensor Selection**: **None / Not Present**.
* **Timer Mode (Addr 16)**: `00` = 5/2 mode, `01` = 7-day mode, `02` = Countdown timer mode.
* **Current Timer State (Addr 42 / DCB Index 14)**:
  * Read: `00` = Timer off, `01` = Timer on.
  * Write: `00` = Auto (follow schedule), `01` = Override ON, `02` = Override OFF.
* **Countdown Minutes (Addr 26 / DCB Index 12–13)**: 16-bit integer (0–1800 minutes).

---

### 5.4 HC-EN (Heating & Cooling)

* **Model ID**: `07` (`0x07`).
* **Sensor Selection**: Addr `13`, DCB Index `9` (supports modes `00` to `04`).
* **Humidity Sensor Address**: DCB Index `7` (links to external HTS sensor).
* **Relative Humidity**: DCB Index `36` (Addr `30`). Returns RH% (0–100%).
* **Dew Point Temperature**: DCB Index `37` (Addr `28`). Calculated dew point in °C.
* **Cooling Controls**:
  * Run Mode `28`: `00` = Heat, `01` = Frost, `02` = Cool.
  * Floor Min Limit `23`: `[10, 30]` °C (prevents cooling below dew point to avoid floor condensation).
  * Output State `38`: Bit 0 = Heat On, Bit 1 = Heat Floor Limit, Bit 4 = Cool On, Bit 5 = Cool Floor Limit, Bit 6 = Dew Point Reached.

---

## 6. Temperature Source & Sensor Selection Specification

Parameter **Sensor Selection** is controlled by writing a 1-byte value to **Address 13**:

```
xx 0b ** 01 0d 00 01 00 <mode> ## ##
```
*(Where `0d 00` = 13 in hex, `01 00` = 1 byte payload)*

### 6.1 Supported Modes

| Mode Value | Name | Primary Comfort Sensor | Floor Limit Interlock Active? |
| :---: | :--- | :--- | :---: |
| `00` (`0x00`) | **Built-in Air Sensor Only** *(Default)* | Internal casing thermistor | No |
| `01` (`0x01`) | **Remote Air Sensor Only** | External remote air probe | No |
| `02` (`0x02`) | **Floor Sensor Only** | Floor screed probe | Yes (Primary control) |
| `03` (`0x03`) | **Built-in Air + Floor Sensor** | Internal casing thermistor | **Yes (Safety cutout at Addr 19)** |
| `04` (`0x04`) | **Remote Air + Floor Sensor** | External remote air probe | **Yes (Safety cutout at Addr 19)** |

### 6.2 Floor Overheat Safety Interlock Logic
When configured for Mode `02`, `03`, or `04`:
1. The thermostat polls the floor probe embedded in the floor screed (reported at DCB bytes 30–31).
2. If the floor temperature reaches or exceeds **Floor Max Limit** (Addr `19`, default 28°C, range 20–45°C):
   * Heating relay is **immediately forced open (OFF)**.
   * Bit 7 of DCB Byte 3 is asserted (`1`), signaling `Floor Limit State`.
   * The LCD displays `FLR HI` and flashes a thermal warning.
3. Once the floor probe cools by 1.0°C below the limit, the interlock resets.
4. If the floor probe becomes disconnected while in Mode 2, 3, or 4:
   * Diagnostic Error `E1` is raised (DCB byte 34 = `0xE1`).
   * Heating relay is safely held open.

### 6.3 Temperature Resolution, Quantization, and Display vs. Wire Representation

A key nuance when integrating Heatmiser thermostats across automation systems (Home Assistant, custom scripts, digital twins) is understanding the distinction between the **wire protocol capability** and the **physical thermostat hardware behavior**:

| Aspect | Wire Protocol (RS485 DCB) | Physical Thermostat (PRT-1 / Slimline LCD) |
| :--- | :--- | :--- |
| **Current / Ambient Temp** | 16-bit Big-Endian, scaled $\times 10$ (`value / 10`), **0.1°C resolution** | Quantized to **0.5°C increments** (or whole degrees), $\pm 0.5^\circ\text{C}$ to $\pm 1.0^\circ\text{C}$ accuracy |
| **Can it report `16.7°C`?** | **Yes** over the bus (raw integer `167`), supported by wire format | **No on LCD**; display quantizes `16.7°C` to **`16.5°C`** (or `17.0°C`) |
| **Set Room Temp (Addr 18)** | 1-Byte integer setpoint (`5` to `35` °C) | Adjustable in `0.5°C` or `1.0°C` button steps |
| **Switching Differential (Addr 6)** | 1-Byte integer (`1` to `3` °C hysteresis) | Feature 02: `1.0°C` default (or `0.5°C` on select revisions) |

* **Protocol Layer**: Raw ADC values can technically populate DCB bytes 28–33 with fractional tenths (`value / 10`).
* **Physical Hardware Layer**: The LCD panel utilizes fixed 7-segment digits with a fractional `.5` annunciator segment. The internal firmware quantizes ambient room measurements to 0.5°C steps for display and regulation decisions. On the wall unit, users see 16.5°C or 17.0°C, never 16.7°C.

---

## 7. Programming Schedules & Cancellation Rules

### 7.1 Program Modes
* **Mode 0 (5/2 Day)**: Monday–Friday share 4 Comfort Levels (Wake, Leave, Return, Sleep); Saturday–Sunday share 4 Comfort Levels.
* **Mode 1 (7 Day)**: Monday through Sunday have individual 4 Comfort Levels (28 periods total).

### 7.2 Period Cancellation Convention
* In comfort temperature schedules, setting **`Hour = 24`** (`0x18`) indicates that the period is **cancelled / skipped**.
* In setpoint schedules, setting **`Set Temp = 24`** (`0x18`) on some older firmware also indicates period cancellation.

---

## 8. Summary of Unique Parameter Write Addresses

| Address (Dec) | Address (Hex) | Parameter Name | Payload Length | Data Range |
| :---: | :---: | :--- | :---: | :--- |
| `5` | `0x05` | Temperature Format | 1 Byte | `0` = °C, `1` = °F |
| `6` | `0x06` | Switch Differential | 1 Byte | `1` to `3` °C |
| `11` | `0x0B` | Thermostat Network Address | 1 Byte | `1` to `32` |
| `12` | `0x0C` | Keypad Up/Down Limit | 1 Byte | `0` to `10` °C |
| **`13`** | **`0x0D`** | **Sensor Selection Mode** | **1 Byte** | **`0` to `4`** |
| `14` | `0x0E` | Optimum Start | 1 Byte | `0` to `3` hours |
| `16` | `0x10` | Program Mode | 1 Byte | `0` = 5/2, `1` = 7-day |
| `17` | `0x11` | Frost Protection Temperature | 1 Byte | `7` to `17` °C |
| `18` | `0x12` | Set Room Temperature | 1 Byte | `5` to `35` °C |
| `19` | `0x13` | Floor Max Limit | 1 Byte | `20` to `45` °C |
| `21` | `0x15` | On / Off Power State | 1 Byte | `0` = Off, `1` = On |
| `22` | `0x16` | Key Lock | 1 Byte | `0` = Unlocked, `1` = Locked |
| `23` | `0x17` | Run Mode | 1 Byte | `0` = Heat, `1` = Frost |
| `24` | `0x18` | Holiday Hours | 2 Bytes | `0` to `999` hours |
| `26` | `0x1A` | Countdown Minutes (TM1) | 2 Bytes | `0` to `1800` minutes |
| `41` | `0x29` | Hot Water State (PRTHW) | 1 Byte | `0` = Auto, `1` = Boost On |
| `42` | `0x2A` | Timer Override (TM1) | 1 Byte | `0` = Auto, `1` = On, `2` = Off |
