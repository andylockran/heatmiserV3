# Schema Files

I couldn't work out how to set the schema files appropriately, but it feels like jsonschema could be useful; so giving that a try.


## Messaging frames

This folder contains some example schemas (.schema.json) and some examples in examples/folder to validate them.

### message.schema.json

This is the command frame format.  


| Byte Order | Field | Value |
| -----------|-------|-------|
| 0 | destinationAddress | [1,32] |
| 1 | frameLength | 10 (when read), n+10 (when write) |
| 2 | sourceAddress | [129,160] The address this command is originating from |
| 3 | functionCode | 1 (write), 0 (read) |
| 4 | startAddressLow | [0, DCB_Len-1] different models of stats have different lengths of DCB. |
| 5 | startAddressHigh | [0, DCB_Len-1] different models of stats have different lengths of DCB. |
| 6 | endAddressLow | [1, DCB_Len], 255 means read the whole DCB |
| 7 | endAddressHigh | [1, DCB_Len], 255 means read the whole DCB |
| 8 ..(n+8) | contents | If function code is 0, no this segment |
| N+1 | crcLow | CRC code from 0 to n+8, crc code not included in calculation |
| N+2 | crcHigh | CRC code from 0 to n+8, crc code not included in calculation |


### reply.schema.json

This is the command frame response format.  


| Byte Order | Field | Value |
| -----------|-------|-------|
| 0 | destinationAddress | [129,160] |
| 1 | frameLengthLow | 7 (when write), 11+n (when read) - crc code included |
| 2 | frameLengthHigh | 7 (when write), 11+n (when read) - crc code included |
| 3 | sourceAddress | [1,32], broadcast frame has no reply |
| 4 | functionCode | 01 (write), 00 (read) |
| 5 | startAddressLow | If function code is 1, no these segments |
| 6 | startAddressHigh | If function code is 1, no these segments |
| 7 | endAddressLow | If function code is 1, no these segments|
| 8 | endAddressHigh | If function code is 1, no these segments. |
| 9 ..(n+9) | contents | Contents for reading |
| N+1 | crcLow | CRC code of this frame, crc code not included in calculation |
| N+2 | crcHigh | CRC code of this frame, crc code not included in calculation |

## Reading and writing a COMMAND frame

Only one master can be connected to a RS485 network and originate a session.  The protocol does not allow for bus arbitration, so if more than one master is connected, data corruption will occur if there is a conflict.

The master node can read all parts of the DCB from a slave node, and can write to some parts of the DCB by sending command frames.

### Reading

A broadcast frame cannot be used for reading data.

Read the entire DCB for each device to ensure you have appropriate data before making a write command.

To read a DCB (e.g. at destinationAddress 1), send the frame below:
```json
{
    "thermostat": 1, 
    "operation": 10,
    "sourceAddress": 129,
    "readFunctionCode": 0,
    "startAddressLow": 0,
    "startAddressHigh": 0,
    "endAddressLow": 255,
    "endAddressHigh": 255,
    "crcLow": 212, 
    "crcHigh": 141,
}
```

N.B the crcLow and crcHigh are calculated by the CRC algorithm.

Care should be taken when reading parts of the DCB, the addresses of all parameters must be contiguous, otherwise there will be no reply.

If the DCB length of a particular model is shorter than that which we are attempting to read, then we will get no reply.

### Writing

Broadcast frames can be sent but do not generate a reply and receipt is not guaranteed.

If they are used, the should be sent three times, to ensure reliability.

Some DCB params are readonly, wherears others are read/write.
Sending a write comment to a read address will fail silently.

See the DCB Schemas for each thermostat to note which are write and which are read/write.

Within the DCB, any data can be read at random, but when writing you must write to the function starting address (it's lowest address).

Example, if we want to modify the frost setting (address 17), and set the room temp (address 18), we cannot do them both at the same time, as even though they're contiguous, they are across two function groups.

For parameters with two bytes, we only need to send one command to write two bytes, with the address of the low 8bit as the starting address.

## DCB Structures

The library was initially written for the PRT model thermostat over RS485.  The following structures are defined in the schemas, but should allow you to understand how to access and write more helper functions for the thermostat class.

For those with 2 byte parameters, when reading, high 8 bits are sent first, while for writing the low 8 bit should be sent first since the MCU used on the RS485 model thermostats is in big-endian format.

Note: For backwards compatibility, Wifi devices output their data using the following data structures, but this library currently does not support communication over Wifi.

### DT/DT-E/PRT/PRT-E

Each model of thermostat uses different DCB structures, so data returned and the data length will differ.

DT/DT-E has 36 bytes.
PRT/PRT-E has 64 bytes in 5/2 day programming mode.
PRT/PRT-E has 148 bytes in 7 day programming mode.

