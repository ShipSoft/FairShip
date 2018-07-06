#ifndef ONLINE_SHIPONLINEDATAFORMAT_H
#define ONLINE_SHIPONLINEDATAFORMAT_H

#include <cstdint>
#include <cassert>
#include <iostream>

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
   int GetDetectorId() const
   {
      bool trigger = false;
      bool beamcounter = false;
      bool RC_signal = false;
      bool scintillatorA = false;
      bool scintillatorB = false;
      int module = 0;
      int station = 0;
      int channel_offset = 0;
      switch (TDC) {
      case 0:
         trigger = channel == 126;
         scintillatorA = channel == 127;
         station = (channel < 96) ? 1 : 2;
         module = (channel / 48) % 2;
         break;
      case 1:
         trigger = channel == 0;
         scintillatorA = channel == 1;
         station = (channel < 80) ? 2 : 3;
         channel_offset = (channel < 80) ? 112 : 1;
         break;
      case 2:
         trigger = channel == 126;
         scintillatorB = channel == 127;
         station = 4;
         channel_offset = -119;
         module = (channel / 48) % 3 + 1;
         break;
      case 3:
         trigger = channel == 0;
         scintillatorB = channel == 1;
         station = (channel < 32) ? 4 : 3;
         channel_offset = (channel < 32) ? 1 : 33;
         module = ((channel + 16) / 48 + 3) % 4;
         break;
      case 4:
         trigger = channel == 96;
         RC_signal = channel == 97 || channel == 98;
         beamcounter = channel > 111;
         module = (channel / 48) % 2 + 2;
         channel_offset = (channel < 48) ? 33 : 0;
         station = 3;
         break;
      }
      if (trigger) {
         return 0;
      } else if (beamcounter || RC_signal) {
         return -1;
      } else if (scintillatorA) {
         return 6;
      } else if (scintillatorB) {
         return 7;
      }
      bool reverse_x = !(station == 2 || (TDC == 4 && channel >= 48));
      int _channel = channel + channel_offset;
      _channel += (_channel < 0) ? 0x80 : 0;
      _channel = reverse_x ? (0x80 - _channel % 0x80) % 0x80 : _channel;
      if (TDC == 0 && channel < 96) {
         _channel += _channel ? 63 : 191;
      } else if (TDC == 3 && channel < 96) {
         _channel += (channel < 32) ? 24 : 32;
      }
      if (TDC == 1) {
         module = (_channel / 48) % 2;
      }

      int view = station == 1 || station == 2 ? module % 2 : 0;
      int plane = (TDC == 2) ? ((_channel % 48) / 24 + 1) % 2
                             : (station == 3 && TDC == 4) ? 1 - (channel % 48) / 24 : (_channel % 48) / 24;
      if (station == 4 && TDC == 3) {
         plane -= 1;
      }
      int layer = (TDC == 4) ? 1 - (channel % 24) / 12 : (_channel % 24) / 12;
      int straw = _channel % 12 + ((station == 3 || station == 4) ? 1 + (3 - module) * 12 : 1);
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
const uint16_t delay(2000 / 0.098); // TODO update value
} // namespace DriftTubes

enum Direction { horizontal, vertical };
namespace RPC {
struct RawHit {
   uint16_t ncrate : 8;
   uint16_t nboard : 8;
   uint16_t hitTime;
   uint8_t pattern[8];
};
} // namespace RPC

#endif
