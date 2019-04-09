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
      bool master_trigger = false;
      bool blacklisted = false;
      int module = 0;
      int station = 0;
      int channel_offset = 0;
      switch (TDC) {
      case 0:
         trigger = channel == 126;
         scintillatorA = channel == 127;
         station = (channel < 96) ? 1 : 2;
         module = (channel / 48) % 2;
         blacklisted = channel >= 120;
         break;
      case 1:
         trigger = channel == 0;
         scintillatorA = channel == 1;
         station = (channel < 80) ? 2 : 4;
         channel_offset = (channel < 80) ? 112 : 1;
         channel_offset += (channel >= 32 && channel < 48) ? +16 : (channel >= 48 && channel < 64) ? -16 : 0;
         blacklisted = channel < 8;
         blacklisted |= channel >= 128;
         break;
      case 2:
         trigger = channel == 126;
         scintillatorB = channel == 127;
         station = 4;
         channel_offset = -119;
         module = (channel / 48) % 3 + 1;
         blacklisted = channel >= 120;
         break;
      case 3:
         trigger = channel == 0;
         scintillatorB = channel == 1;
         station = (channel < 32) ? 4 : 3;
         channel_offset = (channel < 32) ? 1 : 33;
         module = ((channel + 16) / 48 + 3) % 4;
         blacklisted = channel < 8;
         blacklisted |= channel >= 128;
         break;
      case 4:
         trigger = channel == 96;
         RC_signal = channel == 97 || channel == 98;
         master_trigger = channel == 99;
         beamcounter = channel > 111;
         module = (channel / 48) % 2 + 2;
         channel_offset = (channel < 48) * 33;
         station = 3;
         blacklisted = channel >= 96;
         break;
      }
      if (trigger) {
         return 0;
      } else if (master_trigger) {
         return 1;
      } else if (beamcounter || RC_signal) {
         return -1;
      } else if (scintillatorA) {
         return 6;
      } else if (scintillatorB) {
         return 7;
      } else if(blacklisted) {
         return -2;
      }
      bool reverse_x = !(station == 2 || (TDC == 4 && channel >= 48));
      int _channel = channel + channel_offset;
      _channel += (_channel < 0) * 0x80;
      _channel = reverse_x ? (0x80 - _channel % 0x80) % 0x80 : _channel;
      if (TDC == 0 && channel < 96) {
         _channel += _channel ? 63 : 191;
      } else if (TDC == 3 && channel < 96) {
         _channel += (channel < 32) ? 24 : 32;
      }
      if (TDC == 1) {
         module = (_channel / 48) % 2;
      }

      int view = (station == 1 || station == 2) * module % 2;
      int plane = (TDC == 2) ? ((_channel % 48) / 24 + 1) % 2
                             : (station == 3 && TDC == 4) ? 1 - (channel % 48) / 24 : (_channel % 48) / 24;
      if (station == 4 && TDC == 3) {
         plane -= 1;
      }
      int layer = (TDC == 4) ? 1 - (channel % 24) / 12 : (_channel % 24) / 12;
      int straw = _channel % 12 + ((station == 3 || station == 4) ? 1 + (3 - module) * 12 : 1);
      return station * 10000000 + view * 1000000 + plane * 100000 + layer * 10000 + 2000 + straw;
   };
  int GetDetectorIdCharm() const
   {
     bool trigger = false;
     bool beamcounter = false;
     bool RC_signal = false;
     bool master_trigger = false;
     int module = 0;
     int station = 0;
     int module_channel = 0;
     switch (TDC) {
     case 0:
       trigger = channel == 126 || channel == 120;
       RC_signal = channel == 121 || channel == 122;
       master_trigger = channel == 123;
       station = 3;
       module = (channel < 96) ? 2 + (channel / 48) % 2 : 0;
       module_channel = channel % 48;
       //reverse front end board
       if(module == 3) module_channel = 12*(module_channel/12)+(11-module_channel%12);
       break;
     case 1:
       trigger = channel == 0;
       beamcounter = channel >=2 && channel <= 5;
       station = (channel < 80) ? 3 : 4;
       module = (channel >= 32 && channel < 80) ? 1 : 0;
       module_channel = (channel + 16) % 48;
       //cable swap
       if(module==1) module_channel += ( module_channel < 16 ) ? 16 : ( module_channel < 32 ) ? -16 : 0;
       break;
     case 2:
       trigger = channel == 126;
       station = 4;
       module = (channel / 48)  + 1 ;
       module_channel = channel % 48;
       break;
     case 3:
       trigger = channel == 0;
       station = (channel < 32 || channel >= 80) ? 4 : 3;
       module = (channel < 32 ) ? 3 : 4;
       module_channel = (channel + 16) % 48;
       break;
     }
     if (trigger) {
       return 0;
     } else if (master_trigger) {
       return 1;
     } else if (beamcounter || RC_signal) {
       return -1;
     }
     
     int plane = 1 - (module_channel / 24);
     int layer = 1 - (module_channel % 24) / 12;
     int straw = (module >= 4 ? module : 3 - module) * 12 + (11 - (module_channel % 12)) + 1;
     
     return station * 10000000 + plane * 100000 + layer * 10000 + 2000 + straw;
   };
};
enum Flag : uint16_t {
   All_OK = 1,
   TDC0_PROBLEM = 1 << 1,
   TDC1_PROBLEM = 1 << 2,
   TDC2_PROBLEM = 1 << 3,
   TDC3_PROBLEM = 1 << 4,
   TDC4_PROBLEM = 1 << 5,
   NoTrigger = 1<<12,
   NoWidth = 1<<13,
   NoDelay = 1<<14,
   InValid = 1<<15,
};
} // namespace DriftTubes

enum MagicFrameTime { SoS = 0xFF005C03, EoS = 0xFF005C04 };

#endif
