# Schema Files

I couldn't work out how to set the schema files appropriately, but it feels like jsonschema could be useful; so giving that a try.

This folder contains some example schemas (.schema.json) and some examples in examples/folder to validate them.

## message.schema.json

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


## reply.schema.json

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
