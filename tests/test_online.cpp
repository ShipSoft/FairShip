#define CATCH_CONFIG_MAIN
#include "/usr/include/catch/catch.hpp"
#include "../online/ShipOnlineDataFormat.h"
#include "ROOT/TSeq.hxx"

using namespace DriftTubes;

int DetectorIdTest(uint16_t channel)
{
   ChannelId *test = reinterpret_cast<ChannelId *>(&channel);
   int detId = test->GetDetectorId();
   /* std::cout << "Stat:" << "\t" << detId/10000000 << "\n" */
   /*     << "View:" << "\t" << (detId%10000000)/1000000 << "\n" */
   /*     << "Plane:" << "\t" << (detId%1000000)/100000 << "\n" */
   /*     << "Layer:" << "\t" << (detId%100000)/10000 << "\n" */
   /*     << "Straw:" << "\t" << detId%100 << std::endl; */
   return detId;
}

TEST_CASE("Detector ID conversion", "[drifttubes]")
{
   // T4
   REQUIRE(DetectorIdTest(1072) == 30112001);
   REQUIRE(DetectorIdTest(1108) == 30002001);
   REQUIRE(DetectorIdTest(1119) == 30002012);
   REQUIRE(DetectorIdTest(1071) == 30002013);
   REQUIRE(DetectorIdTest(1055) == 30012017);
   REQUIRE(DetectorIdTest(1054) == 30012018);
   REQUIRE(DetectorIdTest(1053) == 30012019);
   REQUIRE(DetectorIdTest(1032) == 30112016);
   REQUIRE(DetectorIdTest(1024) == 30112024);
   REQUIRE(DetectorIdTest(895) == 30002025);
   REQUIRE(DetectorIdTest(884) == 30002036);
   REQUIRE(DetectorIdTest(883) == 30012025);
   REQUIRE(DetectorIdTest(872) == 30012036);
   REQUIRE(DetectorIdTest(871) == 30102025);
   REQUIRE(DetectorIdTest(864) == 30102032);
   REQUIRE(DetectorIdTest(863) == 30102033);
   REQUIRE(DetectorIdTest(860) == 30102036);
   REQUIRE(DetectorIdTest(848) == 30112036);
   REQUIRE(DetectorIdTest(847) == 30002037);
   REQUIRE(DetectorIdTest(800) == 30112048);
   // T3
   REQUIRE(DetectorIdTest(799) == 40002001);
   REQUIRE(DetectorIdTest(776) == 40012012);
   REQUIRE(DetectorIdTest(631) == 40102001);
   REQUIRE(DetectorIdTest(600) == 40002020);
   REQUIRE(DetectorIdTest(547) == 40012025);
   REQUIRE(DetectorIdTest(383) == 40002037);
   REQUIRE(DetectorIdTest(336) == 40112048);
   // T2
   REQUIRE(DetectorIdTest(335) == 21112012);
   REQUIRE(DetectorIdTest(304) == 21002001);
   REQUIRE(DetectorIdTest(288) == 21012005);
   REQUIRE(DetectorIdTest(264) == 20102001);
   REQUIRE(DetectorIdTest(119) == 20012012);
   REQUIRE(DetectorIdTest(96) == 20002001);
   // T1
   REQUIRE(DetectorIdTest(95) == 11002001);
   REQUIRE(DetectorIdTest(94) == 11002002);
   REQUIRE(DetectorIdTest(83) == 11012001);
   REQUIRE(DetectorIdTest(71) == 11102001);
   REQUIRE(DetectorIdTest(59) == 11112001);
   REQUIRE(DetectorIdTest(48) == 11112012);
   REQUIRE(DetectorIdTest(2) == 10112010);
   REQUIRE(DetectorIdTest(1) == 10112011);
   REQUIRE(DetectorIdTest(0) == 10112012);
   for ( auto &&i : ROOT::MakeSeq(5) ){
      for ( auto &&j : ROOT::MakeSeq(128) ){
	 uint16_t channel = i*256+j;
	 if(channel != 1032) {
	    std::cout << channel << std::endl;
	    REQUIRE(DetectorIdTest(channel)!=30112016);
	 }
      }
   }
}
TEST_CASE("Detector ID conversion (trigger)", "[trigger]")
{
   REQUIRE(DetectorIdTest(126) == 0);
   REQUIRE(DetectorIdTest(256) == 0);
   REQUIRE(DetectorIdTest(638) == 0);
   REQUIRE(DetectorIdTest(768) == 0);
   REQUIRE(DetectorIdTest(1120) == 0);
}
TEST_CASE("Detector ID conversion (master trigger)", "[master trigger]")
{
   REQUIRE(DetectorIdTest(1123) == 1);
}
TEST_CASE("Detector ID conversion (scintillator)", "[scint]")
{
   REQUIRE(DetectorIdTest(127) == 6);
   REQUIRE(DetectorIdTest(257) == 6);
   REQUIRE(DetectorIdTest(639) == 7);
   REQUIRE(DetectorIdTest(769) == 7);
}
TEST_CASE("Detector ID conversion (beam counter)", "[beamcounter]")
{
   REQUIRE(DetectorIdTest(1136) == -1);
   REQUIRE(DetectorIdTest(1137) == -1);
   REQUIRE(DetectorIdTest(1138) == -1);
   REQUIRE(DetectorIdTest(1139) == -1);
}
TEST_CASE("Detector ID conversion (RC signal)", "[RC_signal]")
{
   REQUIRE(DetectorIdTest(1121) == -1);
   REQUIRE(DetectorIdTest(1122) == -1);
}
