#define CATCH_CONFIG_MAIN
#include "/usr/include/catch/catch.hpp"
#include "../online/ShipOnlineDataFormat.h"

using namespace DriftTubes;

int DetectorIdTest(uint16_t channel){
    ChannelId* test = reinterpret_cast<ChannelId*>(&channel);
    int detId = test->GetDetectorId();
    /* std::cout << "Stat:" << "\t" << detId/10000000 << "\n" */
    /*     << "View:" << "\t" << (detId%10000000)/1000000 << "\n" */
    /*     << "Plane:" << "\t" << (detId%1000000)/100000 << "\n" */
    /*     << "Layer:" << "\t" << (detId%100000)/10000 << "\n" */
    /*     << "Straw:" << "\t" << detId%100 << std::endl; */
    return detId;
}

TEST_CASE("Detector ID conversion", "[drifttubes]") {
    // T4
    REQUIRE(DetectorIdTest(1072) == 40112001);
    REQUIRE(DetectorIdTest(1108) == 40002001);
    REQUIRE(DetectorIdTest(1119) == 40002012);
    REQUIRE(DetectorIdTest(1071) == 40002013);
    REQUIRE(DetectorIdTest(1055) == 40012017);
    REQUIRE(DetectorIdTest(1054) == 40012018);
    REQUIRE(DetectorIdTest(1053) == 40012019);
    REQUIRE(DetectorIdTest(1032) == 40112016);
    REQUIRE(DetectorIdTest(1024) == 40112024);
    REQUIRE(DetectorIdTest(895) == 40002025);
    REQUIRE(DetectorIdTest(884) == 40002036);
    REQUIRE(DetectorIdTest(883) == 40012025);
    REQUIRE(DetectorIdTest(872) == 40012036);
    REQUIRE(DetectorIdTest(871) == 40102025);
    REQUIRE(DetectorIdTest(864) == 40102032);
    REQUIRE(DetectorIdTest(863) == 40102033);
    REQUIRE(DetectorIdTest(860) == 40102036);
    REQUIRE(DetectorIdTest(848) == 40112036);
    REQUIRE(DetectorIdTest(847) == 40002037);
    REQUIRE(DetectorIdTest(800) == 40112048);
    // T3
    REQUIRE(DetectorIdTest(799) == 30002001);
    REQUIRE(DetectorIdTest(776) == 30012012);
    REQUIRE(DetectorIdTest(631) == 30102001);
    REQUIRE(DetectorIdTest(600) == 30002020);
    REQUIRE(DetectorIdTest(547) == 30012025);
    REQUIRE(DetectorIdTest(383) == 30002037);
    REQUIRE(DetectorIdTest(336) == 30112048);
    // T2
    REQUIRE(DetectorIdTest(335) == 21112012);
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
}
TEST_CASE("Detector ID conversion (trigger)", "[trigger]") {
    REQUIRE(DetectorIdTest(126) == 0);
    REQUIRE(DetectorIdTest(256) == 0);
    REQUIRE(DetectorIdTest(638) == 0);
    REQUIRE(DetectorIdTest(768) == 0);
    REQUIRE(DetectorIdTest(1120) == 0);
}
TEST_CASE("Detector ID conversion (scintillator)", "[scint]") {
    REQUIRE(DetectorIdTest(127) == 6);
    REQUIRE(DetectorIdTest(257) == 6);
    REQUIRE(DetectorIdTest(639) == 7);
    REQUIRE(DetectorIdTest(769) == 7);
}
TEST_CASE("Detector ID conversion (beam counter)", "[beamcounter]") {
    REQUIRE(DetectorIdTest(1136) == -1);
    REQUIRE(DetectorIdTest(1137) == -1);
    REQUIRE(DetectorIdTest(1138) == -1);
    REQUIRE(DetectorIdTest(1139) == -1);
}
TEST_CASE("Detector ID conversion (RC signal)", "[RC_signal]") {
    REQUIRE(DetectorIdTest(1121) == -1);
    REQUIRE(DetectorIdTest(1122) == -1);
}
