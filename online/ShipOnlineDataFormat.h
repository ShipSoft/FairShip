#ifndef ONLINE_SHIPONLINEDATAFORMAT_H
#define ONLINE_SHIPONLINEDATAFORMAT_H

struct RawDataHit {
    uint16_t channelId; // Channel Identifier
    uint16_t hitTime; // Hit time, coarse 25ns based time in MSByte, fine time in LSByte
    uint16_t extraData[0]; // Optional subdetector specific data items
};

struct DataFrameHeader {
    uint16_t size; // Length of the data frame in bytes (including header).
    uint16_t partitionId; // Identifier of the subdetector and partition.
    uint32_t cycleIdentifier; // SHiP cycle identifier as received from TFC.
    uint32_t frameTime; // Frame time in 25ns clock periods
    uint16_t timeExtent; // sequential trigger number
    uint16_t flags; // Version, truncated, etc.
};

struct DataFrame{
    DataFrameHeader header;
    RawDataHit hits[0];
// DataFrameHeader
// Address of first raw data hit.
// for a partition with a fixed hit structure size, the actual number of hits is given by
// the frame size and the hit size:
    int getHitCount() { return (header.size-sizeof(header))/sizeof(RawDataHit); }
};

#endif
