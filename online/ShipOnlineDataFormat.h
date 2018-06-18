#ifndef ONLINE_SHIPONLINEDATAFORMAT_H
#define ONLINE_SHIPONLINEDATAFORMAT_H

#include <cstdint>

struct RawDataHit {
   uint16_t channelId;    // Channel Identifier
   uint16_t hitTime;      // Hit time, coarse 25ns based time in MSByte, fine time in LSByte
   uint16_t extraData[0]; // Optional subdetector specific data items
};

struct DataFrameHeader {
   uint16_t size;            // Length of the data frame in bytes (including header).
   uint16_t partitionId;     // Identifier of the subdetector and partition.
   uint32_t cycleIdentifier; // SHiP cycle identifier as received from TFC.
   uint32_t frameTime;       // Frame time in 25ns clock periods
   uint16_t timeExtent;      // sequential trigger number
   uint16_t flags;           // Version, truncated, etc.
};

struct DataFrame {
   DataFrameHeader header;
   RawDataHit hits[0];
   // DataFrameHeader
   // Address of first raw data hit.
   // for a partition with a fixed hit structure size, the actual number of hits is given by
   // the frame size and the hit size:
   int getHitCount() { return (header.size - sizeof(header)) / sizeof(RawDataHit); }
};

namespace DriftTubes {
struct ChannelId {
   uint16_t channel : 8;
   uint16_t TDC : 4;
   uint16_t edge : 1;
   uint16_t padding : 3;
   int GetDetectorId()
   {
      bool trigger = (TDC == 0 || TDC == 2) ? channel == 126 : (TDC == 1 || TDC == 4) ? channel == 0 : false;
      if (trigger) {
         return 0;
      }
      if ((TDC == 0 && channel == 127) || (TDC == 1 && channel == 1)) {
         // Scintillator S1/S2.1/S2.2
         return 6;
      } else if ((TDC == 2 && channel == 127) || (TDC == 4 && channel == 1)) {
         // Scintillator S2/S2.3/S2.4
         return 7;
      } else if (TDC == 4 && (channel >= 112 && channel <= 115)) {
         // BC Scintillator
         return -1;
      }
      int channel_offset = (TDC == 1 && channel < 80) ? 64 : (TDC == 1) ? 1 : (TDC == 2) ? -119 : (TDC == 4) ? -31 : 0;
      bool reverse = !((TDC == 0 && channel >= 96) || (TDC == 1 && channel < 80));
      int _channel = channel;
      _channel += channel_offset;
      _channel += (_channel < 0) ? 0x80 : 0;
      _channel = reverse ? (0x80 - _channel % 0x80) % 0x80 : _channel;
      if (TDC == 0 && channel < 96) {
         _channel += _channel ? 63 : 191;
      }

      int module = _channel / 48 + 1;
      module += (TDC == 1 && channel < 80) ? 1 : (TDC == 0 && channel < 96) ? 1 : 0;
      int station =
         (TDC == 4)
            ? 3
            : (TDC == 2) ? 3 : (TDC == 1 && channel >= 80) ? 3 : (TDC == 1) ? 2 : (TDC == 0 && channel >= 96) ? 2 : 1;
      int view = (TDC == 0) ? (module - 1) % 2 : (TDC == 1) ? (module - 1) % 2 : 0;
      int plane = (TDC == 2) ? ((_channel % 48) / 24 + 1) % 2 : (_channel % 48) / 24;
      int layer = (_channel % 24) / 12;
      int straw = _channel % 12 + 1;
      return station * 10000000 + view * 1000000 + plane * 100000 + layer * 10000 + 2000 + straw;
   };
};
struct Flags {
   uint16_t completely_different_settings : 1;
   uint16_t width_resolution : 3;
   uint16_t time_resolution : 2;
   uint16_t measurement_type : 2;
   uint16_t padding : 8;
};
} // namespace DriftTubes

#endif
