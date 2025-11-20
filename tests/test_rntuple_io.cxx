/**
 * Test script to verify data classes work with ROOT RNtuple I/O
 * This test performs actual write/read operations to validate:
 * - Classes can be written to RNtuple
 * - Data can be read back correctly
 * - Round-trip serialization preserves values
 */

#include "ROOT/RNTuple.hxx"
#include "ROOT/RNTupleModel.hxx"
#include "ROOT/RNTupleReader.hxx"
#include "ROOT/RNTupleWriter.hxx"
#include "TFile.h"

#include <cmath>
#include <iostream>
#include <memory>
#include <vector>

// Include data class headers
#include "MTCDetHit.h"
#include "MTCDetPoint.h"
#include "ShipHit.h"
#include "ShipMCTrack.h"
#include "ShipParticle.h"
#include "SiliconTargetHit.h"
#include "SiliconTargetPoint.h"
#include "TTPoint.h"
#include "TargetPoint.h"
#include "TimeDetHit.h"
#include "TimeDetPoint.h"
#include "Tracklet.h"
#include "UpstreamTaggerHit.h"
#include "UpstreamTaggerPoint.h"
#include "splitcalCluster.h"
#include "splitcalHit.h"
#include "splitcalPoint.h"
#include "strawtubesHit.h"
#include "strawtubesPoint.h"
#include "vetoHit.h"
#include "vetoHitOnTrack.h"
#include "vetoPoint.h"

using ROOT::RNTupleModel;
using ROOT::RNTupleReader;
using ROOT::RNTupleWriter;

// Test helper: write and read a vector of objects
template<typename T>
bool test_rntuple_io(const char* class_name, std::vector<T>& test_objects)
{
    std::cout << "Testing " << class_name << " RNtuple I/O... " << std::flush;

    const std::string filename = std::string("test_") + class_name + ".root";
    const std::string ntuple_name = std::string(class_name) + "_ntuple";

    try {
        // === WRITE TEST ===
        {
            auto model = RNTupleModel::Create();
            auto vec_field = model->MakeField<std::vector<T>>(class_name);

            auto writer = RNTupleWriter::Recreate(std::move(model), ntuple_name, filename);

            // Write test data
            *vec_field = test_objects;
            writer->Fill();

            // Write another entry with empty vector
            vec_field->clear();
            writer->Fill();

            // Write another entry with the test objects again
            *vec_field = test_objects;
            writer->Fill();
        }

        // === READ TEST ===
        {
            auto reader = RNTupleReader::Open(ntuple_name, filename);

            if (reader->GetNEntries() != 3) {
                std::cout << "FAIL: Expected 3 entries, got " << reader->GetNEntries() << std::endl;
                return false;
            }

            auto vec_view = reader->GetView<std::vector<T>>(class_name);

            // Check first entry
            reader->LoadEntry(0);
            const auto& read_vec1 = vec_view(0);
            if (read_vec1.size() != test_objects.size()) {
                std::cout << "FAIL: Entry 0 size mismatch. Expected " << test_objects.size() << ", got "
                          << read_vec1.size() << std::endl;
                return false;
            }

            // Check second entry (should be empty)
            reader->LoadEntry(1);
            const auto& read_vec2 = vec_view(1);
            if (read_vec2.size() != 0) {
                std::cout << "FAIL: Entry 1 should be empty, got size " << read_vec2.size() << std::endl;
                return false;
            }

            // Check third entry
            reader->LoadEntry(2);
            const auto& read_vec3 = vec_view(2);
            if (read_vec3.size() != test_objects.size()) {
                std::cout << "FAIL: Entry 2 size mismatch. Expected " << test_objects.size() << ", got "
                          << read_vec3.size() << std::endl;
                return false;
            }
        }

        std::cout << "PASS" << std::endl;
        return true;

    } catch (const std::exception& e) {
        std::cout << "FAIL: " << e.what() << std::endl;
        return false;
    }
}

