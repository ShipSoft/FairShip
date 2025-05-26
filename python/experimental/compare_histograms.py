"""Compare histogreams for exact or statistical equality."""

import argparse

import uproot
from scipy import stats

def compare_histograms(hist1, hist2, use_ks_test=False, significance_threshold=0.05):
    """
    Compare two histograms for equality or statistical compatibility.

    Parameters:
    hist1 (hist.Hist): The first histogram to compare.
    hist2 (hist.Hist): The second histogram to compare.
    use_ks_test (bool): If True, perform the Kolmogorov-Smirnov test for statistical comparison.
    significance_threshold (float): The significance threshold for the KS test.

    Returns:
    bool: True if the histograms are equal or statistically compatible, False otherwise.
    """
    # Check if the histograms are equal
    if not hist1 == hist2:
        print(
            f"Histograms '{hist1.name}' are different in terms of bin contents or errors."
        )

        if use_ks_test:
            # Perform the Kolmogorov-Smirnov test
            ks_statistic, p_value = stats.ks_2samp(hist1.values(), hist2.values())
            print(f"KS Statistic: {ks_statistic}, p-value: {p_value}")
            if p_value.all() < significance_threshold:
                print(
                    f"Histograms '{hist1.name}' are statistically different (p < {significance_threshold})."
                )
            else:
                print(
                    f"Histograms '{hist1.name}' are statistically compatible (p >= {significance_threshold})."
                )
        return False

    print(f"Histograms '{hist1.name}' are equal.")
    return True


def main(file1_path, file2_path, use_ks_test, significance_threshold):
    """
    Compare histograms in two ROOT files.

    Parameters:
    file1_path (str): Path to the first ROOT file.
    file2_path (str): Path to the second ROOT file.
    use_ks_test (bool): If True, perform the Kolmogorov-Smirnov test for statistical comparison.
    significance_threshold (float): The significance threshold for the KS test.
    """
    files = {
        1 : uproot.open(file1_path),
        2 : uproot.open(file2_path)
        }

    # Get the list of histogram names from the first file
    
    def isuproothist(inkey, fileno):
        isHist = False
        try:
            isHist = isinstance(files[fileno][inkey], uproot.behaviors.TH1.Histogram)
        except uproot.deserialization.DeserializationError:
            isHist = False
        return isHist

    histograms1 = {
        key: files[1][key]
        for key in files[1].keys()
        if isuproothist(key, 1)
    }
    histograms2 = {
        key: files[2][key]
        for key in files[2].keys()
        if isuproothist(key, 2)
    }

    # Compare histograms with the same names
    for hist_name in histograms1.keys():
        if hist_name in histograms2:
            hist1 = histograms1[hist_name].to_hist()
            hist2 = histograms2[hist_name].to_hist()
            compare_histograms(hist1, hist2, use_ks_test, significance_threshold)
        else:
            print(f"Histogram '{hist_name}' not found in file2.")

    # Check for histograms in file2 that are not in file1
    for hist_name in histograms2.keys():
        if hist_name not in histograms1:
            print(f"Histogram '{hist_name}' not found in file1.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Compare histograms in two ROOT files."
    )
    parser.add_argument("file1", help="Path to the first ROOT file.")
    parser.add_argument("file2", help="Path to the second ROOT file.")
    parser.add_argument(
        "--ks",
        action="store_true",
        help="Use Kolmogorov-Smirnov test for statistical comparison.",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.05,
        help="Significance threshold for the KS test (default: 0.05).",
    )

    args = parser.parse_args()

    main(args.file1, args.file2, args.ks, args.threshold)
