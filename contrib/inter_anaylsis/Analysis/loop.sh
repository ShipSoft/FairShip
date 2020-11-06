#!/bin/bash

python3 plotHisto.py -o inter-MC-ComparisonChi2mu_P.pdf --plottype P -l
python3 plotHisto.py -o inter-MC-ComparisonChi2mu_linP.pdf --plottype P --xmax 120
python3 plotHisto.py -o inter-MC-ComparisonChi2mu_Pt.pdf --plottype Pt -l
python3 plotHisto.py -o inter-MC-ComparisonChi2mu_linPt.pdf --plottype Pt --xmax 2
python3 plotHisto.py -o inter-MC-ComparisonPt_1.pdf --plottype PtSlice --ymin 5 --ymax 10
python3 plotHisto.py -o inter-MC-ComparisonPt_2.pdf --plottype PtSlice --ymin 10 --ymax 25
python3 plotHisto.py -o inter-MC-ComparisonPt_3.pdf --plottype PtSlice --ymin 25 --ymax 50
python3 plotHisto.py -o inter-MC-ComparisonPt_4.pdf --plottype PtSlice --ymin 50 --ymax 75
python3 plotHisto.py -o inter-MC-ComparisonPt_5.pdf --plottype PtSlice --ymin 75 --ymax 100
python3 plotHisto.py -o inter-MC-ComparisonPt_6.pdf --plottype PtSlice --ymin 100 --ymax 125
python3 plotHisto.py -o inter-MC-ComparisonPt_7.pdf --plottype PtSlice --ymin 125 --ymax 150 --xrebin 2
python3 plotHisto.py -o inter-MC-ComparisonPt_8.pdf --plottype PtSlice --ymin 150 --ymax 200 --xrebin 2
python3 plotHisto.py -o inter-MC-ComparisonPt_9.pdf --plottype PtSlice --ymin 200 --ymax 250 --xrebin 4
python3 plotHisto.py -o inter-MC-ComparisonPt_10.pdf --plottype PtSlice --ymin 250 --ymax 300 --xrebin 4
python3 plotHisto.py -o inter-MC-ComparisonChi2Ratios2Dppt.pdf --plottype PtPratio
python3 plotHisto.py -o inter-MC-ComparisonChi2DatapPt.pdf --plottype PtP -l
