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
    REQUIRE(DetectorIdTest(1055) == 30002001);
    REQUIRE(DetectorIdTest(1054) == 30002002);
    REQUIRE(DetectorIdTest(1053) == 30002003);
    REQUIRE(DetectorIdTest(1032) == 30012012);
    REQUIRE(DetectorIdTest(621) == 30102011);
    REQUIRE(DetectorIdTest(600) == 30002020);
    REQUIRE(DetectorIdTest(547) == 30012025);
    REQUIRE(DetectorIdTest(383) == 30002037);
    REQUIRE(DetectorIdTest(336) == 30112048);
    REQUIRE(DetectorIdTest(335) == 21112012);
    REQUIRE(DetectorIdTest(264) == 20102001);
    REQUIRE(DetectorIdTest(119) == 20012012);
    REQUIRE(DetectorIdTest(96) == 20002001);
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
    REQUIRE(DetectorIdTest(1024) == 0);
}
TEST_CASE("Detector ID conversion (scintillator)", "[scint]") {
    REQUIRE(DetectorIdTest(127) == 6);
    REQUIRE(DetectorIdTest(257) == 6);
    REQUIRE(DetectorIdTest(639) == 7);
    REQUIRE(DetectorIdTest(1025) == 7);
}
TEST_CASE("Detector ID conversion (beam counter)", "[beamcounter]") {
    REQUIRE(DetectorIdTest(1136) == -1);
    REQUIRE(DetectorIdTest(1137) == -1);
    REQUIRE(DetectorIdTest(1138) == -1);
    REQUIRE(DetectorIdTest(1139) == -1);
}