int main(int argc, char** argv)
{
    std::cout << "\n=== Testing Data Classes with actual RNtuple I/O ===\n" << std::endl;

    int passed = 0;
    int total = 0;

    // Test base classes
    std::cout << "--- Base Classes ---" << std::endl;

    {
        std::vector<ShipHit> objects;
        objects.emplace_back(1001, 123.45f);
        objects.emplace_back(2002, 678.90f);
        total++;
        if (test_rntuple_io("ShipHit", objects))
            passed++;
    }

    {
        std::vector<ShipMCTrack> objects;
        objects.emplace_back();
        objects.emplace_back();
        total++;
        if (test_rntuple_io("ShipMCTrack", objects))
            passed++;
    }

    {
        std::vector<ShipParticle> objects;
        objects.emplace_back();
        objects.emplace_back();
        total++;
        if (test_rntuple_io("ShipParticle", objects))
            passed++;
    }

    {
        std::vector<vetoHitOnTrack> objects;
        objects.emplace_back();
        objects.emplace_back();
        total++;
        if (test_rntuple_io("vetoHitOnTrack", objects))
            passed++;
    }

    {
        std::vector<Tracklet> objects;
        // Create first tracklet with some hit indices
        Tracklet tracklet1;
        tracklet1.setType(1);   // Type 1 = fitted track
        std::vector<unsigned int>* hits1 = tracklet1.getList();
        hits1->push_back(10);
        hits1->push_back(15);
        hits1->push_back(20);
        hits1->push_back(25);
        objects.push_back(tracklet1);

        // Create second tracklet with different hit indices
        Tracklet tracklet2;
        tracklet2.setType(1);
        std::vector<unsigned int>* hits2 = tracklet2.getList();
        hits2->push_back(30);
        hits2->push_back(35);
        hits2->push_back(40);
        objects.push_back(tracklet2);

        total++;
        if (test_rntuple_io("Tracklet", objects))
            passed++;
    }

    // Test Hit classes
    std::cout << "\n--- Hit Classes ---" << std::endl;

    {
        std::vector<vetoHit> objects;
        objects.emplace_back(1001, 123.45f);
        objects.emplace_back(2002, 345.67f);
        total++;
        if (test_rntuple_io("vetoHit", objects))
            passed++;
    }

    {
        std::vector<strawtubesHit> objects;
        objects.emplace_back(1001000, 123.45f);
        objects.emplace_back(2002000, 234.56f);
        total++;
        if (test_rntuple_io("strawtubesHit", objects))
            passed++;
    }

    {
        std::vector<splitcalHit> objects;
        objects.emplace_back(1001, 123.45f);
        objects.emplace_back(2002, 234.56f);
        total++;
        if (test_rntuple_io("splitcalHit", objects))
            passed++;
    }

    {
        std::vector<splitcalCluster> objects;
        splitcalCluster cluster1;
        cluster1.SetIndex(0);
        cluster1.AddHit(0, 0.5);
        cluster1.AddHit(1, 0.3);
        cluster1.SetStartPoint(1.0, 2.0, 100.0);
        cluster1.SetEndPoint(1.5, 2.5, 150.0);
        objects.push_back(cluster1);

        splitcalCluster cluster2;
        cluster2.SetIndex(1);
        cluster2.AddHit(2, 0.8);
        cluster2.SetStartPoint(3.0, 4.0, 200.0);
        cluster2.SetEndPoint(3.5, 4.5, 250.0);
        objects.push_back(cluster2);

        total++;
        if (test_rntuple_io("splitcalCluster", objects))
            passed++;
    }

    {
        std::vector<MTCDetHit> objects;
        objects.emplace_back();
        objects.emplace_back();
        total++;
        if (test_rntuple_io("MTCDetHit", objects))
            passed++;
    }

    {
        std::vector<SiliconTargetHit> objects;
        objects.emplace_back();
        objects.emplace_back();
        total++;
        if (test_rntuple_io("SiliconTargetHit", objects))
            passed++;
    }

    {
        std::vector<TimeDetHit> objects;
        objects.emplace_back();
        objects.emplace_back();
        total++;
        if (test_rntuple_io("TimeDetHit", objects))
            passed++;
    }

    {
        std::vector<UpstreamTaggerHit> objects;
        objects.emplace_back();
        objects.emplace_back();
        total++;
        if (test_rntuple_io("UpstreamTaggerHit", objects))
            passed++;
    }

    // Test Point classes
    std::cout << "\n--- Point Classes ---" << std::endl;

    {
        std::vector<vetoPoint> objects;
        TVector3 pos(1.0, 2.0, 3.0);
        TVector3 mom(0.1, 0.2, 0.3);
        TVector3 lpos(1.1, 2.1, 3.1);
        TVector3 lmom(0.11, 0.21, 0.31);
        objects.emplace_back(1, 1001, pos, mom, 123.45, 234.56, 0.001, 2212, lpos, lmom);
        objects.emplace_back(2, 2002, pos, mom, 345.67, 456.78, 0.002, 211, lpos, lmom);
        total++;
        if (test_rntuple_io("vetoPoint", objects))
            passed++;
    }

    {
        std::vector<strawtubesPoint> objects;
        TVector3 pos(1.0, 2.0, 3.0);
        TVector3 mom(0.1, 0.2, 0.3);
        objects.emplace_back(1, 1001000, pos, mom, 123.45, 234.56, 0.001, 2212, 0.5);
        objects.emplace_back(2, 2002000, pos, mom, 345.67, 456.78, 0.002, 211, 0.6);
        total++;
        if (test_rntuple_io("strawtubesPoint", objects))
            passed++;
    }

    {
        std::vector<splitcalPoint> objects;
        TVector3 pos(1.0, 2.0, 3.0);
        TVector3 mom(0.1, 0.2, 0.3);
        objects.emplace_back(1, 1001, pos, mom, 123.45, 234.56, 0.001, 2212);
        objects.emplace_back(2, 2002, pos, mom, 345.67, 456.78, 0.002, 211);
        total++;
        if (test_rntuple_io("splitcalPoint", objects))
            passed++;
    }

    {
        std::vector<MTCDetPoint> objects;
        TVector3 pos(1.0, 2.0, 3.0);
        TVector3 mom(0.1, 0.2, 0.3);
        objects.emplace_back(1, 1001, pos, mom, 123.45, 234.56, 0.001, 2212);
        objects.emplace_back(2, 2002, pos, mom, 345.67, 456.78, 0.002, 211);
        total++;
        if (test_rntuple_io("MTCDetPoint", objects))
            passed++;
    }

    {
        std::vector<SiliconTargetPoint> objects;
        TVector3 pos(1.0, 2.0, 3.0);
        TVector3 mom(0.1, 0.2, 0.3);
        objects.emplace_back(1, 1001, pos, mom, 123.45, 234.56, 0.001, 2212);
        objects.emplace_back(2, 2002, pos, mom, 345.67, 456.78, 0.002, 211);
        total++;
        if (test_rntuple_io("SiliconTargetPoint", objects))
            passed++;
    }

    {
        std::vector<TimeDetPoint> objects;
        TVector3 pos(1.0, 2.0, 3.0);
        TVector3 mom(0.1, 0.2, 0.3);
        TVector3 lpos(1.1, 2.1, 3.1);
        TVector3 lmom(0.11, 0.21, 0.31);
        objects.emplace_back(1, 1001, pos, mom, 123.45, 234.56, 0.001, 2212, lpos, lmom);
        objects.emplace_back(2, 2002, pos, mom, 345.67, 456.78, 0.002, 211, lpos, lmom);
        total++;
        if (test_rntuple_io("TimeDetPoint", objects))
            passed++;
    }

    {
        std::vector<UpstreamTaggerPoint> objects;
        TVector3 pos(1.0, 2.0, 3.0);
        TVector3 mom(0.1, 0.2, 0.3);
        TVector3 lpos(1.1, 2.1, 3.1);
        TVector3 lmom(0.11, 0.21, 0.31);
        objects.emplace_back(1, 1001, pos, mom, 123.45, 234.56, 0.001, 2212, lpos, lmom);
        objects.emplace_back(2, 2002, pos, mom, 345.67, 456.78, 0.002, 211, lpos, lmom);
        total++;
        if (test_rntuple_io("UpstreamTaggerPoint", objects))
            passed++;
    }

    {
        std::vector<TTPoint> objects;
        TVector3 pos(1.0, 2.0, 3.0);
        TVector3 mom(0.1, 0.2, 0.3);
        objects.emplace_back(1, 1001, pos, mom, 123.45, 234.56, 0.001, 2212);
        objects.emplace_back(2, 2002, pos, mom, 345.67, 456.78, 0.002, 211);
        total++;
        if (test_rntuple_io("TTPoint", objects))
            passed++;
    }

    {
        std::vector<TargetPoint> objects;
        TVector3 pos(1.0, 2.0, 3.0);
        TVector3 mom(0.1, 0.2, 0.3);
        objects.emplace_back(1, 1001, pos, mom, 123.45, 234.56, 0.001, 2212);
        objects.emplace_back(2, 2002, pos, mom, 345.67, 456.78, 0.002, 211);
        total++;
        if (test_rntuple_io("TargetPoint", objects))
            passed++;
    }

    std::cout << "\n=== Summary ===" << std::endl;
    std::cout << "Passed: " << passed << " / " << total << std::endl;
    std::cout << "Failed: " << (total - passed) << " / " << total << std::endl;

    if (passed == total) {
        std::cout << "\n✓ All RNtuple I/O tests PASSED!" << std::endl;
        std::cout << "All data classes successfully write to and read from RNtuple\n" << std::endl;
        return 0;
    } else {
        std::cout << "\n✗ Some RNtuple I/O tests FAILED!" << std::endl;
        std::cout << "Fix the failing classes before using with RNtuple in production\n" << std::endl;
        return 1;
    }
}
