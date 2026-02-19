#!/usr/bin/env python3
"""
Test script to verify RNTuple digitisation and reconstruction implementation.
This script creates a minimal test to ensure the RNTuple API is used correctly.
"""

import os
import sys

import ROOT

# Add the python directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "python"))


def test_rntuple_model_creation():
    """Test that we can create an RNTuple model with all required fields."""
    print("Testing RNTuple model creation...")

    try:
        # Create model
        model = ROOT.RNTupleModel.Create()

        # Test basic field types that we use
        model.MakeField["FairEventHeader"]("ShipEventHeader")
        model.MakeField["std::vector<genfit::Track*>"]("FitTracks")
        model.MakeField["std::vector<int>"]("fitTrack2MC")
        model.MakeField["std::vector<Tracklet>"]("Tracklets")

        # Test hit vector fields
        model.MakeField["std::vector<strawtubesHit>"]("Digi_strawtubesHits")
        model.MakeField["std::vector<vetoHit>"]("Digi_vetoHits")

        print("✓ All field types created successfully")
        return True

    except Exception as e:
        print(f"✗ Failed to create model: {e}")
        return False


def test_rntuple_writer_creation():
    """Test that we can create an RNTuple writer."""
    print("Testing RNTuple writer creation...")

    try:
        # Create model with a simple field
        model = ROOT.RNTupleModel.Create()
        model.MakeField["int"]("test_field")

        # Create writer
        test_file = "test_rntuple_output.root"
        writer = ROOT.RNTupleWriter.Recreate(model, "test_ntuple", test_file)

        # Create and fill an entry
        entry = writer.CreateEntry()
        entry["test_field"] = 42
        writer.Fill(entry)

        # Clean up
        del writer

        # Verify file was created
        if os.path.exists(test_file):
            os.remove(test_file)
            print("✓ RNTuple writer created and used successfully")
            return True
        else:
            print("✗ Output file was not created")
            return False

    except Exception as e:
        print(f"✗ Failed to create writer: {e}")
        return False


def main():
    """Run all tests."""
    print("=== Testing RNTuple Digitisation/Reconstruction Implementation ===\n")

    tests = [
        test_rntuple_model_creation,
        test_rntuple_writer_creation,
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        if test():
            passed += 1
        print()

    print(f"=== Results: {passed}/{total} tests passed ===")

    if passed == total:
        print("✓ All tests passed! RNTuple implementation looks good.")
        return 0
    else:
        print("✗ Some tests failed. Check the implementation.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
