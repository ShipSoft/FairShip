
! Code converted using TO_F90 by Alan Miller
! Date: 2012-03-16  Time: 11:06:00

!> \file
!! Millepede II program, subroutines.
!!
!! \author Volker Blobel, University Hamburg, 2005-2009 (initial Fortran77 version)
!! \author Gero Flucke, University Hamburg (support of C-type binary files)
!! \author Claus Kleinwort, DESY (maintenance and developement)
!!
!! \copyright
!! Copyright (c) 2009 - 2018 Deutsches Elektronen-Synchroton,
!! Member of the Helmholtz Association, (DESY), HAMBURG, GERMANY \n\n
!! This library is free software; you can redistribute it and/or modify
!! it under the terms of the GNU Library General Public License as
!! published by the Free Software Foundation; either version 2 of the
!! License, or (at your option) any later version. \n\n
!! This library is distributed in the hope that it will be useful,
!! but WITHOUT ANY WARRANTY; without even the implied warranty of
!! MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
!! GNU Library General Public License for more details. \n\n
!! You should have received a copy of the GNU Library General Public
!! License along with this program (see the file COPYING.LIB for more
!! details); if not, write to the Free Software Foundation, Inc.,
!! 675 Mass Ave, Cambridge, MA 02139, USA.
!!

!> \mainpage Overview
!!
!! \section intro_sec Introduction
!! In certain least squares fit problems with a very large number of parameters
!! the set of parameters can be divided into two classes, global and local parameters.
!! Local parameters are those parameters which are present only in subsets of the
!! data. Detector alignment and calibration based on track fits is one of the problems,
!! where the interest is only in optimal values of the global parameters, the
!! alignment parameters. The method, called Millepede, to solve the linear least
!! squares problem with a simultaneous fit of all global and local parameters,
!! irrespectively of the number of local parameters, is described in the draft manual.
!!
!! The Millepede method and the initial implementation has been
!! developed by [V. Blobel](http://www.desy.de/~blobel) from he University of Hamburg.
!! Meanwhile the code is maintained at DESY by the statistics tools group of the
!! analysis center of the Helmholtz Terascale alliance
!! ([www.terascale.de](https://www.wiki.terascale.de/index.php/Millepede_II)).
!!
!! The Millepede II software is provided by DESY under the terms of the
!! [LGPLv2 license](http://www.gnu.org/licenses/old-licenses/lgpl-2.0-standalone.html).
!!
!! \section install_sec Installation
!! To install **Millepede** (on a linux system):
!! 1. Download the software package from the DESY \c svn server to
!!    \a target directory, e.g.:
!!
!!         svn checkout http://svnsrv.desy.de/public/MillepedeII/tags/V04-04-01 target
!!
!! 2. Create **Pede** executable (in \a target directory):
!!
!!         make pede
!!
!! 3. Optionally check the installation by running the simple test case:
!!
!!         ./pede -t
!!
!!    This will create (and use) the necessary text and binary files.
!!
!! \section news_sec News
!! * 131008: New solution method \ref ch-minresqlp "MINRES-QLP"
!! [\ref ref_sec "ref 9"] implemented.
!! * 140226: Reading of C binary files containing *doubles* implemented.
!! * 141020: Storage of values read from text files as *doubles* implemented.
!! * 141125: Dynamic entries (from accepted local fits) check implemented.
!!   (Rejection of local fits may lead to the loss of degrees of freedom.)
!!   Printout of global parameter counters with new command \ref cmd-printcounts.
!! * 141126: Weighted constraints implemented (with new command \ref cmd-weightedcons).
!! * 150210: Solution by elimination for problems with linear equality constraints
!!   has been implemented (as default, new command \ref cmd-withelim) in addition to the
!!   Lagrange multiplier method (new command \ref cmd-withmult).
!! * 150218: Skipping *empty* constraints (without variable parameters).
!!   With new command \ref cmd-checkinput detailed check of input data (binary files,
!!   constraints) is performed, but no solution will be determined.
!!   Some input statistics is available in the output file <tt>millepede.res</tt>.
!! * 150226: Iteration of entries cut with new command \ref cmd-iterateentries.
!!   In the second iteration measurements with any parameters fixed by the 
!!   previous entries cut are skipped. Useful if parameters of measurements have
!!   different number of entries. 
!! * 150420: Skipping of empty constraints has to be enabled by new command \ref
!!   cmd-skipemptycons.
!! * 150901: Preconditioning for MINRES with skyline matrix (avoiding rank deficits 
!!   of band matrix) added (selected by second argument in \ref cmd-bandwidth >0).
!! * 150925: Monitoring of residuals per local fit cycle is selected by \ref cmd-monres.
!!   The normalized residuals are grouped by the first global label and the median 
!!   and the RMS (from the median of the absolute deviations) per group are
!!   written to <tt>millepede.mon</tt>.
!! * 170502: Monitoring of pulls per local fit cycle is selected by \ref cmd-monpull.
!!   The scaling of measurement errors is enabled by \ref cmd-scaleerrors.
!!   Pede will abort now for constraints with a singular QL decomposition
!!   of the constraints matrix (solution by elemination).
!!   This problem is usually caused by *empty* constraints (see \ref
!!   cmd-skipemptycons).
!! * 170831: More debug information for problems with reading Cfiles. Don't stop
!!   after read error for \ref cmd-checkinput mode.
!! * 180525: Some fixes: Proper handling of special (debug) data blocks in binary
!!   files, proper exit code (3) for 'function not decreasing'.
!! * 180815: Some minor fixes, additional level of detail (appearance range of global
!!   parameters in binary files) for \ref cmd-checkinput mode.
!! * 190319: Constraints are now sorted and split into disjoint blocks to speed up
!!   calculation of rank and QL decomposition by block matrix algebra.
!!   This works best if the label sets of the involved alignable objects are disjoint too.
!! * 190412: Cleanup of operations (open, close, rewind) on binary files. New command
!!   \ref cmd-closeandreopen to to enable closing and reopening of binary files
!!   to limit the number of concurrently open files. The modification dates of the
!!   files are monitored to ensure data integrity.
!!
!! \section tools_sec Tools
!! The subdirectory \c tools contains some useful scripts:
!! * \c readMilleBinary.py: Python script to read binary files and print
!!   records in text form.
!! * \c readPedeHists.C: ROOT script to read and convert the **Millepede**
!!   histogram file <tt>millepede.his</tt>.
!!
!! \section details_sec Details
!!
!! Detailed information is available at:
!!
!! \subpage draftman_page
!!
!! \subpage changes_page
!!
!! \subpage option_page
!!
!! \subpage exit_code_page
!!
!! \section Contact
!!
!! For information exchange the **Millepede** mailing list
!! anacentre-millepede2@desy.de should be used.
!!
!! \section ref_sec References
!!
!! 1. A New Method for the High-Precision Alignment of Track Detectors,
!!    Volker Blobel and Claus Kleinwort, Proceedings of the Conference on
!!    Adcanced Statistical Techniques in Particle Physics, Durham, 18 - 22 March 2002,
!!    Report DESY 02-077 (June 2002) and
!!    [hep-ex/0208021](http://arxiv.org/abs/hep-ex/0208021)
!! 2.  Alignment Algorithms, V. Blobel,
!!    [Proceedings](http://cdsweb.cern.ch/search?p=reportnumber%3ACERN-2007-004)
!!    of the LHC Detector Alignment Workshop, September 4 - 6 2006, CERN
!! 3. Software alignment for Tracking Detectors, V. Blobel,
!!    NIM A, 566 (2006), pp. 5-13,
!!    [doi:10.1016/j.nima.2006.05.157](http://dx.doi.org/10.1016/j.nima.2006.05.157)
!! 4. A new fast track-fit algorithm based on broken lines, V. Blobel,
!!    NIM A, 566 (2006), pp. 14-17,
!!    [doi:10.1016/j.nima.2006.05.156](http://dx.doi.org/10.1016/j.nima.2006.05.156)
!! 5. Millepede 2009, V. Blobel, [Contribution]
!!    (https://indico.cern.ch/conferenceOtherViews.py?view=standard&confId=50502)
!!    to the 3rd LHC Detector Alignment Workshop, June 15 - 16 2009, CERN
!! 6. General Broken Lines as advanced track fitting method, C. Kleinwort,
!!    NIM A, 673 (2012), pp. 107-110,
!!    [doi:10.1016/j.nima.2012.01.024](http://dx.doi.org/10.1016/j.nima.2012.01.024)
!! 7. Volker Blobel und Erich Lohrmann, Statistische und numerische Methoden der
!!    Datenanalyse, Teubner Studienb&uuml;cher, B.G. Teubner, Stuttgart, 1998.
!!    [Online-Ausgabe](http://www.desy.de/~blobel/eBuch.pdf).
!! 8. [Systems Optimization Laboratory](http://web.stanford.edu/group/SOL/software/minres),
!!    Stanford University;\n
!!    C. C. Paige and M. A. Saunders (1975),
!!    Solution of sparse indefinite systems of linear equations,
!!    SIAM J. Numer. Anal. 12(4), pp. 617-629.
!! 9. [Systems Optimization Laboratory](http://web.stanford.edu/group/SOL/software/minresqlp),
!!    Stanford University;\n
!!    Sou-Cheng Choi, Christopher Paige, and Michael Saunders,
!!    MINRES-QLP: A Krylov subspace method for indefinite or singular
!!    symmetric systems, SIAM Journal of Scientific Computing 33:4, 1810-1836, 2011,
!!    [doi:10.1137/100787921](http://dx.doi.org/10.1137/100787921)
!!

!> \page changes_page Major changes
!! Major changes with respect to the \ref draftman_page "draft manual".
!! \tableofcontents
!!
!! \section ch-methods Solution methods
!! The following methods to obtain the solution \f$\Vek{x}\f$ from a
!! linear equation system \f$\Vek{A}\cdot\Vek{x}=\Vek{b}\f$ are implemented:
!! \subsection ch-inv Inversion
!! The solution and the covariance matrix \f$\Vek{A}^{-1}\f$ are obtained by
!! \ref an-inv "inversion" of \f$\Vek{A}\f$.
!! Available are the value, error and global correlation for all global parameters.
!! The matrix inversion \ref sqminl "routine" has been \ref ch-openmp "parallelized"
!! and can be used for up to several 10000 parameters.
!! \subsection ch-diag Diagonalization
!! The solution and the covariance matrix \f$\Vek{A}^{-1}\f$ are obtained by
!! \ref an-diag "diagonalization" of \f$\Vek{A}\f$.
!! Available are the value, error, global correlation and
!! eigenvalue (and eigenvector) for all global parameters.
!! \subsection ch-minres Minimal Residual Method (MINRES)
!! The solution is obtained by minimizing \f$\Vert\Vek{A}\cdot\Vek{x}-\Vek{b}\Vert_2\f$
!! iteratively. \ref minresmodule::minres "MINRES"  [\ref ref_sec "ref 8"] is a special case of the
!! generalized minimal residual method (\ref an-gmres "GMRES") for symmetric matrices.
!! Preconditioning with a band matrix of zero or finite
!! \ref mpmod::mbandw "bandwidth" is possible.
!! Individual columns \f$\Vek{c_i}\f$ of the covariance matrix can be calculated by
!! solving \f$\Vek{A}\cdot\Vek{c}_i=\Vek{1}_i\f$ where \f$\Vek{1}_i\f$ is the i-th
!! column on the unit matrix.
!! The most time consuming part (\ref avprod "product" matrix times vector per iteration)
!! has been \ref ch-openmp "parallelized".
!! Available are the value for all (and optionally error, global correlation
!! for few) global parameters.
!! \subsection ch-minresqlp Advanced Minimal Residual Method (MINRES-QLP)
!! The \ref minresqlpmodule::minresqlp "MINRES-QLP" implementation [\ref ref_sec "ref 9"]
!! is a MINRES evolution with improved norm estimates and stopping conditions
!! (leading potentially to different numbers of internal iterations).
!! Internally it uses QLP instead of the QR factorization in
!! MINRES which should be numerically superior and allows to find for
!! singular systems the minimal length (pseudo-inverse) solution.
!!
!! The default behavior is to start (the internal iterations) with QR factorization
!! and to switch to QLP if the (estimated) matrix condition exceeds
!! \ref cmd-mrestranscond "mrtcnd". Pure QR or QLP factorization can be enforced
!! by \ref cmd-mresmode "mrmode".
!!
!! \subsection ch-elim-const Elimination of constraints
!! As alternative to the Lagrange multiplier method the solution by elimination
!! has been added for problems with linear equality constraints.
!! A \ref mpqldec::qldec "QL factorization" (with Householder reflections) of the
!! transposed constraints matrix is used to transform to an unconstrained problem.
!! For sparse matrix storage the sparsity of the global matrix is preserved.
!!
!! \section ch-regul Regularization
!! Optionally a term \f$\tau\cdot\Vert\Vek{x}\Vert\f$ can be added to the objective function
!! (to be minimized) where \f$\Vek{x}\f$ is the vector of global parameters
!! weighted with the inverse of their individual pre-sigma values.
!!
!! \section ch-locfit Local fit
!! In case the \ref par-locfitv "local fit" is a track fit with proper description of multiple
!! scattering in the detector material additional local parameters have to be introduced
!! for each scatterer and solution by *inversion* can get time consuming
!! (~ \f$n_{lp}^3\f$ for \f$n_{lp}\f$ local parameters). For trajectories based on
!! **broken lines** [\ref ref_sec "ref 4,6"] the corresponding matrix \f$\Vek{\Gamma}\f$
!! has a bordered band structure (\f$\Gamma_{ij}=0\f$ for \f$\min(i,j)>b\f$
!! (border size) and \f$|i-j|>m\f$ (bandwidth)). With
!! <i>root-free Cholesky decomposition</i> the time for the solution is linear
!! and for the calculation of \f$\Gamma^{-1}\f$
!! (needed for the construction of the global matrix) quadratic in \f$n_{lp}\f$.
!! For each local fit the structure of \f$\Vek{\Gamma}\f$ is checked and the faster
!! solution method selected automatically.
!!
!! \section ch-openmp Parallelization
!! The code has been largely parallelized using [OpenMP&tm;](www.openmp.org).
!! This includes the reading of binary files, the local fits, the construction of the
!! sparsity structure and filling of the global matrix and the global fit
!! (except by diagonalization). The number of threads is set by the command
!! \ref cmd-threads.
!!
!! \b Caching. The records are read in blocks into a *read cache* and processed from
!! there in parallel, each record by a single thread. For the filling of the global
!! matrix the (zero-compressed) update matrices (\f$\Vek{\D C}_1+\Vek{\D C}_2\f$ from
!! equations \ref eq-c1 "(15)", \ref eq-c2 "(16)")
!! produced by each local fit are collected in a
!! *write cache*. After processing the block of records this is used to update
!! the global matrix in parallel, each row by a single thread.
!! The total cache size can be changed by the command \ref cmd-cache.
!!
!! \section ch-compression Compressed sparse matrix
!! In sparse storage mode for each row the list of column indices (and values) for the
!! non-zero elements are stored. With compression regions of continous column indices
!! are represented by the first index and their number (packed into a single 32bit
!! integer). Compression is selected by the command \ref cmd-compress.
!! In addition rare elements can be neglected (,histogrammed) or stored in single instead
!! of double precision according to the \ref cmd-pairentries command.
!!
!! \section ch-gzip Gzipped C binary files
!! The [zlib](zlib.net) can be used to directly read *gzipped* C binary files.
!! In this case reading with multiple threads
!! (each file by single thread) can speed up the decompression.
!!
!! \section ch-transf Transformation from FORTRAN77 to Fortran90
!! The **Millepede** source code has been formally transformed from <i>fixed form</i>
!! FORTRAN77 to <i>free form</i> Fortran90 (using TO_F90 by Alan Miller)
!! and (most parts) modernized:
!! - <tt>IMPLICIT NONE</tt> everywhere. Unused variables removed.
!! - \c COMMON blocks replaced by \c MODULEs.
!! - Backward \c GOTOs replaced by proper \c DO loops.
!! - \c INTENT (input/output) of arguments described.
!! - Code documented with doxygen.
!!
!! Unused parts of the code (like the interactive mode) have been removed.
!! The reference compiler for the Fortran90 version is gcc-4.6.2 (gcc-4.4.4 works too).
!!
!! \section ch-memmanage Memory management
!! The memory management for dynamic data structures (matrices, vectors, ..)
!! has been changed from a \ref an-dynal "subdivided" *static* \c COMMON block to
!! *dynamic* (\c ALLOCATABLE) Fortran90 arrays. One **Pede** executable is now
!! sufficient for all application sizes.
!!
!! \section ch-readbuf Read buffer size
!! In the \ref sssec-loop1 "first loop" over all binary files a preset
!! \ref mpmod::ndimbuf "read buffer size" is used. Too large records are skipped,
!! but the maximal record length is still being updated. If any records had to be skipped
!! the read buffer size is afterwards adjusted according to the maximal record length
!! and the first loop is repeated.
!!
!! \section ch-numbin Number of binary files
!! The number of binary files has no hard-coded limit anymore, but is calculated from
!! the steering file and resources (file names, descriptors, ..)
!! are allocated dynamically. Some resources may be limited by the system.
!!

!> \page option_page List of options and commands
!!
!! \tableofcontents
!!
!! \section sec-opt Command line options:
!! \subsection opt-t1 -t
!! Create text and binary files for \ref mptest1.f90 "wire chamber" test case, set
!! \ref mpmod::ictest "ictest" to 1.
!! \subsection opt-t2 -t=track-model
!! Create text and binary files for \ref mptest2.f90 "silicon strip tracker" test case
!! using \a track-models with different accounting for multiple scattering, set
!! \ref mpmod::ictest "ictest" to 2..6.
!! \subsection opt-s -s
!! Solution is not iterated.
!! Automatically switched on in case of rank deficits for constraints.
!! \subsection opt-f -f
!! Force iterating of solution (in case of rank deficits for constraints).
!! \subsection opt-c -c
!! Check input (binary files, constraints). No solution is determined. (\ref mpmod::icheck "icheck"=1)
!! \subsection opt-C -C
!! Check input (binary files, constraints, appearance). No solution is determined. (\ref mpmod::icheck "icheck"=2)
!!
!! \section sec-cmd Steering file commands:
!! In general the commands are defined by a single line:
!!
!!         keyword   number1  number2  ...
!!
!! For those specifying \ref sssec-parinf "properties" of the global parameters
!! (\a keyword = \c parameter, \c constraint or \c measurement)
!! for each involved global parameter (identified by a \ref an-glolab "label")
!! one additional line follows:
!!
!!         label     number1  number2  ...
!!
!! Default values for the numerical arguments are shown in
!! the command descriptions in '[]'. Missing arguments without default
!! values have no effect.
!!
!! \subsection cmd-bandwidth bandwidth
!! Set band width \ref mpmod::mbandw "mbandw" for
!! \ref minresmodule::minres "MINRES" preconditioner to \a number1 [0]
!! and additional flag \ref mpmod::lprecm "lprecm" to \a number2 [0].
!! \subsection cmd-cache cache
!! Set (read+write) cache size \ref mpmod::ncache "ncache" to \a number1.
!! Define cache size and average fill level.
!! \subsection cmd-cfiles Cfiles
!! Following binaries are C files.
!! \subsection cmd-checkinput checkinput
!! Set check input flag \ref mpmod::icheck "icheck" to \a number1 [1].
!! Similar to \ref opt-c "-c" or \ref opt-C "-C".
!! For mpmod::icheck "icheck" >0 no solution is performed but input statistics is checked in detail.
!! With mpmod::icheck "icheck" >1 the appearance range (first/last file,record and number of files)
!! of global parameters is determined too.
!! \subsection cmd-chisqcut chisqcut
!! For local fit \ref an-chisq "setChi^2" cut \ref mpmod::chicut "chicut" to \a number1 [1.],
!! \ref mpmod::chirem "chirem" to \a number2 [1.].
!! \subsection cmd-compress compress
!! Set compression flag \ref mpmod::mcmprs "mcmprs" for \ref mpbits.f90 "sparse storage"
!! to 1 (true) (and \ref mpmod::msngpe "msngpe" to 1).
!! \subsection cmd-closeandreopen closeandreopen
!! Set flag \ref mpmod::keepopen "keepOpen" to zero to enable closing and reopening of binary files
!! to limit the number of concurrently open files.
!! \subsection cmd-constraint constraint
!! Define \ref sssec_consinf "constraints" for global parameters.
!! \subsection cmd-debug debug
!! Set number of records with debug printout \ref mpmod::mdebug "mdebug" to
!! \a number1 [3], number of measurements with printout \ref mpmod::mdebg2 "mdebg2" to \a number2.
!! \subsection cmd-dwfractioncut dwfractioncut
!! Set \ref an-dwcut "down-weighting fraction" cut \ref mpmod::dwcut "dwcut"
!! to \a number1 (max. 0.5).
!! \subsection cmd-entries entries
!! Set \ref an-entries "entries" cuts for variable global parameter
!! \ref mpmod::mreqenf "mreqenf" to \a number1 [25],
!! \ref mpmod::mreqena "mreqena" to \a number2 [10] and
!! \ref mpmod::iteren "iteren" to the product of \a number1 and \a number3 [0].
!! \subsection cmd-errlabels errlabels
!! Define (up to 100 in total) global labels \a number1 .. \a numberN
!! for which the parameter errors are calculated for method MINRES too
!! (by \ref solglo "solving" \f$\Vek{C}\cdot\Vek{x}_i = \Vek{b}^i, b^i_j = \delta_{ij} \f$).
!! \subsection cmd-force force
!! Set force (iterations) flag \ref mpmod::iforce "iforce" to 1 (true).
!! Same as \ref opt-f "-f".
!! \subsection cmd-fortranfiles fortranfiles
!! Following binaries are Fortran files.
!! \subsection cmd-globalcorr globalcorr
!! Set flag \ref mpmod::igcorr "igcorr" for output of global correlations to 1 (true).
!! \subsection cmd-histprint histprint
!! Set flag \ref mpmod::nhistp "nhistp" for \ref an-histpr "histogram printout"
!! to 1 (true).
!! \subsection cmd-hugecut hugecut
!! For local fit set Chi^2 cut \ref mpmod::chhuge "chhuge"
!! for \ref sssec-outlierdeb "unreasonable data" to \a number1 [1.].
!! \subsection cmd-iterateentries iterateentries
!! Set maximum value \ref mpmod::iteren "iteren" for iteration of entries cut to
!! \a number1 [maxint]. Can alternatively be set by the \ref cmd-entries command.
!! For parameters with less entries the cut will be iterated ignoring measurements with
!! at least one parameter below \ref mpmod::mreqenf "mreqenf".
!! \subsection cmd-linesearch linesearch
!! The mode \ref mpmod::lsearch "lsearch" of the \ref par-linesearch "line search"
!! to improve the solution is set to \a number1.
!! \subsection cmd-localfit localfit
!! For local fit set number of iterations \ref mpmod::lfitnp "lfitnp"
!! with calculation of pulls to \a number1, flag \ref mpmod::lfitbb "lfitbb"
!! for auto-detection of bordered band matrices to \a number2.
!! \subsection cmd-matiter matiter
!! Set number of iterations \ref mpmod::matrit "matrit" with (re)calcuation of
!! global matrix to \a number1.
!! \subsection cmd-matmoni matmoni
!! Set record interval \ref mpmod::matmon "matmon" for monitoring of (sparse) matrix
!! construction to \a number1.
!! \subsection cmd-maxrecord maxrecord
!! Set record limit \ref mpmod::mxrec "mxrec" to \a number1.
!! \subsection cmd-measurement measurement
!! Define (additional) \ref sssec_gpm "measurements" for global parameters.
!! \subsection cmd-memorydebug memorydebug
!! Set debug flag \ref mpmod::memdbg "memdbg" for memory management
!! to \a number1 [1].
!! \subsection cmd-method method
!! Has special format:
!!
!!         method   name     number1  number2
!!
!! Set \ref ch-methods "solution method" \ref mpmod::metsol "metsol" and
!! storage mode \ref mpmod::matsto "matsto" according to \a name,
!! (\c inversion : (1,1), \c diagonalization : (2,1),
!! \c fullMINRES : (3,1) or \c sparseMINRES : (3,2),
!! \c fullMINRES-QLP : (4,1) or \c sparseMINRES-QLP : (4,2)),
!! (minimum) number of iterations \ref mpmod::mitera "mitera" to \a number1,
!! convergence limit \ref mpmod::dflim "dflim" to \a number2.
!! \subsection cmd-monres monitorresiduals
!! Set flag \ref mpmod::imonit "imonit" for monitoring of residuals to \a number1 [3]
!! and increase number of bins (of size 0.1) for internal storage to \a number2 [100].
!! Monitoring mode \ref mpmod::imonmd "imonmd" is 0.
!! \subsection cmd-monpull monitorpulls
!! Set flag \ref mpmod::imonit "imonit" for monitoring of pulls to \a number1 [3]
!! and increase number of bins (of size 0.1) for internal storage to \a number2 [100].
!! Monitoring mode \ref mpmod::imonmd "imonmd" is 1.
!! \subsection cmd-mresmode mresmode
!! Set \ref minresqlpmodule::minresqlp "MINRES-QLP" factorization mode
!!  \ref mpmod::mrmode "mrmode" to \a number1.
!! \subsection cmd-mrestranscond mrestranscond
!! Set \ref minresqlpmodule::minresqlp "MINRES-QLP" transition (matrix) condition
!!  \ref mpmod::mrtcnd "mrtcnd" to \a number1.
!! \subsection cmd-mrestol mrestol
!! Set tolerance criterion \ref mpmod::mrestl "mrestl" for \ref minresmodule::minres "MINRES"
!! to \a number1 (\f$10^{-10}\f$ .. \f$10^{-4}\f$).
!! \subsection cmd-nofeasiblestart nofeasiblestart
!! Set flag \ref mpmod::nofeas "nofeas" for \ref an-nofeas "skipping"
!! making parameters feasible to \a number1 [1].
!! \subsection cmd-outlierdownweighting outlierdownweighting
!! For local fit set number of \ref sssec-outlow "outlier"
!! \ref an-downw "down-weighting" iterations
!! \ref mpmod::lhuber "lhuber" to \a number1.
!! \subsection cmd-pairentries pairentries
!! Set entries cut for variable global parameter pairs \ref mpmod::mreqpe "mreqpe"
!! to \a number1, histogram upper bound \ref mpmod::mhispe "mhispe" for pairs
!! to \a number2 (<1: no histogramming), upper bound \ref mpmod::msngpe "msngpe"
!! for pair entries with single precision storage
!! to \a number3.
!! \subsection cmd-parameter parameter
!! Define \ref sssec-parinf "initial value, pre-sigma" for global parameters.
!! \subsection cmd-presigma presigma
!! Set default pre-sigma \ref mpmod::regpre "regpre" to \a number1 [1].
!! \subsection cmd-print print
!! Set print level \ref mpmod::mprint "mprint" to \a number1 [1].
!! \subsection cmd-printcounts printcounts
!! Set flag \ref mpmod::ipcntr "ipcntr" to \a number1 [1].
!! The counters for the global parameters from the accepted local fits (=1)
!! or from the binary files (>1) will be printed in the result file.
!! \subsection cmd-printrecord printrecord
!! \ref an-recpri "Record" numbers with printout.
!! \subsection cmd-pullrange pullrange
!! Set (symmetric) range \ref mpmod::prange "prange" for histograms
!! of pulls, normalized residuals to \a number1 (=0: auto-ranging).
!! \subsection cmd-regularisation regularisation
!! Set flag \ref mpmod::nregul "nregul" for regularization to 1 (true),
!! regularization parameter \ref mpmod::regula "regula" to \a number2,
!! default pre-sigma \ref mpmod::regpre "regpre" to \a number3.
!! \subsection cmd-regularization regularization
!! Set flag \ref mpmod::nregul "nregul" for regularization to 1 (true),
!! regularization parameter \ref mpmod::regula "regula" to \a number2,
!! default pre-sigma \ref mpmod::regpre "regpre" to \a number3.
!! \subsection cmd-scaleerrors scaleerrors
!! Set measurement scaling factors \ref mpmod::dscerr "dscerr"
!! to \a number1 [1.] and \a number2 [\a number1].
!! First value is for "global" measurements (with global derivatives),
!! second for "local" measurements (without global derivatives).
!! \subsection cmd-skipemptycons skipemptycons
!! Set flag \ref mpmod::iskpec "iskpec" to 1 (true).
!! Empty constraints (without variable parameters) will be skipped.
!! \subsection cmd-subito subito
!! Set subito (no iterations) flag \ref mpmod::isubit "isubit" to 1 (true).
!! Same as \ref opt-s "-s".
!! \subsection cmd-threads threads
!! Set number \ref mpmod::mthrd "mthrd" of OpenMP&tm; threads for processing
!! to \a number1,
!! number \ref mpmod::mthrdr "mthrdr" of threads for reading
!! binary files to \a number2 [\a number1].
!! \subsection cmd-weightedcons weightedcons
!! Set flag \ref mpmod::iwcons "iwcons" to \a number1 [1].
!! Implements \ref sssec_consinf "weighted constraints" for global parameters.
!! \subsection cmd-withelim withelimination
!! Set flag \ref mpmod::icelim "icelim" to 1 (true).
!! Selects solution by elimination for linear equality constraints.
!! \subsection cmd-withmult withmultipliers
!! Set flag \ref mpmod::icelim "icelim" to 0 (false).
!! Selects solution by Lagrange multipliers for linear equality constraints.
!! \subsection cmd-wolfe wolfe
!! For strong Wolfe condition in \ref par-linesearch "line search"
!! set parameter \ref mpmod::wolfc1 "wolfc1" to \a number1, \ref mpmod::wolfc2
!! "wolfc2" to \a number2.

!> \page exit_code_page List of exit codes
!! The exit code and message of the **Pede** executable can be found in the
!! file <tt>millepede.end</tt> :
!!    + <b>-1</b>   Still running or crashed
!!    + **00**   Ended normally
!!    + **01**   Ended with warnings (bad measurements)
!!    + **02**   Ended with severe warnings (insufficient measurements)
!!    + **03**   Ended with severe warnings (bad global matrix)
!!    + **10**   Aborted, no steering file
!!    + **11**   Aborted, open error for steering file
!!    + **12**   Aborted, second text file in command line
!!    + **13**   Aborted, unknown keywords in steering file
!!    + **14**   Aborted, no binary files
!!    + **15**   Aborted, open error(s) for binary files
!!    + **16**   Aborted, open error(s) for text files
!!    + **17**   Aborted, file name too long
!!    + **18**   Aborted, read error(s) for binary files
!!    + **19**   Aborted, binary file(s) modified
!!    + **20**   Aborted, bad binary records
!!    + **21**   Aborted, no labels/parameters defined
!!    + **22**   Aborted, no variable global parameters
!!    + **23**   Aborted, bad matrix index
!!    + **24**   Aborted, vector/matrix size mismatch
!!    + **25**   Aborted, result vector contains NaNs
!!    + **26**   Aborted, too many rejects
!!    + **27**   Aborted, singular QL decomposition of constraints matrix
!!    + **30**   Aborted, memory allocation failed
!!    + **31**   Aborted, memory deallocation failed
!!    + **32**   Aborted, iteration limit reached in diagonalization
!!    + **33**   Aborted, stack overflow in quicksort
!!    + **34**   Aborted, pattern string too long

!> Millepede II main program \ref sssec-stalone "Pede".
PROGRAM mptwo
    USE mpmod
    USE mpdalc
    USE mptest1, ONLY: nplan,del,dvd
    USE mptest2, ONLY: nlyr,nmx,nmy,sdevx,sdevy

    IMPLICIT NONE
    REAL(mps) :: andf
    REAL(mps) :: c2ndf
    REAL(mps) :: deltat
    REAL(mps) :: diff
    REAL(mps) :: err
    REAL(mps) :: gbu
    REAL(mps) :: gmati
    REAL(mps) :: rej
    REAL :: rloop1
    REAL :: rloop2
    REAL :: rstext
    REAL(mps) :: secnd
    REAL :: rst
    REAL :: rstp
    REAL, DIMENSION(2) :: ta
    INTEGER(mpi) :: i
    INTEGER(mpi) :: ii
    INTEGER(mpi) :: ix
    INTEGER(mpi) :: ixv
    INTEGER(mpi) :: iy
    INTEGER(mpi) :: k
    INTEGER(mpi) :: kfl
    INTEGER(mpi) :: lun
    INTEGER :: minut
    INTEGER :: nhour
    INTEGER(mpi) :: nmxy
    INTEGER(mpi) :: nrc
    INTEGER(mpi) :: nsecnd
    INTEGER(mpi) :: ntot
    INTEGER(mpi) :: ntsec

    CHARACTER (LEN=24) :: chdate
    CHARACTER (LEN=24) :: chost

    INTEGER(mpl) :: rows
    INTEGER(mpl) :: cols

    REAL(mpd) :: sums(9)
    !$    INTEGER(mpi) :: OMP_GET_NUM_PROCS,OMP_GET_MAX_THREADS
    !$    INTEGER(mpi) :: MXTHRD
    !$    INTEGER(mpi) :: NPROC

    SAVE
    !     ...
    CALL etime(ta,rstp)
    CALL fdate(chdate)

    !     millepede monitoring file
    lunmon=0
    !     millepede.log file
    lunlog=8
    lvllog=1
    CALL mvopen(lunlog,'millepede.log')
    CALL getenv('HOSTNAME',chost)
    IF (chost(1:1) == ' ') CALL getenv('HOST',chost)
    WRITE(*,*) '($Rev: 169 $)'
    !$    WRITE(*,*) 'using OpenMP (TM)'
#ifdef __GFORTRAN__
    WRITE(*,111)  __GNUC__ , __GNUC_MINOR__ , __GNUC_PATCHLEVEL__
111 FORMAT(' compiled with gcc ',i0,'.',i0,'.',i0)
#endif
    WRITE(*,*) ' '
    WRITE(*,*) '  <  Millepede II-P starting ... ',chdate
    WRITE(*,*) '                                 ',chost
    WRITE(*,*) ' '

    WRITE(8,*) ' '
    WRITE(8,*) 'Log-file Millepede II-P                        ', chdate
    WRITE(8,*) '                                               ', chost
    CALL peend(-1,'Still running or crashed')
    !     read command line and text files

    CALL filetc   ! command line and steering file analysis
    CALL filetx   ! read text files
    IF (icheck > 0) THEN
        WRITE(*,*) '!!!   Checking input only, no calculation of a solution   !!!'
        WRITE(8,*) '!!!   Checking input only, no calculation of a solution   !!!'
    END IF
    lvllog=mprint ! export print level
    IF (memdbg > 0) printflagalloc=1 ! debug memory management
    !$    WRITE(*,*)
    !$    NPROC=1
    !$    MXTHRD=1
    !$    NPROC=OMP_GET_NUM_PROCS()         ! number of processors available
    !$    CALL OMP_SET_NUM_THREADS(MTHRD)   ! set max number of threads to MTHRD
    !$    MXTHRD=OMP_GET_MAX_THREADS()      ! get max number of threads back
    !$    WRITE(*,*) 'Number of processors available:   ', NPROC
    !$    WRITE(*,*) 'Maximum number of OpenMP threads: ', MXTHRD
    !$    WRITE(*,*) 'Number of threads for processing: ', MTHRD
    !$    IF (MXREC.GT.0) MTHRDR=1          ! to get allways the same MXREC records
    !$    IF (ICHECK.GT.1) MTHRDR=1         ! to get allways the same order of records
    !$    WRITE(*,*) 'Number of threads for reading:    ', MTHRDR
    !$POMP INST INIT                        ! start profiling with ompP
    IF (ncache < 0) THEN
        ncache=25000000*mthrd  ! default cache size (100 MB per thread)
    ENDIF
    rows=6; cols=mthrdr
    CALL mpalloc(readBufferInfo,rows,cols,'read buffer header')
    !     histogram file
    lun=7
    CALL mvopen(lun,'millepede.his')
    CALL hmplun(lun) ! unit for histograms
    CALL gmplun(lun) ! unit for xy data

    !     debugging
    IF(nrecpr /= 0.OR.nrecp2 /= 0) THEN
        CALL mvopen(1,'mpdebug.txt')
    END IF

    CALL etime(ta,rstext)
    times(0)=rstext-rstp ! time for text processing

    !     preparation of data sub-arrays

    CALL loop1
    CALL etime(ta,rloop1)
    times(1)=rloop1-rstext ! time for LOOP1

    CALL loop2
    IF(chicut /= 0.0) THEN
        WRITE(8,*) 'Chi square cut equiv 3 st.dev applied ...'
        WRITE(8,*) ' in  first iteration with factor',chicut
        WRITE(8,*) ' in second iteration with factor',chirem
        WRITE(8,*) ' (reduced by sqrt in next iterations)'
    END IF
    
    IF(lhuber /= 0) THEN
        WRITE(8,*) 'Down-weighting of outliers in', lhuber,' iterations'
        WRITE(8,*) 'Cut on downweight fraction',dwcut
    END IF

    CALL etime(ta,rloop2)
    times(2)=rloop2-rloop1 ! time for LOOP2

    IF(icheck > 0) THEN
        CALL prtstat
        CALL peend(0,'Ended normally')
        GOTO 99 ! only checking input
    END IF

    !     use different solution methods

    CALL mstart('Iteration')   ! Solution module starting

    CALL xloopn                ! all methods

    !     ------------------------------------------------------------------

    IF(nloopn > 2.AND.nhistp /= 0) THEN       ! last iteration
        CALL hmprnt(3)  ! scaled residual of single measurement (with global deriv.)
        CALL hmprnt(12) ! scaled residual of single measurement (no global deriv.)
        CALL hmprnt(4)  ! chi^2/Ndf
    END IF
    IF(nloopn > 2) THEN
        CALL hmpwrt(3)
        CALL hmpwrt(12)
        CALL hmpwrt(4)
        CALL gmpwrt(4) ! location, dispersion (res.) as a function of record nr
        IF (nloopn <= lfitnp) THEN
            CALL hmpwrt(13)
            CALL hmpwrt(14)
            CALL gmpwrt(5)
        END IF
    END IF
    IF(nhistp /= 0) THEN
        CALL gmprnt(1)
        CALL gmprnt(2)
    END IF
    CALL gmpwrt(1)             ! output of xy data
    CALL gmpwrt(2)             ! output of xy data
    !     'track quality' per binary file
    IF (nfilb > 1) THEN
        CALL gmpdef(6,1,'log10(#records) vs file number')
        CALL gmpdef(7,1,'final rejection fraction vs file number')
        CALL gmpdef(8,1,  &
            'final <Chi^2/Ndf> from accepted local fits vs file number')
        CALL gmpdef(9,1, '<Ndf> from accepted local fits vs file number')
  
        DO i=1,nfilb
            kfl=kfd(2,i)
            nrc=-kfd(1,i)
            IF (nrc > 0) THEN
                rej=REAL(nrc-jfd(kfl),mps)/REAL(nrc,mps)
                CALL gmpxy(6,REAL(kfl,mps),LOG10(REAL(nrc,mps))) ! log10(#records) vs file
                CALL gmpxy(7,REAL(kfl,mps),rej)    ! rejection fraction vs file
            END IF
            IF (jfd(kfl) > 0) THEN
                c2ndf=cfd(kfl)/REAL(jfd(kfl),mps)
                CALL gmpxy(8,REAL(kfl,mps),c2ndf)  ! <Chi2/NDF> vs file
                andf=REAL(dfd(kfl),mps)/REAL(jfd(kfl),mps)
                CALL gmpxy(9,REAL(kfl,mps),andf)  ! <NDF> vs file
            END IF
        END DO
        IF(nhistp /= 0) THEN
            CALL gmprnt(6)
            CALL gmprnt(7)
            CALL gmprnt(8)
            CALL gmprnt(9)
        END IF
        CALL gmpwrt(6)             ! output of xy data
        CALL gmpwrt(7)             ! output of xy data
        CALL gmpwrt(8)             ! output of xy data
        CALL gmpwrt(9)             ! output of xy data
    END IF

    IF(ictest == 1) THEN
        WRITE(*,*) ' '
        WRITE(*,*) 'Misalignment test wire chamber'
        WRITE(*,*) ' '
  
        CALL hmpdef( 9,-0.0015,+0.0015,'True - fitted displacement')
        CALL hmpdef(10,-0.0015,+0.0015,'True - fitted Vdrift')
        DO i=1,4
            sums(i)=0.0_mpd
        END DO
        DO i=1,nplan
            diff=REAL(-del(i)-globalParameter(i),mps)
            sums(1)=sums(1)+diff
            sums(2)=sums(2)+diff*diff
            diff=REAL(-dvd(i)-globalParameter(100+i),mps)
            sums(3)=sums(3)+diff
            sums(4)=sums(4)+diff*diff
        END DO
        sums(1)=0.01_mpd*sums(1)
        sums(2)=SQRT(0.01_mpd*sums(2))
        sums(3)=0.01_mpd*sums(3)
        sums(4)=SQRT(0.01_mpd*sums(4))
        WRITE(*,143) 'Parameters   1 - 100: mean =',sums(1), 'rms =',sums(2)
        WRITE(*,143) 'Parameters 101 - 200: mean =',sums(3), 'rms =',sums(4)
143     FORMAT(6X,a28,f9.6,3X,a5,f9.6)
        WRITE(*,*) ' '
        WRITE(*,*) ' '
        WRITE(*,*) '    I '
        WRITE(*,*) '   --- '
        DO i=1,100
            WRITE(*,102) i,-del(i),globalParameter(i),-del(i)-globalParameter(i),  &
                -dvd(i),globalParameter(100+i),-dvd(i)-globalParameter(100+i)
            diff=REAL(-del(i)-globalParameter(i),mps)
            CALL hmpent( 9,diff)
            diff=REAL(-dvd(i)-globalParameter(100+i),mps)
            CALL hmpent(10,diff)
        END DO
        IF(nhistp /= 0) THEN
            CALL hmprnt( 9)
            CALL hmprnt(10)
        END IF
        CALL hmpwrt( 9)
        CALL hmpwrt(10)
    END IF
    IF(ictest > 1) THEN
        WRITE(*,*) ' '
        WRITE(*,*) 'Misalignment test Si tracker'
        WRITE(*,*) ' '
  
        CALL hmpdef( 9,-0.0025,+0.0025,'True - fitted displacement X')
        CALL hmpdef(10,-0.025,+0.025,'True - fitted displacement Y')
        DO i=1,9
            sums(i)=0.0_mpd
        END DO
        nmxy=nmx*nmy
        ix=0
        iy=ntot
        DO i=1,nlyr
            DO k=1,nmxy
                ix=ix+1
                diff=REAL(-sdevx((i-1)*nmxy+k)-globalParameter(ix),mps)
                sums(1)=sums(1)+1.0_mpd
                sums(2)=sums(2)+diff
                sums(3)=sums(3)+diff*diff
                ixv=globalParLabelIndex(2,ix)
                IF (ixv > 0.AND.metsol == 1.OR.metsol == 2) THEN
                    ii=(ixv*ixv+ixv)/2
                    gmati=REAL(globalMatD(ii),mps)
                    ERR=SQRT(ABS(gmati))
                    diff=diff/ERR
                    sums(7)=sums(7)+1.0_mpd
                    sums(8)=sums(8)+diff
                    sums(9)=sums(9)+diff*diff
                END IF
            END DO
            IF (MOD(i,3) == 1) THEN
                DO k=1,nmxy
                    iy=iy+1
                    diff=-REAL(sdevy((i-1)*nmxy+k)-globalParameter(iy),mps)
                    sums(4)=sums(4)+1.0_mpd
                    sums(5)=sums(5)+diff
                    sums(6)=sums(6)+diff*diff
                    ixv=globalParLabelIndex(2,iy)
                    IF (ixv > 0.AND.metsol == 1.OR.metsol == 2) THEN
                        ii=(ixv*ixv+ixv)/2
                        gmati=REAL(globalMatD(ii),mps)
                        ERR=SQRT(ABS(gmati))
                        diff=diff/ERR
                        sums(7)=sums(7)+1.0_mpd
                        sums(8)=sums(8)+diff
                        sums(9)=sums(9)+diff*diff
                    END IF
                END DO
            END IF
        END DO
        sums(2)=sums(2)/sums(1)
        sums(3)=SQRT(sums(3)/sums(1))
        sums(5)=sums(5)/sums(4)
        sums(6)=SQRT(sums(6)/sums(4))
        WRITE(*,143) 'Parameters   1 - 500: mean =',sums(2), 'rms =',sums(3)
        WRITE(*,143) 'Parameters 501 - 700: mean =',sums(5), 'rms =',sums(6)
        IF (sums(7) > 0.5_mpd) THEN
            sums(8)=sums(8)/sums(7)
            sums(9)=SQRT(sums(9)/sums(7))
            WRITE(*,143) 'Parameter pulls, all: mean =',sums(8), 'rms =',sums(9)
        END IF
        WRITE(*,*) ' '
        WRITE(*,*) ' '
        WRITE(*,*) '    I '
        WRITE(*,*) '   --- '
        ix=0
        iy=ntot
        DO i=1,nlyr
            DO k=1,nmxy
                ix=ix+1
                diff=REAL(-sdevx((i-1)*nmxy+k)-globalParameter(ix),mps)
                CALL hmpent( 9,diff)
                WRITE(*,102) ix,-sdevx((i-1)*nmxy+k),globalParameter(ix),-diff
            END DO
        END DO
        DO i=1,nlyr
            IF (MOD(i,3) == 1) THEN
                DO k=1,nmxy
                    iy=iy+1
                    diff=REAL(-sdevy((i-1)*nmxy+k)-globalParameter(iy),mps)
                    CALL hmpent(10,diff)
                    WRITE(*,102) iy,-sdevy((i-1)*nmxy+k),globalParameter(iy),-diff
                END DO
            END IF
        END DO
        IF(nhistp /= 0) THEN
            CALL hmprnt( 9)
            CALL hmprnt(10)
        END IF
        CALL hmpwrt( 9)
        CALL hmpwrt(10)
    END IF

    IF(nrec1+nrec2 > 0) THEN
        WRITE(8,*) ' '
        IF(nrec1 > 0) THEN
            WRITE(8,*) 'Record',nrec1,' has largest residual:',value1
        END IF
        IF(nrec2 > 0) THEN
            WRITE(8,*) 'Record',nrec2,' has largest Chi^2/Ndf:',value2
        END IF
    END IF
    IF(nrec3 < huge(nrec3)) THEN
        WRITE(8,*) 'Record',nrec3, ' is first with error (rank deficit/NaN)'
    END IF
99  WRITE(8,*) ' '
    IF (iteren > mreqenf) THEN
        WRITE(8,*) 'In total 3 +',nloopn,' loops through the data files'
    ELSE
        WRITE(8,*) 'In total 2 +',nloopn,' loops through the data files'
    ENDIF   
    IF (mnrsit > 0) THEN
        WRITE(8,*) ' '
        WRITE(8,*) 'In total    ',mnrsit,' internal MINRES iterations'
    END IF

    WRITE(8,103) times(0),times(1),times(2),times(4),times(7),  &
        times(5),times(8),times(3),times(6)

    CALL etime(ta,rst)
    deltat=rst-rstp
    ntsec=nint(deltat,mpi)
    CALL sechms(deltat,nhour,minut,secnd)
    nsecnd=nint(secnd,mpi)  ! round
    WRITE(8,*) 'Total time =',ntsec,' seconds =',nhour,' h',minut,  &
        ' m',nsecnd,' seconds'
    CALL fdate(chdate)
    WRITE(8,*) 'end                                            ', chdate
    gbu=1.0E-9*REAL(maxwordsalloc*(BIT_SIZE(1_mpi)/8),mps)             ! GB used
    WRITE(8,*) ' '
    WRITE(8,105) gbu

    !     Rejects ----------------------------------------------------------

    IF(nrejec(0)+nrejec(1)+nrejec(2)+nrejec(3) /= 0) THEN
        WRITE(8,*) ' '
        WRITE(8,*) 'Data rejected in last iteration:   '
        WRITE(8,*) '   ',  &
            nrejec(0), ' (rank deficit/NaN) ',nrejec(1),' (Ndf=0)   ',  &
            nrejec(2), ' (huge)   ',nrejec(3),' (large)'
        WRITE(8,*) ' '
    END IF
    IF (icheck <= 0) CALL explfc(8)

    WRITE(*,*) ' '
    WRITE(*,*) '  <  Millepede II-P ending   ... ', chdate ! with exit code',ITEXIT,' >'
    WRITE(*,*) ' '
    gbu=1.0E-9*REAL(maxwordsalloc*(BIT_SIZE(1_mpi)/8),mps)             ! GB used
    WRITE(*,105) gbu
    WRITE(*,*) ' '

102 FORMAT(2X,i4,2X,3F10.5,2X,3F10.5)
103 FORMAT(' Times [in sec] for     text processing',f12.3/  &
        '                                  LOOP1',f12.3/  &
        '                                  LOOP2',f12.3/  &
        '   func. value                         ',f12.3,' *',f4.0/  &
        '   func. value, global matrix, solution',f12.3,' *',f4.0/  &
        '                           new solution',f12.3,' *',f4.0/)
105 FORMAT('      Peak dynamic memory allocation: ',f11.6,' GB')
END PROGRAM mptwo                              ! Mille

!> Error for single global parameter from \ref minresmodule::minres "MINRES".
!!
!! Calculate single row 'x_i' from inverse matrix by solving A*x_i=b
!! with b=0 except b_i=1.
!!
!! \param [in]  ivgbi index of variable parameter

SUBROUTINE solglo(ivgbi)
    USE mpmod
    USE minresModule, ONLY: minres

    IMPLICIT NONE
    REAL(mps) :: par
    REAL(mps) :: dpa
    REAL(mps) :: err
    REAL(mps) :: gcor2
    INTEGER(mpi) :: iph
    INTEGER(mpi) :: istop
    INTEGER(mpi) :: itgbi
    INTEGER(mpi) :: itgbl
    INTEGER(mpi) :: itn
    INTEGER(mpi) :: itnlim
    INTEGER(mpi) :: nout

    INTEGER(mpi), INTENT(IN)                      :: ivgbi

    REAL(mpd) :: shift
    REAL(mpd) :: rtol
    REAL(mpd) :: anorm
    REAL(mpd) :: acond
    REAL(mpd) :: arnorm
    REAL(mpd) :: rnorm
    REAL(mpd) :: ynorm
    REAL(mpd) :: gmati
    REAL(mpd) :: diag
    INTEGER(mpl) :: ijadd
    INTEGER(mpl) :: jk
    INTEGER(mpl) :: ii
    LOGICAL :: checka
    EXTERNAL avprod, mcsolv, mvsolv
    SAVE
    DATA iph/0/
    !     ...
    IF(iph == 0) THEN
        iph=1
        WRITE(*,101)
    END IF
    itgbi=globalParVarToTotal(ivgbi)
    itgbl=globalParLabelIndex(1,itgbi)

    globalVector=0.0_mpd ! reset rhs vector IGVEC
    globalVector(ivgbi)=1.0_mpd

    !      NOUT  =6
    nout  =0
    itnlim=200
    shift =0.0_mpd
    rtol  = mrestl ! from steering
    checka=.FALSE.


    IF(mbandw == 0) THEN           ! default preconditioner
        CALL minres(nagb,  avprod, mcsolv, globalVector, shift, checka ,.TRUE. , &
            globalCorrections, itnlim, nout, rtol, istop, itn, anorm, acond, rnorm, arnorm, ynorm)

    ELSE IF(mbandw > 0) THEN       ! band matrix preconditioner
        CALL minres(nagb,  avprod, mvsolv, globalVector, shift, checka ,.TRUE. , &
            globalCorrections, itnlim, nout, rtol, istop, itn, anorm, acond, rnorm, arnorm, ynorm)
    ELSE
        CALL minres(nagb,  avprod, mvsolv, globalVector, shift, checka ,.FALSE. , &
            globalCorrections, itnlim, nout, rtol, istop, itn, anorm, acond, rnorm, arnorm, ynorm)
    END IF

    par=REAL(globalParameter(itgbi),mps)
    dpa=REAL(par-globalParStart(itgbi),mps)
    gmati=globalCorrections(ivgbi)
    ERR=SQRT(ABS(REAL(gmati,mps)))
    IF(gmati < 0.0_mpd) ERR=-ERR
    IF(matsto == 1) THEN ! normal matrix               ! ???
        ii=ivgbi
        jk=(ii*ii+ii)/2
    ELSE IF(matsto == 2) THEN ! sparse matrix
        jk=ijadd(ivgbi,ivgbi)
    END IF
    IF (jk > 0) THEN
        diag=globalMatD(jk)
    ELSE
        diag=REAL(globalMatF(-jk),mpd)
    END IF
    gcor2=REAL(1.0_mpd-1.0_mpd/(gmati*diag),mps) ! global correlation (squared)
    WRITE(*,102) itgbl,par,REAL(globalParPreSigma(itgbi),mps),dpa,ERR,gcor2,itn
101 FORMAT(1X,'    label     parameter    presigma      differ',  &
        '       Error gcor^2   iit'/ 1X,'---------',2X,5('-----------'),2X,'----')
102 FORMAT(i10,2X,4G12.4,f7.4,i6,i4)
END SUBROUTINE solglo

!> Error for single global parameter from \ref minresqlpmodule::minresqlp "MINRES-QLP".
!!
!! Calculate single row 'x_i' from inverse matrix by solving A*x_i=b
!! with b=0 except b_i=1.
!!
!! \param [in]  ivgbi index of variable parameter

SUBROUTINE solgloqlp(ivgbi)
    USE mpmod
    USE minresqlpModule, ONLY: minresqlp

    IMPLICIT NONE
    REAL(mps) :: par
    REAL(mps) :: dpa
    REAL(mps) :: err
    REAL(mps) :: gcor2
    INTEGER(mpi) :: iph
    INTEGER(mpi) :: istop
    INTEGER(mpi) :: itgbi
    INTEGER(mpi) :: itgbl
    INTEGER(mpi) :: itn
    INTEGER(mpi) :: itnlim
    INTEGER(mpi) :: nout

    INTEGER(mpi), INTENT(IN)                      :: ivgbi

    REAL(mpd) :: shift
    REAL(mpd) :: rtol
    REAL(mpd) :: mxxnrm
    REAL(mpd) :: trcond
    REAL(mpd) :: gmati
    REAL(mpd) :: diag
    INTEGER(mpl) :: ijadd
    INTEGER(mpl) :: jk
    INTEGER(mpl) :: ii

    EXTERNAL avprod, mcsolv, mvsolv
    SAVE
    DATA iph/0/
    !     ...
    IF(iph == 0) THEN
        iph=1
        WRITE(*,101)
    END IF
    itgbi=globalParVarToTotal(ivgbi)
    itgbl=globalParLabelIndex(1,itgbi)

    globalVector=0.0_mpd ! reset rhs vector IGVEC
    globalVector(ivgbi)=1.0_mpd

    !      NOUT  =6
    nout  =0
    itnlim=200
    shift =0.0_mpd
    rtol  = mrestl ! from steering
    mxxnrm = REAL(nagb,mpd)/SQRT(epsilon(mxxnrm))
    IF(mrmode == 1) THEN
        trcond = 1.0_mpd/epsilon(trcond) ! only QR
    ELSE IF(mrmode == 2) THEN
        trcond = 1.0_mpd ! only QLP
    ELSE
        trcond = mrtcnd ! QR followed by QLP
    END IF

    IF(mbandw == 0) THEN           ! default preconditioner
        CALL minresqlp( n=nagb, Aprod=avprod, b=globalVector,  Msolve=mcsolv, nout=nout, &
            itnlim=itnlim, rtol=rtol, maxxnorm=mxxnrm, trancond=trcond, &
            x=globalCorrections, istop=istop, itn=itn)
    ELSE IF(mbandw > 0) THEN       ! band matrix preconditioner
        CALL minresqlp( n=nagb, Aprod=avprod, b=globalVector,  Msolve=mvsolv, nout=nout, &
            itnlim=itnlim, rtol=rtol, maxxnorm=mxxnrm, trancond=trcond, &
            x=globalCorrections, istop=istop, itn=itn)
    ELSE
        CALL minresqlp( n=nagb, Aprod=avprod, b=globalVector, nout=nout, &
            itnlim=itnlim, rtol=rtol, maxxnorm=mxxnrm, trancond=trcond, &
            x=globalCorrections, istop=istop, itn=itn)
    END IF

    par=REAL(globalParameter(itgbi),mps)
    dpa=REAL(par-globalParStart(itgbi),mps)
    gmati=globalCorrections(ivgbi)
    ERR=SQRT(ABS(REAL(gmati,mps)))
    IF(gmati < 0.0_mpd) ERR=-ERR
    IF(matsto == 1) THEN ! normal matrix               ! ???
        ii=ivgbi
        jk=(ii*ii+ii)/2
    ELSE IF(matsto == 2) THEN ! sparse matrix
        jk=ijadd(ivgbi,ivgbi)
    END IF
    IF (jk > 0) THEN
        diag=globalMatD(jk)
    ELSE
        diag=REAL(globalMatF(-jk),mpd)
    END IF
    gcor2=REAL(1.0_mpd-1.0_mpd/(gmati*diag),mps) ! global correlation (squared)
    WRITE(*,102) itgbl,par,REAL(globalParPreSigma(itgbi),mps),dpa,ERR,gcor2,itn
101 FORMAT(1X,'    label     parameter    presigma      differ',  &
        '       Error gcor^2   iit'/ 1X,'---------',2X,5('-----------'),2X,'----')
102 FORMAT(i10,2X,4G12.4,f7.4,i6,i4)
END SUBROUTINE solgloqlp

!> Add \ref par-glowithcon "constraint" information to matrix and vector.
SUBROUTINE addcst
    USE mpmod

    IMPLICIT NONE
    REAL(mpd) :: climit
    REAL(mpd) :: factr
    REAL(mpd) :: sgm

    INTEGER(mpi) :: i
    INTEGER(mpi) :: icgb
    INTEGER(mpi) :: irhs
    INTEGER(mpi) :: itgbi
    INTEGER(mpi) :: ivgb
    INTEGER(mpi) :: j
    INTEGER(mpi) :: jcgb
    INTEGER(mpi) :: l
    INTEGER(mpi) :: label
    INTEGER(mpi) :: nop
    INTEGER(mpi) :: inone

    REAL(mpd) :: rhs
    REAL(mpd) :: drhs(4)
    INTEGER(mpi) :: idrh (4)
    SAVE
    !     ...
    nop=0
    IF(lenConstraints == 0) RETURN  ! no constraints
    climit=1.0E-5         ! limit for printout
    irhs=0 ! number of values in DRHS(.), to be printed

    DO jcgb=1,ncgb
        icgb=matConsSort(3,jcgb) ! unsorted constraint index
        i=vecConsStart(icgb)
        rhs=listConstraints(i  )%value ! right hand side
        sgm=listConstraints(i+1)%value ! sigma parameter
        DO j=i+2,vecConsStart(icgb+1)-1
            label=listConstraints(j)%label
            factr=listConstraints(j)%value
            itgbi=inone(label) ! -> ITGBI= index of parameter label
            ivgb =globalParLabelIndex(2,itgbi) ! -> variable-parameter index
  
            IF(icalcm == 1.AND.nagb > nvgb.AND.ivgb > 0) THEN
                CALL mupdat(nvgb+jcgb,ivgb,factr) ! add to matrix
            END IF
  
            rhs=rhs-factr*globalParameter(itgbi)     ! reduce residuum
        END DO
        IF(ABS(rhs) > climit) THEN
            irhs=irhs+1
            idrh(irhs)=jcgb
            drhs(irhs)=rhs
            nop=1
            IF(irhs == 4) THEN
                WRITE(*,101) (idrh(l),drhs(l),l=1,irhs)
                irhs=0
            END IF
        END IF
        vecConsResiduals(jcgb)=rhs
        IF (nagb > nvgb) globalVector(nvgb+jcgb)=rhs
    END DO

    IF(irhs /= 0) THEN
        WRITE(*,101) (idrh(l),drhs(l),l=1,irhs)
    END IF
    IF(nop == 0) RETURN
    WRITE(*,102) ' Constraints: only equation values >', climit,' are printed'
101 FORMAT('            ',4(i4,g11.3))
102 FORMAT(a,g11.2,a)
END SUBROUTINE addcst

!> Prepare constraints.
!!
!! Count, sort constraints and split into disjoint blocks.

SUBROUTINE prpcon
    USE mpmod
    USE mpdalc

    IMPLICIT NONE
    INTEGER(mpi) :: i
    INTEGER(mpi) :: icgb
    INTEGER(mpi) :: isblck
    INTEGER(mpi) :: ilast
    INTEGER(mpi) :: itgbi
    INTEGER(mpi) :: ivgb
    INTEGER(mpi) :: jcgb
    INTEGER(mpi) :: label
    INTEGER(mpi) :: labelf
    INTEGER(mpi) :: labell
    INTEGER(mpi) :: ncon
    INTEGER(mpi) :: npar
    INTEGER(mpi) :: nconmx
    INTEGER(mpi) :: nparmx
    INTEGER(mpi) :: inone
    INTEGER(mpi) :: itype
    INTEGER(mpi) :: ncgbw
    INTEGER(mpi) :: newlen
    INTEGER(mpi) :: nvar
    INTEGER(mpi) :: last
    INTEGER(mpi) :: lastlen

    INTEGER(mpl):: length
    INTEGER(mpl) :: rows

    ncgb=0
    ncgbw=0
    ncgbe=0
    IF(lenConstraints == 0) RETURN  ! no constraints

    newlen=0
    lastlen=0
    nvar=-1
    i=0
    last=-1
    itype=0
    !        find next constraint header and count nr of constraints
    DO WHILE(i < lenConstraints)
        i=i+1
        label=listConstraints(i)%label
        IF(last == 0.AND.label < 0) THEN
            IF (ncgb > 0 .AND. icheck>0) WRITE(*,113) ncgb, newlen-lastlen-3, nvar
            IF (nvar == 0) ncgbe=ncgbe+1
            IF (nvar == 0 .AND. iskpec > 0) THEN
                ! overwrite
                newlen=lastlen
                ! copy previous value (for label 0)
                newlen=newlen+1
                listConstraints(newlen)%value=listConstraints(i-1)%value
            ELSE
                lastlen=newlen-1 ! end of last accepted constraint
            END IF
            ncgb=ncgb+1
            itype=-label
            IF(itype == 2) ncgbw=ncgbw+1
            nvar=0
        END IF
        last=label
        IF(label > 0) THEN
            itgbi=inone(label) ! -> ITGBI= index of parameter label
            ivgb =globalParLabelIndex(2,itgbi) ! -> variable-parameter index
            IF (ivgb > 0) nvar=nvar+1
        END IF
        IF(label > 0.AND.itype == 2) THEN  ! weighted constraints
            itgbi=inone(label) ! -> ITGBI= index of parameter label
            listConstraints(i)%value=listConstraints(i)%value*globalParCounts(itgbi)
        END IF
        newlen=newlen+1
        listConstraints(newlen)%label=listConstraints(i)%label ! copy label
        listConstraints(newlen)%value=listConstraints(i)%value ! copy value
    END DO
    IF (ncgb > 0 .AND. icheck>0) WRITE(*,113) ncgb, newlen-lastlen-2, nvar
    IF (nvar == 0) ncgbe=ncgbe+1
    IF (nvar == 0 .AND. iskpec > 0) newlen=lastlen
    lenConstraints=newlen

    IF (ncgbe > 0 .AND. iskpec > 0) THEN
        WRITE(*,*) 'PRPCON:',ncgbe,' empty constraints skipped'
        ncgb=ncgb-ncgbe
    END IF
    IF (ncgbw == 0) THEN
        WRITE(*,*) 'PRPCON:',ncgb,' constraints accepted'
    ELSE
        WRITE(*,*) 'PRPCON:',ncgb,' constraints accepted,',ncgbw, 'weighted'
    END IF
    WRITE(*,*)
    
    IF(lenConstraints == 0) RETURN  ! no constraints left
    
    ! keys and index for sorting of constraints
    length=ncgb+1; rows=3
    CALL mpalloc(matConsSort,rows,length,'keys and index for sorting (I)')
    matConsSort(1,ncgb+1)=ntgb+1
    ! start of constraint in list
    CALL mpalloc(vecConsStart,length,'start of constraint in list (I)')
    vecConsStart(ncgb+1)=lenConstraints+1
    ! start and parameter range of constraint blocks 
    CALL mpalloc(matConsBlocks,rows,length,'start of constraint blocks, par. range (I)')

    ! prepare
    i=1
    DO icgb=1,ncgb
        ! new constraint 
        vecConsStart(icgb)=i
        matConsSort(1,icgb)=ntgb ! min variable parameter
        matConsSort(2,icgb)=0    ! max variable parameter
        matConsSort(3,icgb)=icgb ! index
        i=i+2
        DO
            label=listConstraints(i)%label
            itgbi=inone(label) ! -> ITGBI= index of parameter label
            ivgb =globalParLabelIndex(2,itgbi) ! -> variable-parameter index
            IF(ivgb > 0) THEN
                matConsSort(1,icgb)=min(matConsSort(1,icgb),ivgb)
                matConsSort(2,icgb)=max(matConsSort(2,icgb),ivgb)
            END IF    
            i=i+1
            IF(i > lenConstraints) EXIT
            IF(listConstraints(i)%label == 0) EXIT
        END DO
    END DO
    
    ! sort constraints
    call sort2i(matConsSort,ncgb)
    
    ! loop over sorted constraints, try to split into blocks
    ncblck=0
    nconmx=0
    nparmx=0
    mszcon=0
    mszprd=0
    isblck=1
    ilast=0
    DO jcgb=1,ncgb
        ! index in list 
        icgb=matConsSort(3,jcgb)
        ! split into disjoint blocks
        ilast=max(ilast, matConsSort(2,jcgb))
        IF (icheck > 1) THEN
            labelf=globalParLabelIndex(1,globalParVarToTotal(matConsSort(1,jcgb)))
            labell=globalParLabelIndex(1,globalParVarToTotal(matConsSort(2,jcgb)))
            WRITE(*,*) ' Cons. sorted', jcgb, icgb, vecConsStart(icgb), labelf, labell
        END IF   
        IF (matConsSort(1,jcgb+1) > ilast) THEN
            ncblck=ncblck+1
            matConsBlocks(1,ncblck)=isblck
            matConsBlocks(2,ncblck)=matConsSort(1,isblck) ! save first parameter in block
            matConsBlocks(3,ncblck)=ilast ! save last parameter in block
            ncon=jcgb+1-isblck
            npar=ilast+1-matConsSort(1,isblck)
            nconmx=max(nconmx,ncon)
            nparmx=max(nparmx,npar)
            mszcon=mszcon+ncon*npar          ! (sum of) block size for constraint matrix     
            mszprd=mszprd+(ncon*ncon+ncon)/2 ! (sum of) block size for product matrix     
            IF (icheck > 0) THEN
                labelf=globalParLabelIndex(1,globalParVarToTotal(matConsSort(1,isblck)))
                labell=globalParLabelIndex(1,globalParVarToTotal(ilast))
                WRITE(*,*) ' Cons. block ', ncblck, isblck, jcgb, labelf, labell
            ENDIF    
            ! reset for new block
            isblck=jcgb+1
        END IF
    END DO
    matConsBlocks(1,ncblck+1)=ncgb+1
    
    IF (ncblck+icheck > 1) THEN
        WRITE(*,*)
        WRITE(*,*) 'PRPCON: constraints split into ', ncblck, '(disjoint) blocks'
        WRITE(*,*) '        max block size (cons., par.) ', nconmx, nparmx
        IF (icheck > 0) WRITE(*,*) '        total block matrix sizes     ', mszcon, mszprd
    END IF    
113 FORMAT(' constraint',i6,' : ',i9,' parameters,',i9,' variable')

END SUBROUTINE prpcon

!> Matrix for feasible solution.
!!
!! Check rank of product matrix of constraints.

SUBROUTINE feasma
    USE mpmod
    USE mpdalc

    IMPLICIT NONE
    REAL(mpd) :: factr
    REAL(mpd) :: sgm
    INTEGER(mpi) :: i
    INTEGER(mpi) :: iblck
    INTEGER(mpi) :: icgb
    INTEGER(mpi) :: ij
    INTEGER(mpi) :: ifirst
    INTEGER(mpi) :: ilast
    INTEGER(mpi) :: ioffc
    INTEGER(mpi) :: ioffp
    INTEGER(mpi) :: irank
    INTEGER(mpi) :: ipar0
    INTEGER(mpi) :: itgbi
    INTEGER(mpi) :: ivgb
    INTEGER(mpi) :: j
    INTEGER(mpi) :: jcgb
    INTEGER(mpi) :: l
    INTEGER(mpi) :: label
    INTEGER(mpi) :: ncon
    INTEGER(mpi) :: npar
    INTEGER(mpi) :: nrank
    INTEGER(mpi) :: inone

    REAL(mpd):: rhs
    REAL(mpd):: evmax
    REAL(mpd):: evmin
    INTEGER(mpl):: length
    REAL(mpd), DIMENSION(:), ALLOCATABLE :: matConstraintsT
    REAL(mpd), DIMENSION(:), ALLOCATABLE :: auxVectorD
    INTEGER(mpi), DIMENSION(:), ALLOCATABLE :: auxVectorI
    SAVE
    !     ...

    IF(ncgb == 0) RETURN  ! no constraints

    ! QL decomposition
    IF (nfgb < nvgb) CALL qlini(nvgb,ncgb)
    !     product matrix A A^T (A is stored as transposed)
    length=mszprd
    CALL mpalloc(matConsProduct, length, 'product matrix of constraints (blocks)')
    matConsProduct=0.0_mpd
    length=ncgb
    CALL mpalloc(vecConsResiduals, length, 'residuals of constraints')
    CALL mpalloc(vecConsSolution, length, 'solution for constraints')
    CALL mpalloc(auxVectorI,length,'auxiliary array (I)')  ! int aux 1
    CALL mpalloc(auxVectorD,length,'auxiliary array (D)')  ! double aux 1
    !     constraint matrix A (A is stored as transposed)
    length = mszcon
    CALL mpalloc(matConstraintsT,length,'transposed matrix of constraints (blocks)')
    matConstraintsT=0.0_mpd
       
    ! loop over sorted constraints, fill matrices, get rank, inverted product matrix (in blocks)
    ioffc=0 ! block offset in constraint matrix
    ioffp=0 ! block offset in product matrix
    nrank=0
    DO iblck=1,ncblck
        ifirst=matConsBlocks(1,iblck)     ! first constraint in block
        ilast=matConsBlocks(1,iblck+1)-1  ! last constraint in block
        ncon=ilast+1-ifirst               
        ipar0=matConsBlocks(2,iblck)-1    ! parameter offset
        npar=matConsBlocks(3,iblck)-ipar0 ! number of parameters
        DO jcgb=ifirst,ilast
            ! index in list 
            icgb=matConsSort(3,jcgb)
            ! fill constraint matrix
            i=vecConsStart(icgb)
            rhs=listConstraints(i  )%value ! right hand side
            sgm=listConstraints(i+1)%value ! sigma parameter
            DO j=i+2,vecConsStart(icgb+1)-1
                label=listConstraints(j)%label
                factr=listConstraints(j)%value
                itgbi=inone(label) ! -> ITGBI= index of parameter label
                ivgb =globalParLabelIndex(2,itgbi) ! -> variable-parameter index
                IF(ivgb > 0) matConstraintsT(ivgb-ipar0+ioffc+(jcgb-ifirst)*npar)=factr ! matrix element
                globalParCons(itgbi)=globalParCons(itgbi)+1
                rhs=rhs-factr*globalParameter(itgbi)     ! reduce residuum
            END DO
            vecConsResiduals(jcgb)=rhs        ! constraint discrepancy
        END DO
        
        ! get rank of blocks
        DO l=ioffc+1,ioffc+npar
            ij=ioffp
            DO i=1,ncon
                DO j=1,i
                    ij=ij+1
                    matConsProduct(ij)=matConsProduct(ij)+matConstraintsT((i-1)*npar+l)*matConstraintsT((j-1)*npar+l)
                END DO
            END DO
        END DO
        !     inversion of product matrix of constraints
        CALL sqminv(matConsProduct(ioffp+1:ij),vecConsResiduals(ifirst:ilast),ncon,irank, auxVectorD, auxVectorI)
        IF (icheck > 1) WRITE(*,*) ' Constraint block rank', iblck, ncon, irank
        nrank=nrank+irank
        ioffc=ioffc+npar*ncon
        ioffp=ij   
    END DO          

    nmiss1=ncgb-nrank

    WRITE(*,*) ' '
    WRITE(*,*) 'Rank of product matrix of constraints is',nrank,  &
        ' for',ncgb,' constraint equations'
    WRITE(8,*) 'Rank of product matrix of constraints is',nrank,  &
        ' for',ncgb,' constraint equations'
    IF(nrank < ncgb) THEN
        WRITE(*,*) 'Warning: insufficient constraint equations!'
        WRITE(8,*) 'Warning: insufficient constraint equations!'
        IF (iforce == 0) THEN
            isubit=1
            WRITE(*,*) '         --> enforcing SUBITO mode'
            WRITE(8,*) '         --> enforcing SUBITO mode'
        END IF
    END IF
     
    ! QL decomposition
    IF (nfgb < nvgb) THEN
        print *
        print *, 'QL decomposition of constraints matrix'
        CALL qldecb(matConstraintsT,ncblck,matConsBlocks)
        ! check eignevalues of L
        CALL qlgete(evmin,evmax)
        PRINT *, '   largest  |eigenvalue| of L: ', evmax
        PRINT *, '   smallest |eigenvalue| of L: ', evmin
        IF (evmin == 0.0_mpd) THEN
            CALL peend(27,'Aborted, singular QL decomposition of constraints matrix')
            STOP 'FEASMA: stopping due to singular QL decomposition of constraints matrix'
        END IF    
    END IF

    CALL mpdealloc(matConstraintsT)
    CALL mpdealloc(auxVectorD)
    CALL mpdealloc(auxVectorI)

    RETURN
END SUBROUTINE feasma ! matrix for feasible solution

!> Make parameters feasible.
!!
!! \ref sssec-feas "Correct" for constraint equation discrepancies.
!!
!! \param [in]  concut   cut for discrepancies
!! \param [out] iact     =1 if correction needed, else =0
!!
SUBROUTINE feasib(concut,iact)
    USE mpmod
    USE mpdalc

    IMPLICIT NONE
    REAL(mpd) :: factr
    REAL(mpd) :: sgm
    INTEGER(mpi) :: i
    INTEGER(mpi) :: icgb
    INTEGER(mpi) :: iter
    INTEGER(mpi) :: itgbi
    INTEGER(mpi) :: ivgb
    INTEGER(mpi) :: iblck
    INTEGER(mpi) :: ieblck
    INTEGER(mpi) :: isblck
    INTEGER(mpi) :: ifirst
    INTEGER(mpi) :: ilast
    INTEGER(mpi) :: j
    INTEGER(mpi) :: jcgb
    INTEGER(mpi) :: label
    INTEGER(mpi) :: inone
    INTEGER(mpi) :: ncon

    REAL(mps), INTENT(IN)     :: concut
    INTEGER(mpi), INTENT(OUT) :: iact

    REAL(mpd) :: rhs
    REAL(mpd) ::sum1
    REAL(mpd) ::sum2
    REAL(mpd) ::sum3

    REAL(mpd), DIMENSION(:), ALLOCATABLE :: vecCorrections
    SAVE

    iact=0
    IF(lenConstraints == 0) RETURN  ! no constraints

    DO iter=1,2
        vecConsResiduals=0.0_mpd
  
        !      calculate right constraint equation discrepancies
        DO jcgb=1,ncgb
            icgb=matConsSort(3,jcgb) ! unsorted constraint index
            i=vecConsStart(icgb)
            rhs=listConstraints(i  )%value ! right hand side
            sgm=listConstraints(i+1)%value ! sigma parameter
            DO j=i+2,vecConsStart(icgb+1)-1
                label=listConstraints(j)%label
                factr=listConstraints(j)%value
                itgbi=inone(label) ! -> ITGBI= index of parameter label
                rhs=rhs-factr*globalParameter(itgbi)     ! reduce residuum
            ENDDO
            vecConsResiduals(jcgb)=rhs        ! constraint discrepancy
        END DO
  
        !      constraint equation discrepancies -------------------------------
  
        sum1=0.0_mpd
        sum2=0.0_mpd
        sum3=0.0_mpd
        DO icgb=1,ncgb
            sum1=sum1+vecConsResiduals(icgb)**2
            sum2=sum2+ABS(vecConsResiduals(icgb))
            sum3=MAX(sum3,ABS(vecConsResiduals(icgb)))
        END DO
        sum1=SQRT(sum1/REAL(ncgb,mpd))
        sum2=sum2/REAL(ncgb,mpd)
  
        IF(iter == 1.AND.sum1 < concut) RETURN  ! do nothing if correction small
  
        IF(iter == 1.AND.ncgb <= 12) THEN
            WRITE(*,*) ' '
            WRITE(*,*) 'Constraint equation discrepancies:'
            WRITE(*,101) (icgb,vecConsResiduals(icgb),icgb=1,ncgb)
101         FORMAT(4X,4(i5,g12.4))
            WRITE(*,103) concut
103         FORMAT(10X,' Cut on rms value is',g8.1)
        END IF
  
        IF(iact == 0) THEN
            WRITE(*,*) ' '
            WRITE(*,*) 'Improve constraints'
        END IF
        iact=1
  
        WRITE(*,102) iter,sum1,sum2,sum3
102     FORMAT(i6,'   rms',g12.4,'  avrg_abs',g12.4,'  max_abs',g12.4)
  
        CALL mpalloc(vecCorrections,INT(nvgb,mpl),'constraint corrections')
        vecCorrections=0.0_mpd

        !      multiply (block-wise) inverse matrix and constraint vector
        isblck=0
        DO iblck=1,ncblck
            ifirst=matConsBlocks(1,iblck)     ! first constraint in block
            ilast=matConsBlocks(1,iblck+1)-1  ! last constraint in block
            ncon=ilast+1-ifirst
            ieblck=isblck+(ncon*(ncon+1))/2
            CALL dbsvx(matConsProduct(isblck+1:ieblck),vecConsResiduals(ifirst:ilast),vecConsSolution(ifirst:ilast),ncon)
            isblck=ieblck
        END DO    

        DO jcgb=1,ncgb
            icgb=matConsSort(3,jcgb) ! unsorted constraint index
            i=vecConsStart(icgb)
            rhs=listConstraints(i  )%value ! right hand side
            sgm=listConstraints(i+1)%value ! sigma parameter
            DO j=i+2,vecConsStart(icgb+1)-1
                label=listConstraints(j)%label
                factr=listConstraints(j)%value
                itgbi=inone(label) ! -> ITGBI= index of parameter label
                ivgb =globalParLabelIndex(2,itgbi) ! -> variable-parameter index
                IF(ivgb > 0) THEN
                    vecCorrections(ivgb)=vecCorrections(ivgb)+vecConsSolution(jcgb)*factr
                END IF
            ENDDO
        END DO

        DO i=1,nvgb ! add corrections
            itgbi=globalParVarToTotal(i)
            globalParameter(itgbi)=globalParameter(itgbi)+vecCorrections(i)
        END DO

        CALL mpdealloc(vecCorrections)

    END DO ! iteration 1 and 2

END SUBROUTINE feasib ! make parameters feasible

!> Read (block of) records from binary files.
!!
!! Optionally using several threads (each file read by single thread).
!! Records larger than the read buffer (<tt>ndimbuf</tt>) are skipped.
!! In case of skipped events in the first loop over all binary files
!! the buffer size is adapted to the maximum record size (and the initial loop
!! (<tt>LOOP1</tt>) is repeated). C binary files are handled
!! by \ref readc.c and may be gzipped.
!!
!! \param [out]  more  more records to come
!!
!! The records consist of parallel integer and real arrays:
!!
!!         real array              integer array
!!     1   0.0                     error count (this record)
!!     2   RMEAS, measured value   0                            JA
!!     3   local derivative        index of local derivative
!!     4   local derivative        index of local derivative
!!     5    ...
!!     6   SIGMA, error (>0)       0                            JB
!!         global derivative       label of global derivative
!!         global derivative       label of global derivative   IST
!!         RMEAS, measured value   0
!!         local derivative        index of local derivative
!!         local derivative        index of local derivative
!!         ...
!!         SIGMA, error            0
!!         global derivative       label of global derivative
!!         global derivative       label of global derivative
!!         ...
!!     NR  global derivative       label of global derivative
!!
SUBROUTINE peread(more)
    USE mpmod

    IMPLICIT NONE
    INTEGER(mpi) :: i
    INTEGER(mpi) :: iact
    INTEGER(mpi) :: ierrc
    INTEGER(mpi) :: ierrf
    INTEGER(mpi) :: inder
    INTEGER(mpi) :: ioffp
    INTEGER(mpi) :: ios
    INTEGER(mpi) :: ithr
    INTEGER(mpi) :: jfile
    INTEGER(mpi) :: jrec
    INTEGER(mpi) :: k
    INTEGER(mpi) :: kfile
    INTEGER(mpi) :: l
    INTEGER(mpi) :: lun
    INTEGER(mpi) :: mpri
    INTEGER(mpi) :: n
    INTEGER(mpi) :: nact
    INTEGER(mpi) :: nbuf
    INTEGER(mpi) :: ndata
    INTEGER(mpi) :: noff
    INTEGER(mpi) :: noffs
    INTEGER(mpi) :: npointer
    INTEGER(mpi) :: npri
    INTEGER(mpi) :: nr
    INTEGER(mpi) :: nrc
    INTEGER(mpi) :: nrd
    INTEGER(mpi) :: nrpr
    INTEGER(mpi) :: nthr
    INTEGER(mpi) :: ntot
    INTEGER(mpi) :: maxRecordSize
    INTEGER(mpi) :: maxRecordFile

    INTEGER(mpi), INTENT(OUT)                     :: more

    LOGICAL :: lprint
    LOGICAL :: floop
    LOGICAL :: eof
    REAL(mpd) :: ds0
    REAL(mpd) :: ds1
    REAL(mpd) :: ds2
    REAL(mpd) :: dw
    !$    INTEGER(mpi) :: OMP_GET_THREAD_NUM
    CHARACTER (LEN=7) :: cfile
    SAVE

    inder(i)=readBufferDataI(i)

    DATA lprint/.TRUE./
    DATA floop/.TRUE./
    DATA npri / 0 /, mpri / 1000 /
    !     ...
    IF(ifile == 0) THEN  ! start/restart
        nrec=0
        nrecd=0
        ntot=0
        sumRecords=0
        skippedRecords=0
        numBlocks=0
        minRecordsInBlock=size(readBufferDataI)
        maxRecordsInBlock=0
        readBufferInfo=0  ! reset management info
        nrpr=1
        nthr=mthrdr
        nact=0   ! active threads (have something still to read)
        DO k=1,nthr
            IF (ifile < nfilb) THEN
                ifile=ifile+1
                readBufferInfo(1,k)=ifile
                readBufferInfo(2,k)=nact
                nact=nact+1
            END IF
        END DO
    END IF
    nPointer=size(readBufferPointer)/nact
    nData=size(readBufferDataI)/nact
    more=-1
    DO k=1,nthr
        iact=readBufferInfo(2,k)
        readBufferInfo(4,k)=0                 ! reset counter
        readBufferInfo(5,k)=iact*nData  ! reset offset
    END DO
    numBlocks=numBlocks+1 ! new block

    !$OMP  PARALLEL &
    !$OMP  DEFAULT(PRIVATE) &
    !$OMP  SHARED(readBufferInfo,readBufferPointer,readBufferDataI,readBufferDataD, &
    !$OMP  readBufferDataF,nPointer,nData,skippedRecords,ndimbuf,NTHR,NFILF,FLOOP, &
    !$OMP        IFD,KFD,IFILE,NFILB,WFD,XFD,icheck,keepOpen) &
    !$OMP  NUM_THREADS(NTHR)

    ithr=1
    !$ ITHR=OMP_GET_THREAD_NUM()+1     ! thread number
    jfile=readBufferInfo(1,ithr)  ! file index
    iact =readBufferInfo(2,ithr)  ! active thread number
    jrec =readBufferInfo(3,ithr)  ! records read
    ioffp=iact*nPointer
    noffs=(ithr-1)*ndimbuf        ! offset for intermediate float buffer

    files: DO WHILE (jfile > 0)
        kfile=kfd(2,jfile)
        ! open again
        IF (keepOpen < 1 .AND. readBufferInfo(3,ithr) == 0) THEN
            CALL binopn(kfile,ithr,ios)
        END IF        
        records: DO
            nbuf=readBufferInfo(4,ithr)+1
            noff=readBufferInfo(5,ithr)+2     ! 2 header words per record
            nr=ndimbuf
            IF(kfile <= nfilf) THEN ! Fortran file
                lun=kfile+10
                READ(lun,IOSTAT=ierrf) n,(readBufferDataF(noffs+i),i=1,min(n/2,nr)),&
                    (readBufferDataI(noff+i),i=1,min(n/2,nr))
                nr=n/2
                ! convert to double
                DO i=1,nr
                    readBufferDataD(noff+i)=REAL(readBufferDataF(noffs+i),mpr8)
                END DO
                ! IF (ierrf < 0) REWIND lun ! end-of-file ! CHK use binrwd()
                eof=(ierrf /= 0)
            ELSE         ! C file
                lun=kfile-nfilf
                IF (keepOpen < 1) lun=ithr
#ifdef READ_C_FILES
                CALL readc(readBufferDataD(noff+1),readBufferDataF(noffs+1),readBufferDataI(noff+1),nr,lun,ierrc)
                n=nr+nr
                IF (ierrc > 4) readBufferInfo(6,ithr)=readBufferInfo(6,ithr)+1
#else
                ierrc=0
#endif
                eof=(ierrc <= 0.AND.ierrc /= -4) ! allow buffer overruns -> skip record
                IF(eof.AND.ierrc < 0) THEN
                    WRITE(*,*) 'Read error for binary Cfile', kfile, 'record', jrec+1, ':', ierrc 
                    WRITE(8,*) 'Read error for binary Cfile', kfile, 'record', jrec+1, ':', ierrc
                    IF (icheck <= 0) THEN ! stop unless 'checkinput' mode
                        WRITE(cfile,'(I7)') kfile
                        CALL peend(18,'Aborted, read error(s) for binary file ' // cfile)
                        STOP 'PEREAD: stopping due to read errors'
                    ENDIF
                END IF
            END IF
            IF(eof) EXIT records   ! end-of-files or error

            jrec=jrec+1
            readBufferInfo(3,ithr)=jrec
            IF(floop) THEN
                xfd(jfile)=max(xfd(jfile),n)
                IF(ithr == 1) THEN
                    CALL hmplnt(1,n)
                    IF(inder(noff+1) /= 0) CALL hmpent(8,REAL(inder(noff+1),mps))
                END IF
            END IF

            IF (nr <= ndimbuf) THEN
                readBufferInfo(4,ithr)=nbuf
                readBufferInfo(5,ithr)=noff+nr

                readBufferPointer(ioffp+nbuf)=noff       ! pointer to start of buffer
                readBufferDataI(noff  )=noff+nr          ! pointer to  end  of buffer
                readBufferDataI(noff-1)=ifd(kfile)+jrec  ! global record number (available with LOOP2)
                readBufferDataD(noff  )=REAL(kfile,mpr8) ! file number
                readBufferDataD(noff-1)=REAL(wfd(kfile),mpr8) ! weight

                IF ((noff+nr+2+ndimbuf >= nData*(iact+1)).OR.(nbuf >= nPointer)) EXIT files ! buffer full
            ELSE
                !$OMP ATOMIC
                skippedRecords=skippedRecords+1
                CYCLE records
            END IF

        END DO records

        readBufferInfo(1,ithr)=-jfile   ! flag eof        
        IF (keepOpen < 1) THEN ! close again
            CALL bincls(kfile,ithr)
        ELSE ! rewind 
            CALL binrwd(kfile)    
        END IF
        IF (kfd(1,jfile) == 1) THEN
            PRINT *, 'PEREAD: file ', kfile, 'read the first time, found',jrec,' records'
            kfd(1,jfile)=-jrec
        END IF
        !        take next file
        !$OMP CRITICAL
        IF (ifile < nfilb) THEN
            ifile=ifile+1
            jrec=0
            readBufferInfo(1,ithr)=ifile
            readBufferInfo(3,ithr)=jrec
        END IF
        !$OMP END CRITICAL
        jfile=readBufferInfo(1,ithr)

    END DO files
    !$OMP END PARALLEL
    !     compress pointers
    nrd=readBufferInfo(4,1) ! buffers from 1 .thread
    DO k=2,nthr
        iact =readBufferInfo(2,k)
        ioffp=iact*nPointer
        nbuf=readBufferInfo(4,k)
        DO l=1,nbuf
            readBufferPointer(nrd+l)=readBufferPointer(ioffp+l)
        END DO
        nrd=nrd+nbuf
    END DO

    more=0
    DO k=1,nthr
        jfile=readBufferInfo(1,k)
        IF (jfile > 0) THEN ! no eof yet
            readBufferInfo(2,k)=more
            more=more+1
        ELSE
            ! no more files, thread retires
            readBufferInfo(1,k)=0
            readBufferInfo(2,k)=-1
            readBufferInfo(3,k)=0
            nrecd=nrecd+readBufferInfo(6,k)
            readBufferInfo(6,k)=0
        END IF
    END DO
    !     record limit ?
    IF (mxrec > 0.AND.(ntot+nrd) >= mxrec) THEN
        nrd=mxrec-ntot
        more=-1
        DO k=1,nthr
            jfile=readBufferInfo(1,k)
            IF (jfile > 0) THEN   ! rewind or close files
                nrc=readBufferInfo(3,k)
                IF (kfd(1,jfile) == 1) kfd(1,jfile)=-nrc
                kfile=kfd(2,jfile)
                IF (keepOpen < 1) THEN ! close again
                    CALL bincls(kfile,k)
                ELSE ! rewind
                    CALL binrwd(kfile)
                END IF               
            END IF
        END DO
    END IF

    ntot=ntot+nrd
    nrec=ntot
    numReadbuffer=nrd

    sumRecords=sumRecords+nrd
    minRecordsInBlock=MIN(minRecordsInBlock,nrd)
    maxRecordsInBlock=MAX(maxRecordsInBlock,nrd)

    DO WHILE (nloopn == 0.AND.ntot >= nrpr)
        WRITE(*,*) ' Record ',nrpr
        IF (nrpr < 100000) THEN
            nrpr=nrpr*10
        ELSE
            nrpr=nrpr+100000
        END IF
    END DO

    IF (ncache > 0.AND.nloopn <= 1.AND. npri < mpri.AND.mprint > 1) THEN
        npri=npri+1
        IF (npri == 1) WRITE(*,100)
        WRITE(*,101) nrec, nrd, more ,ifile
100     FORMAT(/' PeRead        records         active      file'  &
            /'            total     block   threads    number')
101     FORMAT(' PeRead',4I10)
    END IF

    IF (more <= 0) THEN
        ifile=0
        IF (floop) THEN
            !           check for file weights
            ds0=0.0_mpd
            ds1=0.0_mpd
            ds2=0.0_mpd
            maxRecordSize=0
            maxRecordFile=0
            DO k=1,nfilb
                IF (xfd(k) > maxRecordSize) THEN
                    maxRecordSize=xfd(k)
                    maxRecordFile=k
                END IF
                dw=REAL(-kfd(1,k),mpd)
                IF (wfd(k) /= 1.0) nfilw=nfilw+1
                ds0=ds0+dw
                ds1=ds1+dw*REAL(wfd(k),mpd)
                ds2=ds2+dw*REAL(wfd(k)**2,mpd)
            END DO
            PRINT *, 'PEREAD: file ', maxRecordFile, 'with max record size ', maxRecordSize
            IF (nfilw > 0.AND.ds0 > 0.0_mpd) THEN
                ds1=ds1/ds0
                ds2=ds2/ds0-ds1*ds1
                DO lun=6,lunlog,2
                    WRITE(lun,177) nfilw,REAL(ds1,mps),REAL(ds2,mps)
177                 FORMAT(/' !!!!!',i4,' weighted binary files',  &
                        /' !!!!! mean, variance of weights =',2G12.4)
                END DO
            END IF
            !           integrate record numbers
            DO k=2,nfilb
                ifd(k)=ifd(k-1)-kfd(1,k-1)
            END DO
            !           sort
            IF (nthr > 1) CALL sort2k(kfd,nfilb)  
            IF (skippedRecords > 0) THEN
                PRINT *, 'PEREAD skipped records: ', skippedRecords
                ndimbuf=maxRecordSize/2 ! adjust buffer size
            END IF
        END IF
        lprint=.FALSE.
        floop=.FALSE.
        IF (ncache > 0.AND.nloopn <= 1.AND.mprint > 0)  &
            WRITE(*,179) numBlocks, sumRecords, minRecordsInBlock, maxRecordsInBlock
179     FORMAT(/' Read  cache usage (#blocks, #records, ',  &
            'min,max records/block'/17X,4I10)
    END IF
    RETURN

END SUBROUTINE peread

!> Prepare records.
!!
!! For global parameters replace label by index (<tt>INONE</tt>).
!!
!! \param[in] mode <=0: build index table (INONE) for global variables; \n
!!                 >0: use index table, can be parallelized, optional scale errors 
!!
SUBROUTINE peprep(mode)
    USE mpmod

    IMPLICIT NONE

    INTEGER(mpi), INTENT(IN) :: mode

    INTEGER(mpi) :: ibuf
    INTEGER(mpi) :: ichunk
    INTEGER(mpi) :: iproc
    INTEGER(mpi) :: isfrst
    INTEGER(mpi) :: islast
    INTEGER(mpi) :: ist
    INTEGER(mpi) :: j
    INTEGER(mpi) :: ja
    INTEGER(mpi) :: jb
    INTEGER(mpi) :: jsp
    INTEGER(mpi) :: nst
    INTEGER(mpi), PARAMETER :: maxbad = 100 ! max number of bad records with print out
    INTEGER(mpi) :: nbad
    INTEGER(mpi) :: nerr
    INTEGER(mpi) :: inone
    !$    INTEGER(mpi) :: OMP_GET_THREAD_NUM


    isfrst(ibuf)=readBufferPointer(ibuf)+1
    islast(ibuf)=readBufferDataI(readBufferPointer(ibuf))

    IF (mode > 0) THEN
        ichunk=MIN((numReadBuffer+mthrd-1)/mthrd/32+1,256)
        ! parallelize record loop
        !$OMP  PARALLEL DO &
        !$OMP   DEFAULT(PRIVATE) &
        !$OMP   SHARED(numReadBuffer,readBufferPointer,readBufferDataI,readBufferDataD,ICHUNK,iscerr,dscerr) &
        !$OMP   SCHEDULE(DYNAMIC,ICHUNK)
        DO ibuf=1,numReadBuffer ! buffer for current record
            iproc=0
            !$        IPROC=OMP_GET_THREAD_NUM()         ! thread number
            ist=isfrst(ibuf)
            nst=islast(ibuf)
            DO ! loop over measurements
                CALL isjajb(nst,ist,ja,jb,jsp)
                IF(jb == 0) EXIT
                DO j=1,ist-jb
                    readBufferDataI(jb+j)=inone( readBufferDataI(jb+j) ) ! translate to index
                END DO
                ! scale error ?
                IF (iscerr > 0) THEN
                    IF (jb < ist) THEN
                        readBufferDataD(jb) = readBufferDataD(jb) * dscerr(1) ! 'global' measurement
                    ELSE
                        readBufferDataD(jb) = readBufferDataD(jb) * dscerr(2) ! 'local' measurement
                    END IF 
                END IF    
            END DO
        END DO
        !$OMP  END PARALLEL DO
    END IF

    !$POMP INST BEGIN(peprep)
    IF (mode <= 0) THEN
        nbad=0
        DO ibuf=1,numReadBuffer ! buffer for current record
            CALL pechk(ibuf,nerr)
            IF(nerr > 0) THEN
                nbad=nbad+1
                IF(nbad >= maxbad) EXIT
            ELSE
                ist=isfrst(ibuf)
                nst=islast(ibuf)
                DO ! loop over measurements
                    CALL isjajb(nst,ist,ja,jb,jsp)
                    IF(jb == 0) EXIT
                    DO j=1,ist-jb
                        readBufferDataI(jb+j)=inone( readBufferDataI(jb+j) ) ! translate to index
                    END DO
                END DO
            END IF
        END DO
        IF(nbad > 0) THEN
            CALL peend(20,'Aborted, bad binary records')
            STOP 'PEREAD: stopping due to bad records'
        END IF
    END IF
    !$POMP INST END(peprep)

END SUBROUTINE peprep

!> Check Millepede record.
!!
!! Check integer structure of labels and markers (zeros). Check floats for NaNs.
!!
!! \param [in]     ibuf   buffer number
!! \param [out]    nerr   error flags
!!
SUBROUTINE pechk(ibuf, nerr)
    USE mpmod

    IMPLICIT NONE
    REAL(mpr8) :: glder
    INTEGER(mpi) :: i
    INTEGER(mpi) :: is
    INTEGER(mpi) :: ist
    INTEGER(mpi) :: inder
    INTEGER(mpi) :: ioff
    INTEGER(mpi) :: isfrst
    INTEGER(mpi) :: islast
    INTEGER(mpi) :: ja
    INTEGER(mpi) :: jb
    INTEGER(mpi) :: jsp
    INTEGER(mpi) :: nan
    INTEGER(mpi) :: nst

    INTEGER(mpi), INTENT(IN)                      :: ibuf
    INTEGER(mpi), INTENT(OUT)                     :: nerr
    SAVE
    !     ...
    inder(i)=readBufferDataI(i)
    glder(i)=readBufferDataD(i)
    isfrst(ibuf)=readBufferPointer(ibuf)+1
    islast(ibuf)=readBufferDataI(readBufferPointer(ibuf))

    ist=isfrst(ibuf)
    nst=islast(ibuf)
    nerr=0
    is=ist
    jsp=0
    outer: DO WHILE(is < nst)
        ja=0
        jb=0
        inner1: DO
            is=is+1
            IF(is > nst) EXIT outer
            IF(inder(is) == 0) EXIT inner1 ! found 1. marker
        END DO inner1
        ja=is
        inner2: DO
            is=is+1
            IF(is > nst) EXIT outer
            IF(inder(is) == 0) EXIT inner2 ! found 2. marker
        END DO inner2
        jb=is        
        IF(ja+1 == jb.AND.glder(jb) < 0.0_mpr8) THEN
            !  special data
            jsp=jb ! pointer to special data
            is=is+NINT(-glder(jb),mpi) ! skip NSP words
            CYCLE outer
        END IF     
        DO WHILE(inder(is+1) /= 0.AND.is < nst)
            is=is+1
        END DO
    END DO outer
    IF(is > nst) THEN
        ioff = readBufferPointer(ibuf)
        WRITE(*,100) readBufferDataI(ioff-1), INT(readBufferDataD(ioff),mpi)
100     FORMAT(' PEREAD: record ', I8,' in file ',I6, ' is broken !!!')
        nerr=nerr+1
    ENDIF
    nan=0
    DO i=ist, nst
        IF(.NOT.(readBufferDataD(i) <= 0.0_mpr8).AND..NOT.(readBufferDataD(i) > 0.0_mpr8)) nan=nan+1
    END DO
    IF(nan > 0) THEN
        ioff = readBufferPointer(ibuf)
        WRITE(*,101) readBufferDataI(ioff-1), INT(readBufferDataD(ioff),mpi), nan
101     FORMAT(' PEREAD: record ', I8,' in file ',I6, ' contains ', I6, ' NaNs !!!')
        nerr= nerr+2
    ENDIF

END SUBROUTINE pechk

!> Decode Millepede record.
!!
!! Get indices JA, JB, IS for next measurement within record:
!! - Measurement is: <tt>GLDER(JA)</tt>
!! - Local derivatives are:
!!   <tt>(INDER(JA+J),GLDER(JA+J),J=1,JB-JA-1)</tt>  i.e. JB-JA-1 derivatives
!! - Standard deviation is: <tt>GLDER(JB)</tt>
!! - Global derivatives are:
!!   <tt>(INDER(JB+J),GLDER(JB+J),J=1,IS-JB)</tt>  i.e. IST-JB derivatives
!!
!! End_of_data is indicated by returned values JA=0 and JB=0
!! Special data are ignored. At end_of_data the info to the
!! special data is returned: IS = pointer to special data;
!! number of words is <tt>NSP=-GLDER(IS)</tt>.
!!
!! \param [in]     nst    index of last  word of record
!! \param [in,out] is     index of last global derivative
!!                        (index of first word of record at the first call)
!! \param [out]    ja     index of measured value (=0 at end), = pointer to local derivatives
!! \param [out]    jb     index of standard deviation (=0 at end), = pointer to global derivatives
!! \param [out]    jsp    index to special data
!!
SUBROUTINE isjajb(nst,is,ja,jb,jsp)
    USE mpmod

    IMPLICIT NONE
    REAL(mpr8) :: glder
    INTEGER(mpi) :: i
    INTEGER(mpi) :: inder

    INTEGER(mpi), INTENT(IN)                      :: nst
    INTEGER(mpi), INTENT(IN OUT)                  :: is
    INTEGER(mpi), INTENT(OUT)                     :: ja
    INTEGER(mpi), INTENT(OUT)                     :: jb
    INTEGER(mpi), INTENT(OUT)                     :: jsp
    SAVE
    !     ...
    inder(i)=readBufferDataI(i)
    glder(i)=readBufferDataD(i)

    jsp=0
    DO
        ja=0
        jb=0
        IF(is >= nst) RETURN
        DO
            is=is+1
            IF(inder(is) == 0) EXIT
        END DO
        ja=is
        DO
            is=is+1
            IF(inder(is) == 0) EXIT
        END DO
        jb=is
        IF(ja+1 == jb.AND.glder(jb) < 0.0_mpr8) THEN
            !  special data
            jsp=jb ! pointer to special data
            is=is+NINT(-glder(jb),mpi) ! skip NSP words
            CYCLE
        END IF     
        DO WHILE(inder(is+1) /= 0.AND.is < nst)
            is=is+1
        END DO
        EXIT
    END DO

END SUBROUTINE isjajb


!***********************************************************************
!                        LOOPN ...
!> \ref sssec-loopn "Loop" with fits and sums.
!!
!! Loop over all binary files. Perform local fits to calculate Chi2, ndf
!! and r.h.s. 'b' of linear equation system A*x=b. In first iteration(s)
!! fill matrix A.

SUBROUTINE loopn
    USE mpmod

    IMPLICIT NONE
    REAL(mpd) :: dsum
    REAL(mps) :: elmt
    REAL(mpd) :: factrj
    REAL(mpd) :: factrk
    REAL(mpr8) :: glder
    REAL(mps) :: peakd
    REAL(mps) :: peaki
    REAL(mps) :: ratae
    REAL(mpd) :: rhs
    REAL(mps) :: rloop
    REAL(mpd) :: sgm
    REAL(mps) :: used
    REAL(mps) :: usei
    REAL(mpd) :: weight
    INTEGER(mpi) :: i
    INTEGER(mpi) :: ia
    INTEGER(mpi) :: ib
    INTEGER(mpi) :: ibuf
    INTEGER(mpi) :: inder
    INTEGER(mpi) :: ioffb
    INTEGER(mpi) :: ipr
    INTEGER(mpi) :: isfrst
    INTEGER(mpi) :: islast
    INTEGER(mpi) :: itgbi
    INTEGER(mpi) :: itgbij
    INTEGER(mpi) :: itgbik
    INTEGER(mpi) :: ivgb
    INTEGER(mpi) :: ivgbij
    INTEGER(mpi) :: ivgbik
    INTEGER(mpi) :: j
    INTEGER(mpi) :: k
    INTEGER(mpi) :: lastit
    INTEGER(mpi) :: lun
    INTEGER(mpi) :: ncrit
    INTEGER(mpi) :: ndfs
    INTEGER(mpi) :: ngras
    INTEGER(mpi) :: nparl
    INTEGER(mpi) :: nr
    INTEGER(mpi) :: nrej
    INTEGER(mpi) :: inone
    INTEGER(mpi) :: ilow
    INTEGER(mpi) :: nlow
    INTEGER(mpi) :: nzero
    LOGICAL :: btest

    REAL(mpd):: adder
    REAL(mpd)::funref
    REAL(mpd)::dchi2s
    REAL(mpd)::sndf
    INTEGER(mpl):: ii
    SAVE
    !     ...
    isfrst(ibuf)=readBufferPointer(ibuf)+1
    islast(ibuf)=readBufferDataI(readBufferPointer(ibuf))
    inder(i)=readBufferDataI(i)
    glder(i)=readBufferDataD(i)
    !     ----- book and reset ---------------------------------------------
    IF(nloopn == 0) THEN      ! first call
        lastit=-1
        iitera=0
    END IF

    nloopn=nloopn+1           ! increase loop counter
    ndfsum=0
    sumndf=0.0_mpd
    funref=0.0_mpd

    IF(nloopn == 1) THEN      ! book histograms for 1. iteration
        CALL gmpdef(1,4,'Function value in iterations')
        IF (metsol == 3 .OR. metsol == 4) THEN ! extend to GMRES, i.e. 4?
            CALL gmpdef(2,3,'Number of MINRES steps vs iteration nr')
        END IF
        CALL hmpdef( 5,0.0,0.0,'Number of degrees of freedom')
        CALL hmpdef(11,0.0,0.0,'Number of local parameters')
        CALL hmpdef(23,0.0,0.0, 'SQRT of diagonal elements without presigma')
        CALL hmpdef(24,0.0,0.0, 'Log10 of off-diagonal elements')
        CALL hmpdef(25,0.0,0.0, 'Relative individual pre-sigma')
        CALL hmpdef(26,0.0,0.0, 'Relative global pre-sigma')
    END IF


    CALL hmpdef(3,-prange,prange, &   ! book
        'Normalized residuals of single (global) measurement')
    CALL hmpdef(12,-prange,prange, &   ! book
        'Normalized residuals of single (local) measurement')
    CALL hmpdef(13,-prange,prange, &   ! book
        'Pulls of single (global) measurement')
    CALL hmpdef(14,-prange,prange, &   ! book
        'Pulls of single (local) measurement')
    CALL hmpdef(4,0.0,0.0,'Chi^2/Ndf after local fit')
    CALL gmpdef(4,5,'location, dispersion (res.) vs record nr')
    CALL gmpdef(5,5,'location, dispersion (pull) vs record nr')

    !      WRITE(*,*) 'LOOPN ', NLOOPN, ' executing ICALCM=', ICALCM

    !     reset

    globalVector=0.0_mpd ! reset rhs vector              IGVEC
    globalCounter=0
    IF(icalcm == 1) THEN
        globalMatD=0.0_mpd
        globalMatF=0.
        IF (metsol >= 3) matPreCond=0.0_mpd
    END IF

    IF(nloopn == 2) CALL hmpdef(6,0.0,0.0,'Down-weight fraction')

    newite=.FALSE.
    IF(iterat /= lastit) THEN ! new iteration
        newite=.TRUE.
        funref=fvalue
        IF(nloopn > 1) THEN
            nrej=nrejec(0)+nrejec(1)+nrejec(2)+nrejec(3)
            !            CALL MEND
            IF(iterat == 1) THEN
                chicut=chirem
            ELSE IF(iterat >= 1) THEN
                chicut=SQRT(chicut)
                IF(chicut /= 0.0.AND.chicut < 1.5) chicut=1.0
                IF(chicut /= 0.0.AND.nrej == 0)    chicut=1.0
            END IF
        END IF
    !         WRITE(*,111) ! header line
    END IF

    DO i=0,3
        nrejec(i)=0   ! reset reject counter
    END DO
    DO k=3,6
        writeBufferHeader(k)=0  ! cache usage
        writeBufferHeader(-k)=0
    END DO
    !     statistics per binary file
    DO i=1,nfilb
        jfd(i)=0
        cfd(i)=0.0
        dfd(i)=0
    END DO
    
    IF (imonit /= 0) measHists=0 ! reset monitoring histograms
    
    !     ----- read next data ----------------------------------------------
    DO
        CALL peread(nr)  ! read records
        CALL peprep(1)   ! prepare records
        ndfs  =0
        sndf  =0.0_mpd
        dchi2s=0.0_mpd
        CALL loopbf(nrejec,ndfs,sndf,dchi2s,nfiles,jfd,cfd,dfd)
        ndfsum=ndfsum+ndfs
        sumndf=sumndf+sndf
        CALL addsum(dchi2s)
        IF (nr <= 0) EXIT ! next block of events ?
    END DO
    ! sum up RHS (over threads) once (reduction in LOOPBF: summation for each block)
    ioffb=0
    DO ipr=2,mthrd
        ioffb=ioffb+lenGlobalVec
        DO k=1,lenGlobalVec
            globalVector(k)=globalVector(k)+globalVector(ioffb+k)
            globalCounter(k)=globalCounter(k)+globalCounter(ioffb+k)
        END DO
    END DO

    IF (icalcm == 1) THEN
        ! PRINT *, ' cache/w ',(writeBufferHeader(-K),K=3,6),(writeBufferHeader(K),K=3,6)
        nparl=writeBufferHeader(3)
        ncrit=writeBufferHeader(4)
        used=REAL(writeBufferHeader(-5),mps)/REAL(writeBufferHeader(-3),mps)*0.1
        usei=REAL(writeBufferHeader(5),mps)/REAL(writeBufferHeader(3),mps)*0.1
        peakd=REAL(writeBufferHeader(-6),mps)*0.1
        peaki=REAL(writeBufferHeader(6),mps)*0.1
        WRITE(*,111) nparl,ncrit,usei,used,peaki,peakd
111     FORMAT(' Write cache usage (#flush,#overrun,<levels>,',  &
            'peak(levels))'/2I7,',',4(f6.1,'%'))
        ! fill second half (j>i) of global matric for extended storage
        IF (mextnd > 0) CALL mhalf2()
    END IF

    ! check entries/counters
    nlow=0
    ilow=1
    nzero=0
    DO i=1,nvgb
        IF(globalCounter(i) == 0) nzero=nzero+1
        IF(globalCounter(i) < mreqena) THEN
            nlow=nlow+1
            IF(globalCounter(i) < globalCounter(ilow)) ilow=i
        END IF
    END DO
    IF(nlow > 0) THEN
        nalow=nalow+nlow
        itgbi=globalParVarToTotal(ilow)
        print *
        print *, " ... warning ..." 
        print *, " global parameters with too few (< MREQENA) accepted entries: ", nlow
        print *, " minimum entries: ", globalCounter(ilow), " for label ", globalParLabelIndex(1,itgbi)
        print *
    END IF   
    IF(icalcm == 1 .AND. nzero > 0) THEN
        ndefec = nzero ! rank defect
        WRITE(*,*)   'Warning: the rank defect of the symmetric',nfgb,  &
            '-by-',nfgb,' matrix is ',ndefec,' (should be zero).'
        WRITE(lun,*) 'Warning: the rank defect of the symmetric',nfgb,  &
            '-by-',nfgb,' matrix is ',ndefec,' (should be zero).'
        IF (iforce == 0) THEN
            isubit=1
            WRITE(*,*)   '         --> enforcing SUBITO mode'
            WRITE(lun,*) '         --> enforcing SUBITO mode'
        END IF
    END IF

    !     ----- after end-of-data add contributions from pre-sigma ---------

    IF(nloopn == 1) THEN
        !        plot diagonal elements
        elmt=0.0
        DO i=1,nvgb        ! diagonal elements
            ii=0
            IF(matsto == 1) THEN
                ii=i
                ii=(ii*ii+ii)/2
            END IF
            IF(matsto == 2) ii=i
            IF(matsto == 3) ii=i
            IF(ii /= 0) THEN
                elmt=REAL(globalMatD(ii),mps)
                IF(elmt > 0.0) CALL hmpent(23,1.0/SQRT(elmt))
            END IF
        END DO
    END IF



    !     add pre-sigma contributions to matrix diagonal

    !      WRITE(*,*) 'Adding to diagonal ICALCM IND6',ICALCM,IND6

    IF(icalcm == 1) THEN
        DO ivgb=1,nvgb                        ! add evtl. pre-sigma
            !          WRITE(*,*) 'Index ',IVGB,IVGB,QM(IND6+IVGB)
            IF(globalParPreWeight(ivgb) /= 0.0) THEN
                IF(ivgb > 0) CALL mupdat(ivgb,ivgb,globalParPreWeight(ivgb))
            END IF
        END DO
    END IF

    CALL hmpwrt(23)
    CALL hmpwrt(24)
    CALL hmpwrt(25)
    CALL hmpwrt(26)


    !     add regularization term to F and to rhs --------------------------

    !      WRITE(*,*) 'NREGUL ',NREGUL,NLOOPN

    IF(nregul /= 0) THEN ! add regularization term to F and to rhs
        DO ivgb=1,nvgb
            itgbi=globalParVarToTotal(ivgb) ! global parameter index
            globalVector(ivgb)=globalVector(ivgb) -globalParameter(itgbi)*globalParPreWeight(ivgb)
            adder=globalParPreWeight(ivgb)*globalParameter(itgbi)**2
            CALL addsum(adder)
        END DO
    END IF


    !     ----- add contributions from "measurement" -----------------------


    i=1
    DO WHILE (i <= lenMeasurements)
        rhs=listMeasurements(i  )%value ! right hand side
        sgm=listMeasurements(i+1)%value ! sigma parameter
        i=i+2
        weight=0.0
        IF(sgm > 0.0) weight=1.0/sgm**2

        dsum=-rhs

        !     loop over label/factor pairs
        ia=i
        DO
            i=i+1
            IF(i > lenMeasurements) EXIT
            IF(listMeasurements(i)%label == 0) EXIT
        END DO
        ib=i-1

        DO j=ia,ib
            factrj=listMeasurements(j)%value
            itgbij=inone(listMeasurements(j)%label) ! total parameter index
            IF(itgbij /= 0) THEN
                dsum=dsum+factrj*globalParameter(itgbij)     ! residuum
            END IF
            !      add to vector
            ivgbij=0
            IF(itgbij /= 0) ivgbij=globalParLabelIndex(2,itgbij) ! variable-parameter index
            IF(ivgbij > 0) THEN
                globalVector(ivgbij)=globalVector(ivgbij) -weight*dsum*factrj ! vector
                globalCounter(ivgbij)=globalCounter(ivgbij)+1
            END IF
  
            IF(icalcm == 1.AND.ivgbij > 0) THEN
                DO k=ia,j
                    factrk=listMeasurements(k)%value
                    itgbik=inone(listMeasurements(k)%label) ! total parameter index
                    !          add to matrix
                    ivgbik=0
                    IF(itgbik /= 0) ivgbik=globalParLabelIndex(2,itgbik) ! variable-parameter index
                    IF(ivgbij > 0.AND.ivgbik > 0) THEN    !
                        CALL mupdat(ivgbij,ivgbik,weight*factrj*factrk)
                    END IF
                END DO
            END IF
        END DO

        adder=weight*dsum**2
        CALL addsum(adder)   ! accumulate chi-square

    END DO

    !     ----- printout ---------------------------------------------------


    CALL getsum(fvalue)   ! get accurate sum (Chi^2)
    flines=0.5_mpd*fvalue   ! Likelihood function value
    rloop=iterat+0.01*nloopn
    actfun=REAL(funref-fvalue,mps)
    IF(nloopn == 1) actfun=0.0
    ngras=nint(angras,mpi)
    ratae=0.0                              !!!
    IF(delfun /= 0.0) THEN
        ratae=MIN(99.9,actfun/delfun)  !!!
        ratae=MAX(-99.9,ratae)
    END IF

    !     rejects ...

    nrej  =nrejec(0)+nrejec(1)+nrejec(2)+nrejec(3)
    IF(nloopn == 1) THEN
        IF(nrej /= 0) THEN
            WRITE(*,*) ' '
            WRITE(*,*) 'Data rejected in initial loop:'
            WRITE(*,*) '   ',  &
                nrejec(0), ' (rank deficit/NaN) ',nrejec(1),' (Ndf=0)   ',  &
                nrejec(2), ' (huge)   ',nrejec(3),' (large)'
        END IF
    END IF
    !      IF(NREJEC(1)+NREJEC(2)+NREJEC(3).NE.0) THEN
    !         WRITE(LUNLOG,*) 'Data rejected in initial loop:',NREJEC(1),
    !     +   ' (Ndf=0)   ',NREJEC(2),' (huge)   ',NREJEC(3),' (large)'
    !      END IF


    IF(newite.AND.iterat == 2) THEN
        IF(nrecpr /= 0.OR.nrecp2 /= 0) nrecer=nrec3
        IF(nrecpr < 0) THEN
            nrecpr=nrec1
        END IF
        IF(nrecp2 < 0) THEN
            nrecp2=nrec2
        END IF
    END IF

    IF(nloopn <= 2) THEN
        IF(nhistp /= 0) THEN
        !            CALL HMPRNT(3)  ! scaled residual of single measurement
        !            CALL HMPRNT(12) ! scaled residual of single measurement
        !            CALL HMPRNT(4)  ! chi^2/Ndf
        END IF
        CALL hmpwrt(3)
        CALL hmpwrt(12)
        CALL hmpwrt(4)
        CALL gmpwrt(4) ! location, dispersion (res.) as a function of record nr
        IF (nloopn <= lfitnp) THEN
            CALL hmpwrt(13)
            CALL hmpwrt(14)
            CALL gmpwrt(5) ! location, dispersion (pull) as a function of record nr
        END IF
    END IF
    !      IF(NLOOPN.EQ.2.AND.NHISTP.NE.0) CALL HMPRNT(6)
    IF(nloopn == 2) CALL hmpwrt(6)
    IF(nloopn <= 1) THEN
        !         IF(NHISTP.NE.0) CALL HMPRNT(5)  ! number of degrees of freedom
        !         IF(NHISTP.NE.0) CALL HMPRNT(11) ! Nlocal
        CALL hmpwrt(5)
        CALL hmpwrt(11)
    END IF

    !     local fit: band matrix structure !?
    IF (nloopn == 1.AND.nbndr(1)+nbndr(2) > 0) THEN
        DO lun=6,8,2
            WRITE(lun,*) ' '
            WRITE(lun,*) ' === local fits have bordered band matrix structure ==='
            IF (nbndr(1) > 0 ) WRITE(lun,101) ' NBNDR',nbndr(1),'number of records (upper/left border)'
            IF (nbndr(2) > 0 ) WRITE(lun,101) ' NBNDR',nbndr(2),'number of records (lower/right border)'
            WRITE(lun,101) ' NBDRX',nbdrx,'max border size'
            WRITE(lun,101) ' NBNDX',nbndx,'max band width'
        END DO
    END IF

    lastit=iterat
    
    ! monitoring of residuals
    IF (imonit < 0 .OR. (nloopn == 1 .AND. btest(imonit,0))) CALL monres

101 FORMAT(1X,a8,' =',i10,' = ',a)
! 101  FORMAT(' LOOPN',I6,' Function value',F22.8,10X,I6,' records')
! 102  FORMAT('   incl. constraint penalty',F22.8)
! 103  FORMAT(I13,3X,A,G12.4)
END SUBROUTINE loopn                 ! loop with fits

!> Print title for iteration.
!!
!! \param [in] lunp    unit number

SUBROUTINE ploopa(lunp)
    USE mpmod

    IMPLICIT NONE

    INTEGER(mpi), INTENT(IN)                  :: lunp
    !     ..
    WRITE(lunp,*)   ' '
    WRITE(lunp,101) ! header line
    WRITE(lunp,102) ! header line
101 FORMAT(' it fc','   fcn_value dfcn_exp  slpr costh  iit st',  &
        ' ls  step cutf',1X,'rejects hhmmss FMS')
102 FORMAT(' -- --',' ----------- --------  ---- -----  --- --',  &
        ' -- ----- ----',1X,'------- ------ ---')
    RETURN
END SUBROUTINE ploopa   ! title for iteration

!> Print iteration line.
!!
!! \param [in] lunp    unit number

SUBROUTINE ploopb(lunp)
    USE mpmod

    IMPLICIT NONE
    INTEGER(mpi) :: ma
    INTEGER :: minut
    INTEGER(mpi) :: nfa
    INTEGER :: nhour
    INTEGER(mpi) :: nrej
    INTEGER(mpi) :: nsecnd
    REAL(mps) :: ratae
    REAL :: rstb
    REAL(mps) :: secnd
    REAL(mps) :: slopes(3)
    REAL(mps) :: steps(3)
    REAL, DIMENSION(2) :: ta

    INTEGER(mpi), INTENT(IN)                  :: lunp

    CHARACTER (LEN=4):: ccalcm(4)
    DATA ccalcm / ' end','   S', ' F  ',' FMS' /
    SAVE

    nrej=nrejec(0)+nrejec(1)+nrejec(2)+nrejec(3)    ! rejects
    IF(nrej > 9999999) nrej=9999999
    CALL etime(ta,rstb)
    deltim=rstb-rstart
    CALL sechms(deltim,nhour,minut,secnd) ! time
    nsecnd=nint(secnd,mpi)
    IF(iterat == 0) THEN
        WRITE(lunp,103) iterat,nloopn,fvalue,  &
            chicut,nrej,nhour,minut,nsecnd,ccalcm(lcalcm)
    ELSE
        IF (lsinfo == 10) THEN ! line search skipped
            WRITE(lunp,105) iterat,nloopn,fvalue,delfun,  &
                iitera,istopa,chicut,nrej,nhour,minut,nsecnd,ccalcm(lcalcm)
        ELSE
            CALL ptlopt(nfa,ma,slopes,steps)  ! slopes steps
            ratae=MAX(-99.9,MIN(99.9,slopes(2)/slopes(1)))
            stepl=steps(2)
            WRITE(lunp,104) iterat,nloopn,fvalue,delfun,ratae,angras,  &
                iitera,istopa,lsinfo,stepl, chicut,nrej,nhour,minut,nsecnd,ccalcm(lcalcm)
        ENDIF
    END IF
103 FORMAT(i3,i3,e12.5,38X,f5.1, 1X,i7,  i3,i2.2,i2.2,a4)
104 FORMAT(i3,i3,e12.5,1X,e8.2,f6.3,f6.3,i5,2I3,f6.3,f5.1,  &
        1X,i7,  i3,i2.2,i2.2,a4)
105 FORMAT(i3,i3,e12.5,1X,e8.2,12X,i5,I3,9X,f5.1,  &
        1X,i7,  i3,i2.2,i2.2,a4)
    RETURN
END SUBROUTINE ploopb ! iteration line

!> Print sub-iteration line.
!!
!! \param [in] lunp    unit number

SUBROUTINE ploopc(lunp)
    USE mpmod

    IMPLICIT NONE
    INTEGER(mpi) :: ma
    INTEGER(mpi) :: minut
    INTEGER(mpi) :: nfa
    INTEGER(mpi) :: nhour
    INTEGER(mpi) :: nrej
    INTEGER(mpi) :: nsecnd
    REAL(mps) :: ratae
    REAL :: rstb
    REAL(mps) :: secnd
    REAL(mps) :: slopes(3)
    REAL(mps) :: steps(3)
    REAL, DIMENSION(2) :: ta

    INTEGER(mpi), INTENT(IN)                  :: lunp
    CHARACTER (LEN=4):: ccalcm(4)
    DATA ccalcm / ' end','   S', ' F  ',' FMS' /
    SAVE

    nrej=nrejec(0)+nrejec(1)+nrejec(2)+nrejec(3)    ! rejects
    IF(nrej > 9999999) nrej=9999999
    CALL etime(ta,rstb)
    deltim=rstb-rstart
    CALL sechms(deltim,nhour,minut,secnd) ! time
    nsecnd=nint(secnd,mpi)
    IF (lsinfo == 10) THEN ! line search skipped
        WRITE(lunp,104) nloopn,fvalue,nrej,nhour,minut,nsecnd,ccalcm(lcalcm)
    ELSE
        CALL ptlopt(nfa,ma,slopes,steps)  ! slopes steps
        ratae=ABS(slopes(2)/slopes(1))
        stepl=steps(2)
        WRITE(lunp,105) nloopn,fvalue, ratae,lsinfo,  &
            stepl,nrej,nhour,minut,nsecnd,ccalcm(lcalcm)
    END IF
104 FORMAT(3X,i3,e12.5,9X, 35X, i7,  i3,i2.2,i2.2,a4)
105 FORMAT(3X,i3,e12.5,9X,     f6.3,14X,i3,f6.3,6X, i7,  i3,i2.2,i2.2,a4)
    RETURN

END SUBROUTINE ploopc                   ! sub-iteration line

!> Print solution line.
!!
!! \param [in] lunp    unit number

SUBROUTINE ploopd(lunp)
    USE mpmod
    IMPLICIT NONE
    INTEGER :: minut
    INTEGER :: nhour
    INTEGER(mpi) :: nsecnd
    REAL :: rstb
    REAL(mps) :: secnd
    REAL, DIMENSION(2) :: ta


    INTEGER(mpi), INTENT(IN)                  :: lunp
    CHARACTER (LEN=4):: ccalcm(4)
    DATA ccalcm / ' end','   S', ' F  ',' FMS' /
    SAVE
    CALL etime(ta,rstb)
    deltim=rstb-rstart
    CALL sechms(deltim,nhour,minut,secnd) ! time
    nsecnd=NINT(secnd,mpi)

    WRITE(lunp,106) nhour,minut,nsecnd,ccalcm(lcalcm)
106 FORMAT(69X,i3,i2.2,i2.2,a4)
    RETURN
END SUBROUTINE ploopd

!> Print explanation of iteration table.
SUBROUTINE explfc(lunit)
    USE mpdef
    USE mpmod, ONLY: metsol

    IMPLICIT NONE
    INTEGER(mpi) :: lunit
    WRITE(lunit,*) ' '
    WRITE(lunit,102) 'Explanation of iteration table'
    WRITE(lunit,102) '=============================='
    WRITE(lunit,101) 'it',  &
        'iteration number. Global parameters are improved for it > 0.'
    WRITE(lunit,102) 'First function evaluation is called iteraton 0.'
    WRITE(lunit,101) 'fc', 'number of function evaluations.'
    WRITE(lunit,101) 'fcn_value', 'value of 2 x Likelihood function (LF).'
    WRITE(lunit,102) 'The final value is the chi^2 value of the fit and should'
    WRITE(lunit,102) 'be about equal to the NDF (see below).'
    WRITE(lunit,101) 'dfcn_exp',  &
        'expected reduction of the value of the Likelihood function (LF)'
    WRITE(lunit,101) 'slpr', 'ratio of the actual slope to inital slope.'
    WRITE(lunit,101) 'costh',  &
        'cosine of angle between search direction and -gradient'
    IF (metsol == 3) THEN
        WRITE(lunit,101) 'iit',  &
            'number of internal iterations in MINRES algorithm'
        WRITE(lunit,101) 'st', 'stop code of MINRES algorithm'
        WRITE(lunit,102) '< 0:   rhs is very special, with beta2 = 0'
        WRITE(lunit,102) '= 0:   rhs b = 0, i.e. the exact solution is  x = 0'
        WRITE(lunit,102) '= 1    requested accuracy achieved, as determined by rtol'
        WRITE(lunit,102) '= 2    reasonable accuracy achieved, given eps'
        WRITE(lunit,102) '= 3    x has converged to an eigenvector'
        WRITE(lunit,102) '= 4    matrix ill-conditioned (Acond has exceeded 0.1/eps)'
        WRITE(lunit,102) '= 5    the iteration limit was reached'
        WRITE(lunit,102) '= 6    Matrix x vector does not define a symmetric matrix'
        WRITE(lunit,102) '= 7    Preconditioner does not define a symmetric matrix'
    ELSEIF (metsol == 4) THEN
        WRITE(lunit,101) 'iit',  &
            'number of internal iterations in MINRES-QLP algorithm'
        WRITE(lunit,101) 'st', 'stop code of MINRES-QLP algorithm'
        WRITE(lunit,102) '= 1: beta_{k+1} < eps, iteration k is the final Lanczos step.'
        WRITE(lunit,102) '= 2: beta2 = 0.  If M = I, b and x are eigenvectors of A.'
        WRITE(lunit,102) '= 3: beta1 = 0.  The exact solution is  x = 0.'
        WRITE(lunit,102) '= 4: A solution to (poss. singular) Ax = b found, given rtol.'
        WRITE(lunit,102) '= 5: A solution to (poss. singular) Ax = b found, given eps.'
        WRITE(lunit,102) '= 6: Pseudoinverse solution for singular LS problem, given rtol.'
        WRITE(lunit,102) '= 7: Pseudoinverse solution for singular LS problem, given eps.'
        WRITE(lunit,102) '= 8: The iteration limit was reached.'
        WRITE(lunit,102) '= 9: The operator defined by Aprod appears to be unsymmetric.'
        WRITE(lunit,102) '=10: The operator defined by Msolve appears to be unsymmetric.'
        WRITE(lunit,102) '=11: The operator defined by Msolve appears to be indefinite.'
        WRITE(lunit,102) '=12: xnorm has exceeded maxxnorm or will exceed it next iteration.'
        WRITE(lunit,102) '=13: Acond has exceeded Acondlim or 0.1/eps.'
        WRITE(lunit,102) '=14: Least-squares problem but no converged solution yet.'
        WRITE(lunit,102) '=15: A null vector obtained, given rtol.'
    ENDIF
    WRITE(lunit,101) 'ls', 'line search info'
    WRITE(lunit,102) '< 0    recalculate function'
    WRITE(lunit,102) '= 0:   N or STP lt 0 or step not descending'
    WRITE(lunit,102) '= 1:   Linesearch convergence conditions reached'
    WRITE(lunit,102) '= 2:   interval of uncertainty at lower limit'
    WRITE(lunit,102) '= 3:   max nr of line search calls reached'
    WRITE(lunit,102) '= 4:   step at the lower bound'
    WRITE(lunit,102) '= 5:   step at the upper bound'
    WRITE(lunit,102) '= 6:   rounding error limitation'
    WRITE(lunit,101) 'step',  &
        'the factor for the Newton step during the line search. Usually'
    WRITE(lunit,102)  &
        'a value of 1 gives a sufficient reduction of the LF. Oherwise'
    WRITE(lunit,102) 'other step values are tried.'
    WRITE(lunit,101) 'cutf',  &
        'cut factor. Local fits are rejected, if their chi^2 value'
    WRITE(lunit,102)  &
        'is larger than the 3-sigma chi^2 value times the cut factor.'
    WRITE(lunit,102) 'A cut factor of 1 is used finally, but initially a larger'
    WRITE(lunit,102) 'factor may be used. A value of 0.0 means no cut.'
    WRITE(lunit,101) 'rejects', 'total number of rejected local fits.'
    WRITE(lunit,101) 'hmmsec', 'the time in hours (h), minutes (mm) and seconds.'
    WRITE(lunit,101) 'FMS', 'calculation of Function value, Matrix, Solution.'
    WRITE(lunit,*) ' '

101 FORMAT(a9,' =  ',a)
102 FORMAT(13X,a)
END SUBROUTINE explfc

!> Update element of global matrix.
!!
!! Add value ADD to matrix element (I,J).
!!
!! \param [in]  i   first index
!! \param [in]  j   second index
!! \param [in]  add summand

SUBROUTINE mupdat(i,j,add)       !
    USE mpmod

    IMPLICIT NONE

    INTEGER(mpi), INTENT(IN)                      :: i
    INTEGER(mpi), INTENT(IN)                      :: j
    REAL(mpd), INTENT(IN)             :: add

    INTEGER(mpl):: ijadd
    INTEGER(mpl):: ia
    INTEGER(mpl):: ja
    INTEGER(mpl):: ij
    !     ...
    IF(i <= 0.OR.j <= 0) RETURN
    ia=MAX(i,j)          ! larger
    ja=MIN(i,j)          ! smaller
    ij=0
    IF(matsto == 1) THEN                  ! full symmetric matrix
        ij=ja+(ia*ia-ia)/2                ! ISYM index
        globalMatD(ij)=globalMatD(ij)+add
    ELSE IF(matsto == 2) THEN             ! sparse symmetric matrix
        ij=ijadd(i,j)                     ! inline code requires same time
        IF (ij == 0) RETURN               ! pair is suppressed
        IF (ij > 0) THEN
            globalMatD(ij)=globalMatD(ij)+add
        ELSE
            globalMatF(-ij)=globalMatF(-ij)+REAL(add,mps)
        END IF
    END IF
    IF(metsol >= 3) THEN
        IF(mbandw > 0) THEN     ! for Cholesky decomposition
            IF(ia <= nvgb) THEN   ! variable global parameter
                ij=indPreCond(ia)-ia+ja
                IF(ia > 1.AND.ij <= indPreCond(ia-1)) ij=0
                IF(ij /= 0) matPreCond(ij)=matPreCond(ij)+add
                IF(ij < 0.OR.ij > size(matPreCond)) THEN
                    CALL peend(23,'Aborted, bad matrix index')
                    STOP 'mupdat: bad index'
                END IF
            ELSE                  ! Lagrange multiplier
                ij=indPreCond(nvgb)+(ia-nvgb-1)*nvgb+ja
                IF(ij /= 0) matPreCond(ij)=matPreCond(ij)+add
            END IF
        ELSE IF(mbandw == 0) THEN      ! default preconditioner
            IF(ia <= nvgb) THEN   ! variable global parameter
                IF(ja == ia) matPreCond(ia)=matPreCond(ia)+add ! diag
            ELSE                  ! Lagrange multiplier
                ij=nvgb+(ia-nvgb-1)*nvgb+ja
                IF(ij /= 0) matPreCond(ij)=matPreCond(ij)+add
            END IF
        END IF
    END IF
END SUBROUTINE mupdat


!> Loop over records in read buffer (block), fits and sums.
!!
!! Loop over records in current read buffer block (with multiple threads).
!! Perform \ref par-locfitv "local fits" (optionally with \ref par-downw
!! "outlier downweigthing") to calculate Chi2, ndf and r.h.s. 'b' of
!! linear equation system A*x=b. In first iteration(s) fill global matrix A.
!!
!! For the filling of the global matrix each thread creates from his share of local fits
!! (small) udpdate matrices (\f$\Vek{\D C}_1+\Vek{\D C}_2\f$ from equations \ref eq-c1 "(15)",
!! \ref eq-c2 "(16)") stored in a write buffer. After all events in the read buffer
!! block have been processed the global matrix is being updated from the matrices in
!! the write buffer in parallel (each row by different thread).
!!
!! The matrices of the local fits are checked for bordered band structure.
!! For border size b and band width m all elements (i,j) are zero for
!! min(i,j)>b and abs(i-j)>m. For sufficient small (b,m) a solution by
!! \ref dbcdec "root free Cholesky decomposition" and
!! forward/backward substitution of the band part
!! is much faster compared to inversion (see broken lines in references).
!! Based on the expected computing cost the faster solution method is selected.
!!
!! \param [in,out]  nrej     number of rejected records
!! \param [in,out]  ndfs     sum(ndf)
!! \param [in,out]  sndf     sum(weighted ndf)
!! \param [in,out]  dchi2s   sum(weighted chi2)
!! \param [in]      numfil   number of binary files
!! \param [in,out]  naccf    number of accepted records per binary file
!! \param [in,out]  chi2f    sum(chi2/ndf) per binary file
!! \param [in,out]  ndff     sum(ndf) per binary file

SUBROUTINE loopbf(nrej,ndfs,sndf,dchi2s, numfil,naccf,chi2f,ndff)
    USE mpmod

    IMPLICIT NONE
    REAL(mpd) :: cauchy
    REAL(mps) :: chichi
    REAL(mps) :: chlimt
    REAL(mps) :: chndf
    REAL(mpd) :: chuber
    REAL(mpd) :: down
    REAL(mpr8) :: glder
    REAL(mpd) :: pull
    REAL(mpd) :: r1
    REAL(mpd) :: r2
    REAL(mps) :: rec
    REAL(mpd) :: rerr
    REAL(mpd) :: resid
    REAL(mps) :: resing
    REAL(mpd) :: resmax
    REAL(mpd) :: rmeas
    REAL(mpd) :: rmloc
    REAL(mpd) :: suwt
    REAL(mps) :: used
    REAL(mpd) :: wght
    REAL(mps) :: chindl
    INTEGER(mpi) :: i
    INTEGER(mpi) :: ia
    INTEGER(mpi) :: ib
    INTEGER(mpi) :: ibuf
    INTEGER(mpi) :: ichunk
    INTEGER(mpl) :: icmn
    INTEGER(mpl) :: icost
    INTEGER(mpi) :: id
    INTEGER(mpi) :: idiag
    INTEGER(mpi) :: iext
    INTEGER(mpi) :: ij
    INTEGER(mpi) :: ije
    INTEGER(mpi) :: ijn
    INTEGER(mpi) :: ijsym
    INTEGER(mpi) :: ik
    INTEGER(mpi) :: ike
    INTEGER(mpi) :: im
    INTEGER(mpi) :: imeas
    INTEGER(mpi) :: in
    INTEGER(mpi) :: inder
    INTEGER(mpi) :: inv
    INTEGER(mpi) :: ioffb
    INTEGER(mpi) :: ioffc
    INTEGER(mpi) :: ioffd
    INTEGER(mpi) :: ioffe
    INTEGER(mpi) :: ioffi
    INTEGER(mpi) :: iprdbg
    INTEGER(mpi) :: iproc
    INTEGER(mpi) :: irbin
    INTEGER(mpi) :: irow
    INTEGER(mpi) :: isfrst
    INTEGER(mpi) :: islast
    INTEGER(mpi) :: ist
    INTEGER(mpi) :: iter
    INTEGER(mpi) :: itgbi
    INTEGER(mpi) :: ivgbj
    INTEGER(mpi) :: ivgbk
    INTEGER(mpi) :: j
    INTEGER(mpi) :: ja
    INTEGER(mpi) :: jb
    INTEGER(mpi) :: jk
    INTEGER(mpi) :: jn
    INTEGER(mpi) :: joffd
    INTEGER(mpi) :: joffi
    INTEGER(mpi) :: jproc
    INTEGER(mpi) :: jsp
    INTEGER(mpi) :: k
    INTEGER(mpi) :: kbdr
    INTEGER(mpi) :: kbdrx
    INTEGER(mpi) :: kbnd
    INTEGER(mpi) :: kfl
    INTEGER(mpi) :: kx
    INTEGER(mpi) :: mbdr
    INTEGER(mpi) :: mbnd
    INTEGER(mpi) :: mside
    INTEGER(mpi) :: nalc
    INTEGER(mpi) :: nalg
    INTEGER(mpi) :: nan
    INTEGER(mpi) :: nb
    INTEGER(mpi) :: ndf
    INTEGER(mpi) :: ndfsd
    INTEGER(mpi) :: ndown
    INTEGER(mpi) :: neq
    INTEGER(mpi) :: nfred
    INTEGER(mpi) :: nfrei
    INTEGER(mpi) :: ngg
    INTEGER(mpi) :: nprdbg
    INTEGER(mpi) :: nrank
    INTEGER(mpi) :: nrc
    INTEGER(mpi) :: nst
    INTEGER(mpi) :: nter
    INTEGER(mpi) :: nweig

    INTEGER(mpi), INTENT(IN OUT)                     :: nrej(0:3)
    INTEGER(mpi), INTENT(IN OUT)                     :: ndfs
    REAL(mpd), INTENT(IN OUT)            :: sndf
    REAL(mpd), INTENT(IN OUT)            :: dchi2s
    INTEGER(mpi), INTENT(IN)                         :: numfil
    INTEGER(mpi), INTENT(IN OUT)                     :: naccf(numfil)
    REAL(mps), INTENT(IN OUT)                        :: chi2f(numfil)
    INTEGER(mpi), INTENT(IN OUT)                     :: ndff(numfil)

    REAL(mpd):: dchi2
    REAL(mpd)::dvar
    REAL(mpd):: dw1
    REAL(mpd)::dw2
    REAL(mpd)::summ

    !$    INTEGER(mpi) OMP_GET_THREAD_NUM

    LOGICAL:: lprnt
    LOGICAL::lhist
    CHARACTER (LEN=3):: chast
    DATA chuber/1.345_mpd/  ! constant for Huber down-weighting
    DATA cauchy/2.3849_mpd/ ! constant for Cauchy down-weighting
    SAVE chuber,cauchy
    !     ...
    ijsym(i,j)=MIN(i,j)+(MAX(i,j)*MAX(i,j)-MAX(i,j))/2
    isfrst(ibuf)=readBufferPointer(ibuf)+1
    islast(ibuf)=readBufferDataI(readBufferPointer(ibuf))
    inder(i)=readBufferDataI(i)
    glder(i)=readBufferDataD(i)

    ichunk=MIN((numReadBuffer+mthrd-1)/mthrd/32+1,256)
    ! reset header, 3 words per thread:
    !    number of entries, offset to data, indices
    writeBufferInfo=0
    writeBufferData=0.
    nprdbg=0
    iprdbg=-1

    ! parallelize record loop
    ! private copy of NDFS,.. for each thread, combined at end, init with 0.
    !$OMP  PARALLEL DO &
    !$OMP   DEFAULT(PRIVATE) &
    !$OMP   SHARED(numReadBuffer,readBufferPointer,readBufferDataI, &
    !$OMP      readBufferDataD,writeBufferHeader,writeBufferInfo, &
    !$OMP      writeBufferData,writeBufferIndices,writeBufferUpdates,globalVector,globalCounter, &
    !$OMP      globalParameter,globalParLabelIndex,globalIndexUsage,backIndexUsage, &
    !$OMP      measBins,numMeas,measIndex,measRes,measHists, &
    !$OMP      NAGB,NVGB,NAGBN,ICALCM,ICHUNK,NLOOPN,NRECER,NPRDBG,IPRDBG, &
    !$OMP      NEWITE,CHICUT,LHUBER,CHUBER,ITERAT,NRECPR,MTHRD, &
    !$OMP      DWCUT,CHHUGE,NRECP2,CAUCHY,LFITNP,LFITBB,IMONIT,IMONMD) &
    !$OMP   REDUCTION(+:NDFS,SNDF,DCHI2S,NREJ,NBNDR,NACCF,CHI2F,NDFF) &
    !$OMP   REDUCTION(MAX:NBNDX,NBDRX) &
    !$OMP   REDUCTION(MIN:NREC3) &
    !$OMP   SCHEDULE(DYNAMIC,ICHUNK)
    DO ibuf=1,numReadBuffer                       ! buffer for current record
        nrc=readBufferDataI(isfrst(ibuf)-2)       ! record
        kfl=NINT(readBufferDataD(isfrst(ibuf)-1),mpi) ! file
        dw1=REAL(readBufferDataD(isfrst(ibuf)-2),mpd) ! weight
        dw2=SQRT(dw1)
  
        iproc=0
        !$       IPROC=OMP_GET_THREAD_NUM()         ! thread number
        ioffb=nagb*iproc                                  ! offset 'f'.
        ioffc=nagbn*iproc                                 ! offset 'c'.
        ioffe=nvgb*iproc                                  ! offset 'e'
        ioffd=writeBufferHeader(-1)*iproc+writeBufferInfo(2,iproc+1)  ! offset data
        ioffi=writeBufferHeader(1)*iproc+writeBufferInfo(3,iproc+1)+2 ! offset indices
        !     ----- reset ------------------------------------------------------
        lprnt=.FALSE.
        lhist=(iproc == 0)
        REC=nrc            ! floating point value
        IF(nloopn == 1.AND.MOD(nrc,100000) == 0) THEN
            WRITE(*,*) 'Record',nrc,' ... still reading'
        END IF
  
        !      printout/debug only for one thread at a time
  
  
        !      flag for record printout -----------------------------------------
  
        lprnt=.FALSE.
        IF(newite.AND.(iterat == 1.OR.iterat == 3)) THEN
            IF(nrc == nrecpr) lprnt=.TRUE.
            IF(nrc == nrecp2) lprnt=.TRUE.
            IF(nrc == nrecer) lprnt=.TRUE.
        END IF
        IF (lprnt)THEN
            !$OMP ATOMIC
            nprdbg=nprdbg+1               ! number of threads with debug
            IF (nprdbg == 1) iprdbg=iproc ! first thread with debug
            IF (iproc /= iprdbg) lprnt=.FALSE.
        !         print *, ' LPRNT ', NRC, NPRDBG, IPRDBG, IPROC, LPRNT
        END IF
        IF(lprnt) THEN
            WRITE(1,*) ' '
            WRITE(1,*) '------------------ Loop',nloopn,  &
                ': Printout for record',nrc,iproc
            WRITE(1,*) ' '
        END IF
  
        !     ----- print data -------------------------------------------------
  
        IF(lprnt) THEN
            imeas=0              ! local derivatives
            ist=isfrst(ibuf)
            nst=islast(ibuf)
            DO ! loop over measurements
                CALL isjajb(nst,ist,ja,jb,jsp)
                IF(ja == 0) EXIT
                IF(imeas == 0) WRITE(1,1121)
                imeas=imeas+1
                WRITE(1,1122) imeas,glder(ja),glder(jb),  &
                    (inder(ja+j),glder(ja+j),j=1,jb-ja-1)
            END DO
1121        FORMAT(/'Measured value and local derivatives'/  &
                '  i measured std_dev  index...derivative ...')
1122        FORMAT(i3,2G12.4,3(i3,g12.4)/(27X,3(i3,g12.4)))
    
            imeas=0              ! global derivatives
            ist=isfrst(ibuf)
            nst=islast(ibuf)
            DO ! loop over measurements
                CALL isjajb(nst,ist,ja,jb,jsp)
                IF(ja == 0) EXIT
                IF(imeas == 0) WRITE(1,1123)
                imeas=imeas+1
                IF (jb < ist) THEN
                    IF(ist-jb > 2) THEN
                        WRITE(1,1124) imeas,(globalParLabelIndex(1,inder(jb+j)),inder(jb+j),  &
                            globalParLabelIndex(2,inder(jb+j)),glder(jb+j),j=1,ist-jb)
                    ELSE
                        WRITE(1,1125) imeas,(globalParLabelIndex(1,inder(jb+j)),inder(jb+j),  &
                            globalParLabelIndex(2,inder(jb+j)),glder(jb+j),j=1,ist-jb)
                    END IF
                END IF
            END DO
1123        FORMAT(/'Global derivatives'/  &
                '  i  label gindex vindex derivative ...')
1124        FORMAT(i3,2(i9,i7,i7,g12.4)/(3X,2(i9,i7,i7,g12.4)))
1125        FORMAT(i3,2(i9,i7,i7,g12.4))
        END IF
  
        !      ----- first loop -------------------------------------------------
        !       ------ prepare local fit ------
        !      count local and global derivates
        !      subtract actual alignment parameters from the measured data
  
        IF(lprnt) THEN
            WRITE(1,*) ' '
            WRITE(1,*) 'Data corrections using values of global parameters'
            WRITE(1,*) '=================================================='
            WRITE(1,101)
        END IF
        nalg=0                         ! count number of global derivatives
        nalc=0                         ! count number of local derivatives
        neq=0                          ! count number of equations
        ist=isfrst(ibuf)
        nst=islast(ibuf)
        DO ! loop over measurements
            CALL isjajb(nst,ist,ja,jb,jsp)
            IF(ja == 0) EXIT
            rmeas=REAL(glder(ja),mpd)     ! data
            neq=neq+1                     ! count equation
            !         subtract global ... from measured value
            DO j=1,ist-jb                 ! global parameter loop
                itgbi=inder(jb+j)            ! global parameter label
                rmeas=rmeas-REAL(glder(jb+j),mpd)*globalParameter(itgbi) ! subtract   !!! reversed
                IF (icalcm == 1) THEN
                    ij=globalParLabelIndex(2,itgbi)         ! index of variable global parameter
                    IF(ij > 0) THEN
                        ijn=backIndexUsage(ioffe+ij)        ! get index of index
                        IF(ijn == 0) THEN                   ! not yet included
                            nalg=nalg+1                     ! count
                            globalIndexUsage(ioffc+nalg)=ij ! store global index
                            backIndexUsage(ioffe+ij)=nalg   ! store back index
                        END IF
                    END IF
                END IF
            END DO
            IF(lprnt) THEN
                IF (jb < ist) WRITE(1,102) neq,glder(ja),rmeas,glder(jb)
            END IF
            readBufferDataD(ja)=REAL(rmeas,mpr8)   ! global contribution subtracted
            DO j=1,jb-ja-1              ! local parameter loop
                ij=inder(ja+j)
                nalc=MAX(nalc,ij)       ! number of local parameters
            END DO
        END DO
101     FORMAT(' index measvalue   corrvalue          sigma')
102     FORMAT(i6,2X,2G12.4,' +-',g12.4)
  
        IF(nalc <= 0) GO TO 90
  
        ngg=(nalg*nalg+nalg)/2
        IF (icalcm == 1) THEN
            DO k=1,nalg*nalc
                localGlobalMatrix(k)=0.0_mpd ! reset global-local matrix
            END DO
            writeBufferIndices(ioffi-1)=nrc       ! index header:
            writeBufferIndices(ioffi  )=nalg      ! event number, number of global par
            CALL sort1k(globalIndexUsage(ioffc+1),nalg) ! sort global par.
            DO k=1,nalg
                iext=globalIndexUsage(ioffc+k)
                writeBufferIndices(ioffi+k)=iext    ! global par indices
                backIndexUsage(ioffe+iext)=k    ! update back index
            END DO
            DO k=1,ngg
                writeBufferUpdates(ioffd+k)=0.0_mpd ! reset global-global matrix
            END DO
        END IF
        !      ----- iteration start and check ---------------------------------
  
        nter=1                         ! first loop without down-weighting
        IF(nloopn /= 1.AND.lhuber /= 0) nter=lhuber
        localCorrections(1:neq) = 0._mpd
  
        !      check matrix for bordered band structure (MBDR+MBND+1 <= NALC)
        mbnd=-1
        mbdr=nalc
        mside=-1 ! side (1: upper/left border, 2: lower/right border)
        DO i=1, 2*nalc
            ibandh(i)=0
        END DO
        irow=1
        idiag=1
        ndfsd=0
  
        iter=0
        resmax=0.0
        DO WHILE(iter < nter)  ! outlier suppresssion iteration loop
            iter=iter+1
            resmax=0.0
            IF(lprnt) THEN
                WRITE(1,*) ' '
                WRITE(1,*) 'Outlier-suppression iteration',iter,' of',nter
                WRITE(1,*) '=========================================='
                WRITE(1,*) ' '
                imeas=0
            END IF
  
            !      ----- second loop ------------------------------------------------
            !      accumulate normal equations for local fit and determine solution
            DO i=1,nalc
                blvec(i)=0.0_mpd                  ! reset vector
            END DO
            DO i=1,(nalc*nalc+nalc)/2 ! GF: FIXME - not really, local parameter number...
                clmat(i)=0.0_mpd               ! (p)reset matrix
            END DO
            neq=0
            ndown=0
            nweig=0
            ist=isfrst(ibuf)
            nst=islast(ibuf)
            DO ! loop over measurements
                CALL isjajb(nst,ist,ja,jb,jsp)
                IF(ja == 0) EXIT
                rmeas=REAL(glder(ja),mpd)     ! data
                rerr =REAL(glder(jb),mpd)     ! ... and the error
                wght =1.0_mpd/rerr**2         ! weight from error
                neq=neq+1                     ! count equation
                nweig=nweig+1
                resid=rmeas-localCorrections(neq)           ! subtract previous fit
                IF(nloopn /= 1.AND.iter /= 1.AND.lhuber /= 0) THEN
                    IF(iter <= 3) THEN
                        IF(ABS(resid) > chuber*rerr) THEN     ! down-weighting
                            wght=wght*chuber*rerr/ABS(resid)
                            ndown=ndown+1
                        END IF
                    ELSE       ! Cauchy
                        wght=wght/(1.0+(resid/rerr/cauchy)**2)
                    END IF
                END IF

                IF(lprnt.AND.iter /= 1.AND.nter /= 1) THEN
                    chast='   '
                    IF(ABS(resid) > chuber*rerr) chast='*  '
                    IF(ABS(resid) > 3.0*rerr) chast='** '
                    IF(ABS(resid) > 6.0*rerr) chast='***'
                    IF(imeas == 0) WRITE(1,*) 'Second loop: accumulate'
                    IF(imeas == 0) WRITE(1,103)
                    imeas=imeas+1
                    down=1.0/SQRT(wght)
                    r1=resid/rerr
                    r2=resid/down
                    WRITE(1,104) imeas,rmeas,resid,rerr,r1,chast,r2
                END IF
103             FORMAT(' index corrvalue    residuum          sigma',  &
                    '     nresid     cnresid')
104             FORMAT(i6,2X,2G12.4,' +-',g12.4,f7.2,1X,a3,f8.2)
    
                DO j=1,jb-ja-1 ! normal equations, local parameter loop
                    ij=inder(ja+j)          ! local parameter index J
                    blvec(ij)=blvec(ij)+wght*rmeas*REAL(glder(ja+j),mpd)
                    DO k=1,j
                        ik=inder(ja+k)         ! local parameter index K
                        jk=ijsym(ij,ik)        ! index in symmetric matrix
                        clmat(jk)=clmat(jk) &  ! force double precision
                            +wght*REAL(glder(ja+j),mpd)*REAL(glder(ja+k),mpd)
                        !           check for band matrix substructure
                        IF (iter == 1) THEN
                            id=IABS(ij-ik)+1
                            im=MIN(ij,ik) ! upper/left border
                            ibandh(id)=MAX(ibandh(id),im)
                            im=MIN(nalc+1-ij,nalc+1-ik) ! lower/rght border (mirrored)
                            ibandh(nalc+id)=MAX(ibandh(nalc+id),im)
                        END IF
                    END DO
                END DO
            END DO
            !      for non trivial fits check for bordered band matrix structure
            IF (iter == 1.AND.nalc > 5.AND.lfitbb > 0) THEN
                kx=-1
                kbdrx=0
                icmn=INT(nalc,mpl)**3 ! cost (*6) should improve by at least factor 2
                ! upper/left border ?
                kbdr=0  
                DO k=nalc,2,-1
                    kbnd=k-2
                    kbdr=MAX(kbdr,ibandh(k))
                    icost=6*INT(nalc-kbdr,mpl)*INT(kbnd+kbdr+1,mpl)**2+2*INT(kbdr,mpl)**3
                    IF (icost < icmn) THEN
                        icmn=icost
                        kx=k
                        kbdrx=kbdr
                        mside=1
                    END IF
                END DO    
                IF (kx < 0) THEN
                    ! lower/right border instead?
                    kbdr=0  
                    DO k=nalc,2,-1
                        kbnd=k-2
                        kbdr=MAX(kbdr,ibandh(k+nalc))
                        icost=6*INT(nalc-kbdr,mpl)*INT(kbnd+kbdr+1,mpl)**2+2*INT(kbdr,mpl)**3
                        IF (icost < icmn) THEN
                            icmn=icost
                            kx=k
                            kbdrx=kbdr
                            mside=2
                        END IF
                    END DO
                END IF
                IF (kx > 0) THEN
                    mbnd=kx-2
                    mbdr=kbdrx
                END IF
            END IF
  
            IF (mbnd >= 0) THEN
                !      fast solution for border banded matrix (inverse for ICALCM>0)
                IF (nloopn == 1) THEN
                    nbndr(mside)=nbndr(mside)+1
                    nbdrx=MAX(nbdrx,mbdr)
                    nbndx=MAX(nbndx,mbnd)
                END IF

                inv=0
                IF (nloopn <= lfitnp.AND.iter == 1) inv=1 ! band part of inverse (for pulls)
                IF (icalcm == 1.OR.lprnt) inv=2     ! complete inverse
                IF (mside == 1) THEN
                    CALL sqmibb(clmat,blvec,nalc,mbdr,mbnd,inv,nrank,  &
                        vbnd,vbdr,aux,vbk,vzru,scdiag,scflag)
                ELSE
                    CALL sqmibb2(clmat,blvec,nalc,mbdr,mbnd,inv,nrank,  &
                        vbnd,vbdr,aux,vbk,vzru,scdiag,scflag)
                ENDIF        
            ELSE
                !      full inversion and solution
                inv=2
                CALL sqminv(clmat,blvec,nalc,nrank,scdiag,scflag)
            END IF
            !      check for NaNs
            nan=0
            DO k=1, nalc
                IF ((.NOT.(blvec(k) <= 0.0_mpd)).AND. (.NOT.(blvec(k) > 0.0_mpd))) nan=nan+1
            END DO

            IF(lprnt) THEN
                WRITE(1,*) ' '
                WRITE(1,*) 'Parameter determination:',nalc,' parameters,', ' rank=',nrank
                WRITE(1,*) '-----------------------'
                IF(ndown /= 0) WRITE(1,*) '   ',ndown,' data down-weighted'
                WRITE(1,*) ' '
            END IF
  
            !      ----- third loop -------------------------------------------------
            !      calculate single residuals remaining after local fit and chi^2
  
            summ=0.0_mpd
            suwt=0.0
            neq=0
            imeas=0
            ist=isfrst(ibuf)
            nst=islast(ibuf)
            DO ! loop over measurements
                CALL isjajb(nst,ist,ja,jb,jsp)
                IF(ja == 0) EXIT
                rmeas=REAL(glder(ja),mpd)     ! data (global contrib. subtracted)
                rerr =REAL(glder(jb),mpd)     ! ... and the error
                wght =1.0_mpd/rerr**2         ! weight from error
                neq=neq+1                     ! count equation
                rmloc=0.0                     ! local fit result reset
                DO j=1,jb-ja-1                ! local parameter loop
                    ij=inder(ja+j)
                    rmloc=rmloc+REAL(glder(ja+j),mpd)*blvec(ij) ! local fit result
                END DO
                localCorrections(neq)=rmloc   ! save local fit result
                rmeas=rmeas-rmloc             ! reduced to residual
    
                !         calculate pulls? (needs covariance matrix)
                IF(iter == 1.AND.inv > 0.AND.nloopn <= lfitnp) THEN
                    dvar=0.0_mpd
                    DO j=1,jb-ja-1
                        ij=inder(ja+j)
                        DO k=1,jb-ja-1
                            ik=inder(ja+k)
                            jk=ijsym(ij,ik)
                            dvar=dvar+clmat(jk)*REAL(glder(ja+j),mpd)*REAL(glder(ja+k),mpd)
                        END DO
                    END DO
                    !          some variance left to define a pull?
                    IF (0.999999_mpd/wght > dvar) THEN
                        pull=rmeas/SQRT(1.0_mpd/wght-dvar)
                        IF (lhist) THEN
                            IF (jb < ist) THEN
                                CALL hmpent(13,REAL(pull,mps)) ! histogram pull
                                CALL gmpms(5,REC,REAL(pull,mps))
                            ELSE
                                CALL hmpent(14,REAL(pull,mps)) ! histogram pull
                            END IF
                        END IF
                        !  monitoring
                        IF (imonit /= 0) THEN
                            IF (jb < ist) THEN
                                ij=inder(jb+1) ! group by first global label
                                if (imonmd == 0) THEN
                                    irbin=MIN(measBins,max(1,INT(pull*rerr/measRes(ij)/measBinSize+0.5*REAL(measBins,mpd))))
                                ELSE    
                                    irbin=MIN(measBins,max(1,INT(pull/measBinSize+0.5*REAL(measBins,mpd))))
                                ENDIF
                                irbin=irbin+measBins*(measIndex(ij)-1+numMeas*iproc)
                                measHists(irbin)=measHists(irbin)+1
                            ENDIF
                        ENDIF
                    END IF
                END IF
    
                IF(iter == 1.AND.jb < ist.AND.lhist)  &
                    CALL gmpms(4,REC,REAL(rmeas/rerr,mps)) ! residual (with global deriv.)
    
                dchi2=wght*rmeas*rmeas
                !          DCHIT=DCHI2
                resid=rmeas
                IF(nloopn /= 1.AND.iter /= 1.AND.lhuber /= 0) THEN
                    IF(iter <= 3) THEN
                        IF(ABS(resid) > chuber*rerr) THEN     ! down-weighting
                            wght=wght*chuber*rerr/ABS(resid)
                            dchi2=2.0*chuber*(ABS(resid)/rerr-0.5*chuber)
                        END IF
                    ELSE
                        wght=wght/(1.0_mpd+(resid/rerr/cauchy)**2)
                        dchi2=LOG(1.0_mpd+(resid/rerr/cauchy)**2)*cauchy**2
                    END IF
                END IF
    
                down=1.0/SQRT(wght)

                !          SUWT=SUWT+DCHI2/DCHIT
                suwt=suwt+rerr/down
                IF(lprnt) THEN
                    chast='   '
                    IF(ABS(resid) > chuber*rerr) chast='*  '
                    IF(ABS(resid) > 3.0*rerr) chast='** '
                    IF(ABS(resid) > 6.0*rerr) chast='***'
                    IF(imeas == 0) WRITE(1,*) 'Third loop: single residuals'
                    IF(imeas == 0) WRITE(1,105)
                    imeas=imeas+1
                    r1=resid/rerr
                    r2=resid/down
                    IF(resid < 0.0) r1=-r1
                    IF(resid < 0.0) r2=-r2
                    WRITE(1,106) imeas,glder(ja),rmeas,rerr,r1,chast,r2
                END IF
105             FORMAT(' index corrvalue    residuum          sigma',  &
                    '     nresid     cnresid')
106             FORMAT(i6,2X,2G12.4,' +-',g12.4,f7.2,1X,a3,f8.2)

                IF(iter == nter) THEN
                    readBufferDataD(ja)=REAL(rmeas,mpr8) ! store remaining residual
                    resmax=MAX(resmax,ABS(rmeas)/rerr)
                END IF

                IF(iter == 1.AND.lhist) THEN
                    IF (jb < ist) THEN
                        CALL hmpent( 3,REAL(rmeas/rerr,mps)) ! histogram norm residual
                    ELSE
                        CALL hmpent(12,REAL(rmeas/rerr,mps)) ! histogram norm residual
                    END IF
                END IF
                summ=summ+dchi2        ! accumulate chi-square sum
            END DO
            ndf=neq-nrank
            resing=(REAL(nweig,mps)-REAL(suwt,mps))/REAL(nweig,mps)
            IF (lhist) THEN
                IF(iter == 1) CALL hmpent( 5,REAL(ndf,mps))  ! histogram Ndf
                IF(iter == 1) CALL hmpent(11,REAL(nalc,mps)) ! histogram Nlocal
                IF(nloopn == 2.AND.iter == nter) CALL hmpent(6,resing)
            END IF
            IF(lprnt) THEN
                WRITE(1,*) ' '
                WRITE(1,*) 'Chi^2=',summ,' at',ndf,' degrees of freedom: ',  &
                    '3-sigma limit is',chindl(3,ndf)*REAL(ndf,mps)
                WRITE(1,*) suwt,' is sum of factors, compared to',nweig,  &
                    ' Downweight fraction:',resing
            END IF
            IF(nrank /= nalc.OR.nan > 0) THEN
                nrej(0)=nrej(0)+1         ! count cases
                IF (nrec3 == huge(nrec3)) nrec3=nrc
                IF(lprnt) THEN
                    WRITE(1,*) ' rank deficit/NaN ', nalc, nrank, nan
                    WRITE(1,*) '   ---> rejected!'
                END IF
                GO TO 90
            END IF
            IF(ndf <= 0) THEN
                nrej(1)=nrej(1)+1         ! count cases
                IF(lprnt) THEN
                    WRITE(1,*) '   ---> rejected!'
                END IF
                GO TO 90
            END IF
  
            chndf=REAL(summ/REAL(ndf,mpd),mps)
  
            IF(iter == 1.AND.lhist) CALL hmpent(4,chndf) ! histogram chi^2/Ndf
        END DO  ! outlier iteration loop
  
        ndfs=ndfs+ndf              ! (local) sum of Ndf
        sndf=sndf+REAL(ndf,mpd)*dw1  ! (local) weighted sum of Ndf
  
        !      ----- reject eventually ------------------------------------------
  
        IF(newite.AND.iterat == 2) THEN ! find record with largest Chi^2/Ndf
            IF(nrecp2 < 0.AND.chndf > writeBufferData(2,iproc+1)) THEN
                writeBufferData(2,iproc+1)=chndf
                writeBufferInfo(7,iproc+1)=nrc
            END IF
        END IF
  
        chichi=chindl(3,ndf)*REAL(ndf,mps)
        ! GF       IF(SUMM.GT.50.0*CHICHI) THEN ! huge
        ! CHK CHICUT<0: NO cut (1st iteration)
        IF(chicut >= 0.0) THEN
            IF(summ > chhuge*chichi) THEN ! huge
                nrej(2)=nrej(2)+1    ! count cases with huge chi^2
                IF(lprnt) THEN
                    WRITE(1,*) '   ---> rejected!'
                END IF
                GO TO 90
            END IF

            IF(chicut > 0.0) THEN
                chlimt=chicut*chichi
                !          WRITE(*,*) 'chi^2 ',SUMM,CHLIMT,CHICUT,CHINDL(3,NDF),NDF
                IF(summ > chlimt) THEN
                    IF(lprnt) THEN
                        WRITE(1,*) '   ---> rejected!'
                    END IF
                    !              add to FVALUE
                    dchi2=chlimt               ! total contribution limit
                    dchi2s=dchi2s+dchi2*dw1    ! add total contribution
                    nrej(3)=nrej(3)+1      ! count cases with large chi^2
                    GO TO 90
                END IF
            END IF
        END IF 
  
        IF(lhuber > 1.AND.dwcut /= 0.0.AND.resing > dwcut) THEN
            !         add to FVALUE
            dchi2=summ                 ! total contribution
            dchi2s=dchi2s+dchi2*dw1    ! add total contribution
            nrej(3)=nrej(3)+1      ! count cases with large chi^2
            !          WRITE(*,*) 'Downweight fraction cut ',RESING,DWCUT,SUMM
            IF(lprnt) THEN
                WRITE(1,*) '   ---> rejected!'
            END IF
            GO TO 90
        END IF
  
        IF(newite.AND.iterat == 2) THEN ! find record with largest residual
            IF(nrecpr < 0.AND.resmax > writeBufferData(1,iproc+1)) THEN
                writeBufferData(1,iproc+1)=REAL(resmax,mps)
                writeBufferInfo(6,iproc+1)=nrc
            END IF
        END IF
        !      'track quality' per binary file: accepted records
        naccf(kfl)=naccf(kfl)+1
        ndff(kfl) =ndff(kfl) +ndf
        chi2f(kfl)=chi2f(kfl)+chndf
  
        !      ----- fourth loop ------------------------------------------------
        !      update of global matrix and vector according to the "Millepede"
        !      principle, from the global/local information
    
        ist=isfrst(ibuf)
        nst=islast(ibuf)
        DO ! loop over measurements
            CALL isjajb(nst,ist,ja,jb,jsp)
            IF(ja <= 0) EXIT
    
            rmeas=REAL(glder(ja),mpd)     ! data residual
            rerr =REAL(glder(jb),mpd)     ! ... and the error
            wght =1.0_mpd/rerr**2         ! weight from measurement error
            dchi2=wght*rmeas*rmeas        ! least-square contribution
    
            IF(nloopn /= 1.AND.lhuber /= 0) THEN       ! check residual
                resid=ABS(rmeas)
                IF(resid > chuber*rerr) THEN
                    wght=wght*chuber*rerr/resid          ! down-weighting
                    dchi2=2.0*chuber*(resid/rerr-0.5*chuber) ! modified contribution
                END IF
            END IF
            dchi2s=dchi2s+dchi2*dw1    ! add to total objective function
    
            !         global-global matrix contribution: add directly to gg-matrix
    
            DO j=1,ist-jb
                ivgbj=globalParLabelIndex(2,inder(jb+j))     ! variable-parameter index
                IF(ivgbj > 0) THEN
                    globalVector(ioffb+ivgbj)=globalVector(ioffb+ivgbj)  &
                        +dw1*wght*rmeas*REAL(glder(jb+j),mpd) ! vector  !!! reverse
                    globalCounter(ioffb+ivgbj)=globalCounter(ioffb+ivgbj)+1    
                    IF(icalcm == 1) THEN
                        ije=backIndexUsage(ioffe+ivgbj)        ! get index of index, non-zero
                        DO k=1,j
                            ivgbk=globalParLabelIndex(2,inder(jb+k))
                            IF(ivgbk > 0) THEN
                                ike=backIndexUsage(ioffe+ivgbk)        ! get index of index, non-zero
                                ia=MAX(ije,ike)          ! larger
                                ib=MIN(ije,ike)          ! smaller
                                ij=ib+(ia*ia-ia)/2
                                writeBufferUpdates(ioffd+ij)=writeBufferUpdates(ioffd+ij)  &
                                    -dw1*wght*REAL(glder(jb+j),mpd)*REAL(glder(jb+k),mpd)
                            END IF
                        END DO
                    END IF
                END IF
            END DO

            !         normal equations - rectangular matrix for global/local pars
            !         global-local matrix contribution: accumulate rectangular matrix
            IF (icalcm /= 1) CYCLE
            DO j=1,ist-jb
                ivgbj=globalParLabelIndex(2,inder(jb+j))           ! variable-parameter index
                IF(ivgbj > 0) THEN
                    ije=backIndexUsage(ioffe+ivgbj)        ! get index of index, non-zero
                    DO k=1,jb-ja-1
                        ik=inder(ja+k)           ! local index
                        jk=ik+(ije-1)*nalc       ! matrix index
                        localGlobalMatrix(jk)=localGlobalMatrix(jk)+dw2*wght*REAL(glder(jb+j),mpd)*REAL(glder(ja+k),mpd)
                    END DO
                END IF
            END DO
        END DO
  
  
        !      ----- final matrix update ----------------------------------------
        !      update global matrices and vectors
        IF(icalcm /= 1) GO TO 90 ! matrix update
        !      (inverse local matrix) * (rectang. matrix) -> CORM
        !                                        T
        !      resulting symmetrix matrix  =   G   *   Gamma^{-1}   *   G
  
        CALL dbavat(clmat,localGlobalMatrix,writeBufferUpdates(ioffd+1),nalc,-nalg)
  
        !      (rectang. matrix) * (local param vector)   -> CORV
        !      resulting vector = G * q (q = local parameter)
        !      CALL DBGAX(DQ(IGLMA/2+1),BLVEC,DQ(ICORV/2+1),NALG,NALC)  ! not done
        !      the vector update is not done, because after local fit it is zero!

        !      update cache status
        writeBufferInfo(1,iproc+1)=writeBufferInfo(1,iproc+1)+1
        writeBufferInfo(2,iproc+1)=writeBufferInfo(2,iproc+1)+ngg
        writeBufferInfo(3,iproc+1)=writeBufferInfo(3,iproc+1)+nalg+2
        !      check free space
        nfred=writeBufferHeader(-1)-writeBufferInfo(2,iproc+1)-writeBufferHeader(-2)
        nfrei=writeBufferHeader(1)-writeBufferInfo(3,iproc+1)-writeBufferHeader(2)
        IF (nfred < 0.OR.nfrei < 0) THEN ! need to flush
            nb=writeBufferInfo(1,iproc+1)
            joffd=writeBufferHeader(-1)*iproc  ! offset data
            joffi=writeBufferHeader(1)*iproc+2 ! offset indices
            used=REAL(writeBufferInfo(2,iproc+1),mps)/REAL(writeBufferHeader(-1),mps)
            writeBufferInfo(4,iproc+1)=writeBufferInfo(4,iproc+1) +NINT(1000.0*used,mpi)
            used=REAL(writeBufferInfo(3,iproc+1),mps)/REAL(writeBufferHeader(1),mps)
            writeBufferInfo(5,iproc+1)=writeBufferInfo(5,iproc+1) +NINT(1000.0*used,mpi)
            !$OMP CRITICAL
            writeBufferHeader(-4)=writeBufferHeader(-4)+1
            writeBufferHeader(4)=writeBufferHeader(4)+1
    
            DO ib=1,nb
                ijn=0
                DO in=1,writeBufferIndices(joffi)
                    i=writeBufferIndices(joffi+in)
                    !         DQ(IGVEC/2+I)=DQ(IGVEC/2+I)+DQ(ICORV/2+IN)  ! not done: = zero
                    DO jn=1,in
                        ijn=ijn+1
                        j=writeBufferIndices(joffi+jn)
                        CALL mupdat(i,j,-writeBufferUpdates(joffd+ijn))  ! matrix update
                    END DO
                END DO
                joffd=joffd+ijn
                joffi=joffi+writeBufferIndices(joffi)+2
            END DO
            !$OMP END CRITICAL
            !       reset counter, pointers
            DO k=1,3
                writeBufferInfo(k,iproc+1)=0
            END DO
        END IF

90      IF(lprnt) THEN
            WRITE(1,*) ' '
            WRITE(1,*) '------------------ End of printout for record',nrc
            WRITE(1,*) ' '
        END IF
  
        DO i=1,nalg                 ! reset global index array
            iext=globalIndexUsage(ioffc+i)
            backIndexUsage(ioffe+iext)=0
        END DO
  
    END DO
    !$OMP END PARALLEL DO

    IF (icalcm == 1) THEN
        !     flush remaining matrices
        DO k=1,mthrd ! update statistics
            writeBufferHeader(-3)=writeBufferHeader(-3)+1
            used=REAL(writeBufferInfo(2,k),mps)/REAL(writeBufferHeader(-1),mps)
            writeBufferInfo(4,k)=writeBufferInfo(4,k)+NINT(1000.0*used,mpi)
            writeBufferHeader(-5)=writeBufferHeader(-5)+writeBufferInfo(4,k)
            writeBufferHeader(-6)=MAX(writeBufferHeader(-6),writeBufferInfo(4,k))
            writeBufferInfo(4,k)=0
            writeBufferHeader(3)=writeBufferHeader(3)+1
            used=REAL(writeBufferInfo(3,k),mps)/REAL(writeBufferHeader(1),mps)
            writeBufferInfo(5,k)=writeBufferInfo(5,k)+NINT(1000.0*used,mpi)
            writeBufferHeader(5)=writeBufferHeader(5)+writeBufferInfo(5,k)
            writeBufferHeader(6)=MAX(writeBufferHeader(6),writeBufferInfo(5,k))
            writeBufferInfo(5,k)=0
        END DO
  
        !$OMP  PARALLEL &
        !$OMP  DEFAULT(PRIVATE) &
        !$OMP  SHARED(writeBufferHeader,writeBufferInfo,writeBufferIndices,writeBufferUpdates,MTHRD)
        iproc=0
        !$ IPROC=OMP_GET_THREAD_NUM()         ! thread number
        DO jproc=0,mthrd-1
            nb=writeBufferInfo(1,jproc+1)
            !        print *, ' flush end ', JPROC, NRC, NB
            joffd=writeBufferHeader(-1)*jproc  ! offset data
            joffi=writeBufferHeader(1)*jproc+2 ! offset indices
            DO ib=1,nb
                !         print *, '   buf end ', JPROC,IB,writeBufferIndices(JOFFI-1),writeBufferIndices(JOFFI)
                ijn=0
                DO in=1,writeBufferIndices(joffi)
                    i=writeBufferIndices(joffi+in)
                    !$        IF (MOD(I,MTHRD).EQ.IPROC) THEN
                    DO jn=1,in
                        ijn=ijn+1
                        j=writeBufferIndices(joffi+jn)
                        CALL mupdat(i,j,-writeBufferUpdates(joffd+ijn))  ! matrix update
                    END DO
                !$        ELSE
                !$          IJN=IJN+IN
                !$        ENDIF
                END DO
                joffd=joffd+ijn
                joffi=joffi+writeBufferIndices(joffi)+2
            END DO
        END DO
    !$OMP END PARALLEL
    END IF

    IF(newite.AND.iterat == 2) THEN ! get worst records (for printrecord -1 -1)
        IF (nrecpr < 0) THEN
            DO k=1,mthrd
                IF (writeBufferData(1,k) > value1) THEN
                    value1=writeBufferData(1,k)
                    nrec1 =writeBufferInfo(6,k)
                END IF
            END DO
        END IF
        IF (nrecp2 < 0) THEN
            DO k=1,mthrd
                IF (writeBufferData(2,k) > value2) THEN
                    value2=writeBufferData(2,k)
                    nrec2 =writeBufferInfo(7,k)
                END IF
            END DO
        END IF
    END IF

END SUBROUTINE loopbf




!***********************************************************************

!> Print final log file
!!
!! For each global parameter:
!! - label (I10)
!! - parameter value (G14.5)
!! - presigma (G14.5)
!! - difference of parameters values (G14.5)
!! - difference at last iteration (G14.5)
!! - error (standard deviation) (G14.5)
!! - global correlation (F8.3), on request only
!! - Entries from binary files or during iterations
!!
SUBROUTINE prtglo
    USE mpmod

    IMPLICIT NONE
    REAL(mps):: dpa
    REAL(mps):: err
    REAL(mps):: gcor
    INTEGER(mpi) :: i
    INTEGER(mpi) :: icount
    INTEGER(mpi) :: ie
    INTEGER(mpi) :: iev
    INTEGER(mpi) :: ij
    INTEGER(mpi) :: imin
    INTEGER(mpi) :: iprlim
    INTEGER(mpi) :: isub
    INTEGER(mpi) :: itgbi
    INTEGER(mpi) :: itgbl
    INTEGER(mpi) :: ivgbi
    INTEGER(mpi) :: j
    INTEGER(mpi) :: label
    INTEGER(mpi) :: lup
    REAL(mps):: par

    REAL(mpd):: diag
    REAL(mpd)::gmati
    REAL(mpd)::gcor2
    INTEGER(mpi) :: labele(3)
    INTEGER(mpl):: ii
    REAL(mps):: compnt(3)
    SAVE
    !     ...

    lup=09
    CALL mvopen(lup,'millepede.res')

    WRITE(*,*) ' '
    WRITE(*,*) '         Result of fit for global parameters'
    WRITE(*,*) '         ==================================='
    WRITE(*,*) ' '

    WRITE(*,101)

    WRITE(lup,*) 'Parameter   ! first 3 elements per line are',  &
        ' significant (if used as input)'


    iprlim=10
    DO itgbi=1,ntgb  ! all parameter variables
        itgbl=globalParLabelIndex(1,itgbi)
        ivgbi=globalParLabelIndex(2,itgbi)
        par=REAL(globalParameter(itgbi),mps)      ! initial value
        icount=0 ! counts
        IF(ivgbi > 0) THEN
            icount=globalCounter(ivgbi) ! used in last iteration
            dpa=REAL(globalParameter(itgbi)-globalParStart(itgbi),mps)       ! difference
            IF(metsol == 1.OR.metsol == 2) THEN
                ii=ivgbi
                ii=(ii*ii+ii)/2
                gmati=globalMatD(ii)
                ERR=SQRT(ABS(REAL(gmati,mps)))
                IF(gmati < 0.0_mpd) ERR=-ERR
                diag=workspaceDiag(ivgbi)
                gcor=-1.0
                IF(gmati*diag > 0.0_mpd) THEN   ! global correlation
                    gcor2=1.0_mpd-1.0_mpd/(gmati*diag)
                    IF(gcor2 >= 0.0_mpd.AND.gcor2 <= 1.0_mpd) gcor=REAL(SQRT(gcor2),mps)
                END IF
            END IF
        END IF
        IF(ipcntr > 1) icount=globalParCounts(itgbi) ! from binary files 
        IF(itgbi <= iprlim) THEN
            IF(ivgbi <= 0) THEN
                WRITE(*  ,102) itgbl,par,REAL(globalParPreSigma(itgbi),mps)
            ELSE
                IF(metsol == 1.OR.metsol == 2) THEN
                    IF (igcorr == 0) THEN
                        WRITE(*,102) itgbl,par,REAL(globalParPreSigma(itgbi),mps),dpa,ERR
                    ELSE
                        WRITE(*,102) itgbl,par,REAL(globalParPreSigma(itgbi),mps),dpa,ERR,gcor
                    END IF
                ELSE
                    WRITE(*,102) itgbl,par,REAL(globalParPreSigma(itgbi),mps),dpa
                END IF
            END IF
        ELSE IF(itgbi == iprlim+1) THEN
            WRITE(*  ,*) '... (further printout suppressed, but see log file)'
        END IF

        !      file output
        IF(ivgbi <= 0) THEN
            IF (ipcntr /= 0) THEN
                WRITE(lup,110) itgbl,par,REAL(globalParPreSigma(itgbi),mps),icount
            ELSE
                WRITE(lup,102) itgbl,par,REAL(globalParPreSigma(itgbi),mps)
            END IF               
        ELSE
            IF(metsol == 1.OR.metsol == 2) THEN
                IF (ipcntr /= 0) THEN
                    WRITE(lup,112) itgbl,par,REAL(globalParPreSigma(itgbi),mps),dpa,ERR,icount            
                ELSE IF (igcorr /= 0) THEN
                    WRITE(lup,102) itgbl,par,REAL(globalParPreSigma(itgbi),mps),dpa,ERR,gcor
                ELSE
                    WRITE(lup,102) itgbl,par,REAL(globalParPreSigma(itgbi),mps),dpa,ERR
                END IF
            ELSE
                IF (ipcntr /= 0) THEN
                    WRITE(lup,111) itgbl,par,REAL(globalParPreSigma(itgbi),mps),dpa,icount
                ELSE
                    WRITE(lup,102) itgbl,par,REAL(globalParPreSigma(itgbi),mps),dpa
                END IF    
            END IF
        END IF
    END DO
    REWIND lup
    CLOSE(UNIT=lup)

    IF(metsol == 2) THEN        ! diagonalisation: write eigenvectors
        CALL mvopen(lup,'millepede.eve')
        imin=1
        DO i=nagb,1,-1
            IF(workspaceEigenValues(i) > 0.0_mpd) THEN
                imin=i          ! index of smallest pos. eigenvalue
                EXIT
            ENDIF
        END DO
        iev=0
  
        DO isub=0,MIN(15,imin-1)
            IF(isub < 10) THEN
                i=imin-isub
            ELSE
                i=isub-9
            END IF
    
            !        DO I=IMIN,MAX(1,IMIN-9),-1    ! backward loop, up to 10 vectors
            WRITE(*,*) 'Eigenvector ',i,' with eigenvalue',workspaceEigenValues(i)
            WRITE(lup,*) 'Eigenvector ',i,' with eigenvalue',workspaceEigenValues(i)
            DO j=1,nagb
                ij=j+(i-1)*nagb      ! index with eigenvector array
                IF(j <= nvgb) THEN
                    itgbi=globalParVarToTotal(j)
                    label=globalParLabelIndex(1,itgbi)
                ELSE
                    label=nvgb-j             ! label negative for constraints
                END IF
                iev=iev+1
                labele(iev)=label
                compnt(iev)=REAL(workspaceEigenVectors(ij),mps)    ! component
                IF(iev == 3) THEN
                    WRITE(lup,103) (labele(ie),compnt(ie),ie=1,iev)
                    iev=0
                END IF
            END DO
            IF(iev /= 0) WRITE(lup,103) (labele(ie),compnt(ie),ie=1,iev)
            iev=0
            WRITE(lup,*) ' '
        END DO
  
    END IF

101 FORMAT(1X,'    label       parameter      presigma        differ',  &
        '         error'/ 1X,'-----------',4X,4('-------------'))
102 FORMAT(i10,2X,4G14.5,f8.3)
103 FORMAT(3(i11,f11.7,2X))
110 FORMAT(i10,2X,2G14.5,28X,i12)
111 FORMAT(i10,2X,3G14.5,14X,i12)
112 FORMAT(i10,2X,4G14.5,i12)
END SUBROUTINE prtglo    ! print final log file

!***********************************************************************

!> Print input statistic
!!
!! For each global parameter:
!! - label (I10)
!! - parameter value (G14.5)
!! - presigma (G14.5)
!! - difference of parameters values (G14.5), = 0.
!! - Entries from binary files
!!
SUBROUTINE prtstat
    USE mpmod

    IMPLICIT NONE
    REAL(mps):: par
    REAL(mps):: presig
    INTEGER(mpi) :: icount
    INTEGER(mpi) :: itgbi
    INTEGER(mpi) :: itgbl
    INTEGER(mpi) :: ivgbi
    INTEGER(mpi) :: lup
    INTEGER(mpi) :: ncon
    INTEGER(mpi) :: k

    SAVE
    !     ...

    lup=09
    CALL mvopen(lup,'millepede.res')
    WRITE(lup,*) '*** Results of checking input only, no solution performed ***'
    WRITE(lup,*) '! fixed-1: by pre-sigma, -2: by entries cut, -3: by iterated entries cut'
    WRITE(lup,*) '!      Label       Value     Pre-sigma         Entries Constraints  Status '
    !iprlim=10
    DO itgbi=1,ntgb  ! all parameter variables
        itgbl=globalParLabelIndex(1,itgbi)
        ivgbi=globalParLabelIndex(2,itgbi)
        par=REAL(globalParameter(itgbi),mps)      ! initial value
        presig=REAL(globalParPreSigma(itgbi),mps) ! initial presigma
        icount=globalParCounts(itgbi) ! from binary files
        ncon=globalParCons(itgbi) ! number of active constraints

        IF (ivgbi <= 0) THEN
            WRITE(lup,110) itgbl,par,presig,icount,ncon,ivgbi
        ELSE
            WRITE(lup,111) itgbl,par,presig,icount,ncon
        END IF
    END DO
    ! appearance statistics
    IF (icheck > 1) THEN
        WRITE(lup,*) '! '
        WRITE(lup,*) '! Appearance statistics '
        WRITE(lup,*) '!      Label  First file and record  Last file and record   #files  #paired-par'
        DO itgbi=1,ntgb
            WRITE(lup,112) globalParLabelIndex(1,itgbi), (appearanceCounter(itgbi*5+k), k=-4,0), pairCounter(itgbi)
        END DO
    END IF
    REWIND lup
    CLOSE(UNIT=lup)

110 FORMAT(' ! ',i10,2X,2G14.5,2i12,'  fixed',I2)
111 FORMAT(' ! ',i10,2X,2G14.5,2i12,'  variable')
112 FORMAT(' !.',i10,6i11)
END SUBROUTINE prtstat    ! print input statistics


!> Product symmetric matrix times vector.
!!
!! A(sym) * X => B. Used by \ref minresmodule::minres "MINRES" method (Is most CPU intensive part).
!! The matrix A is the global matrix in full symmetric or (compressed) sparse storage.
!!
!! \param [in]   n   size of matrix
!! \param [in]   x   vector X
!! \param [in]   b   result vector B

SUBROUTINE avprd0(n,x,b)
    USE mpmod

    IMPLICIT NONE
    INTEGER(mpi) :: i
    INTEGER(mpi) :: iencdb
    INTEGER(mpi) :: iencdm
    INTEGER(mpi) :: iproc
    INTEGER(mpi) :: ir
    INTEGER(mpi) :: j
    INTEGER(mpi) :: jc
    INTEGER(mpi) :: jj
    INTEGER(mpi) :: jn

    INTEGER(mpi), INTENT(IN)          :: n
    REAL(mpd), INTENT(IN)             :: x(n)
    REAL(mpd), INTENT(OUT)            :: b(n)
    INTEGER(mpl) :: k
    INTEGER(mpl) :: kk
    INTEGER(mpl) :: kl
    INTEGER(mpl) :: ku
    INTEGER(mpl) :: ll
    INTEGER(mpl) :: lj
    INTEGER(mpl) :: indij
    INTEGER(mpl) :: indid
    INTEGER(mpl) :: ij
    INTEGER(mpi) :: ichunk
    !$    INTEGER(mpi) OMP_GET_THREAD_NUM
    SAVE
    !     ...
    !$ DO i=1,n
    !$    b(i)=0.0_mpd             ! reset 'global' B()
    !$ END DO
    ichunk=MIN((n+mthrd-1)/mthrd/8+1,1024)
    IF(matsto == 1) THEN
        ! full symmetric matrix
        ! parallelize row loop
        ! private copy of B(N) for each thread, combined at end, init with 0.
        ! slot of 1024 'I' for next idle thread
        !$OMP  PARALLEL DO &
        !$OMP  PRIVATE(J,IJ) &
        !$OMP  REDUCTION(+:B) &
        !$OMP  SCHEDULE(DYNAMIC,ichunk)
        DO i=1,n
            ij=i
            ij=(ij*ij-ij)/2
            b(i)=globalMatD(ij+i)*x(i)
            DO j=1,i-1
                b(j)=b(j)+globalMatD(ij+j)*x(i)
                b(i)=b(i)+globalMatD(ij+j)*x(j)
            END DO
        END DO
        !$OMP END PARALLEL DO
    ELSE
        ! sparse, compressed matrix
        IF(sparseMatrixOffsets(2,1) /= n+1) THEN
            CALL peend(24,'Aborted, vector/matrix size mismatch')
            STOP 'AVPRD0: mismatched vector and matrix'
        END IF
        iencdb=nencdb
        iencdm=ishft(1,iencdb)-1
        ! parallelize row loop
        ! slot of 1024 'I' for next idle thread
        !$OMP PARALLEL DO &
        !$OMP  PRIVATE(IR,K,KK,LL,KL,KU,INDID,INDIJ,J,JC,JN,LJ,JJ) &
        !$OMP  REDUCTION(+:B) &
        !$OMP  SCHEDULE(DYNAMIC,ichunk)
        DO i=1,n
            iproc=0
            !$     IPROC=OMP_GET_THREAD_NUM()         ! thread number
            b(i)=globalMatD(i)*x(i)    ! diagonal elements
            !                                ! off-diagonals double precision
            ir=i
            kk=sparseMatrixOffsets(1,ir) ! offset in 'd' (column lists)
            ll=sparseMatrixOffsets(2,ir) ! offset in 'j' (matrix)
            kl=0
            ku=sparseMatrixOffsets(1,ir+1)-1-kk
            indid=kk
            indij=ll
            IF (sparseMatrixColumns(indid) /= 0) THEN  ! no compression
                DO k=kl,ku
                    j=sparseMatrixColumns(indid+k)
                    b(j)=b(j)+globalMatD(indij+k)*x(i)
                    b(i)=b(i)+globalMatD(indij+k)*x(j)
                END DO
            ELSE
                lj=0
                ku=((ku+1)*8)/9-1         ! number of regions (-1)
                indid=indid+ku/8+1        ! skip group offsets
                IF (mextnd>0) THEN
                    ! extended storage
                    DO kl=0,ku
                        jc=sparseMatrixColumns(indid+kl)
                        j=ishft(jc,-iencdb)
                        jn=IAND(jc, iencdm)
                        b(i)=b(i)+dot_product(globalMatD(indij+lj:indij+lj+jn-1),x(j:j+jn-1))
                        lj=lj+jn
                    END DO    
                ELSE
                    DO kl=0,ku
                        jc=sparseMatrixColumns(indid+kl)
                        j=ishft(jc,-iencdb)
                        jn=IAND(jc, iencdm)
                        DO jj=1,jn
                            b(j)=b(j)+globalMatD(indij+lj)*x(i)
                            b(i)=b(i)+globalMatD(indij+lj)*x(j)
                            j=j+1
                            lj=lj+1
                        END DO
                    END DO
                END IF 
            END IF

            IF (nspc > 1) THEN
                ir=i+n+1                     ! off-diagonals single precision
                kk=sparseMatrixOffsets(1,ir) ! offset in 'd' (column lists)
                ll=sparseMatrixOffsets(2,ir) ! offset in '.' (matrix)
                kl=0
                ku=sparseMatrixOffsets(1,ir+1)-1-kk
                indid=kk
                indij=ll
                IF (sparseMatrixColumns(indid) /= 0) THEN  ! no compression
                    DO k=kl,ku
                        j=sparseMatrixColumns(indid+k)
                        b(j)=b(j)+REAL(globalMatF(indij+k),mpd)*x(i)
                        b(i)=b(i)+REAL(globalMatF(indij+k),mpd)*x(j)
                    END DO
                ELSE
                    lj=0
                    ku=((ku+1)*8)/9-1         ! number of regions (-1)
                    indid=indid+ku/8+1        ! skip group offsets
                    DO kl=0,ku
                        jc=sparseMatrixColumns(indid+kl)
                        j=ishft(jc,-iencdb)
                        jn=IAND(jc, iencdm)
                        IF (mextnd>0) THEN
                            ! extended storage
                            DO jj=1,jn
                                b(i)=b(i)+REAL(globalMatF(indij+lj),mpd)*x(j)
                                j=j+1
                                lj=lj+1
                            END DO
                        ELSE
                            DO jj=1,jn
                                b(j)=b(j)+REAL(globalMatF(indij+lj),mpd)*x(i)
                                b(i)=b(i)+REAL(globalMatF(indij+lj),mpd)*x(j)
                                j=j+1
                                lj=lj+1
                            END DO
                        END IF       
                    END DO
                END IF
            END IF
        END DO
    ENDIF

END SUBROUTINE avprd0

!> Product symmetric matrix times vector.
!!
!! A(sym) * X => B. Used by \ref minresmodule::minres "MINRES" method (Is most CPU intensive part).
!! The matrix A is the global matrix in full symmetric or (compressed) sparse storage.
!! Allows for size of X and smaller than size of matrix in case of solution with constriants by elimination.
!!
!! \param [in]   n   size of matrix ( <= size of global matrix)
!! \param [in]   x   vector X
!! \param [in]   b   result vector B

SUBROUTINE avprod(n,x,b)
    USE mpmod

    IMPLICIT NONE

    INTEGER(mpi), INTENT(IN)          :: n
    REAL(mpd), INTENT(IN)             :: x(n)
    REAL(mpd), INTENT(OUT)            :: b(n)

    SAVE
    !     ...
    IF(n > nagb) THEN
        CALL peend(24,'Aborted, vector/matrix size mismatch')
        STOP 'AVPROD: mismatched vector and matrix'
    END IF
    ! input to AVPRD0
    vecXav(1:n)=x
    vecXav(n+1:nagb)=0.0_mpd
    !use elimination for constraints ?
    IF(n < nagb) CALL qlmlq(vecXav,1,.false.) ! Q*x
    ! calclulate vecBav=globalMat*vecXav
    CALL AVPRD0(nagb,vecXav,vecBav)
    !use elimination for constraints ?
    IF(n < nagb) CALL qlmlq(vecBav,1,.true.) ! Q^t*x
    ! output from AVPRD0
    b=vecBav(1:n)

END SUBROUTINE avprod


!> Index for sparse storage.
!!
!! In case of (compressed) sparse storage calculate index for off-diagonal matrix element.
!!
!! \param  [in]  itema  row number
!! \param  [in]  itemb  column number
!! \return index (>(<) 0: double(single) precision element, =0: not existing)

FUNCTION ijadd(itema,itemb)      ! index using "d" and "z"
    USE mpmod

    IMPLICIT NONE
    INTEGER(mpi) :: iencdb
    INTEGER(mpi) :: iencdm
    INTEGER(mpi) :: isgn
    INTEGER(mpi) :: ispc
    INTEGER(mpi) :: item2
    INTEGER(mpi) :: jtem
    INTEGER(mpi) :: jtemc
    INTEGER(mpi) :: jtemn

    INTEGER(mpi), INTENT(IN) :: itema
    INTEGER(mpi), INTENT(IN) :: itemb

    INTEGER(mpl) :: ijadd
    INTEGER(mpl) :: k
    INTEGER(mpl) :: kk
    INTEGER(mpl) :: kl
    INTEGER(mpl) :: ku
    INTEGER(mpl) :: indid
    INTEGER(mpl) :: nd
    INTEGER(mpl) :: ll
    INTEGER(mpl) :: k8
    INTEGER(mpl) :: item1
    !     ...
    ijadd=0
    nd=sparseMatrixOffsets(2,1)-1   ! dimension of matrix
    item1=MAX(itema,itemb)          ! larger index
    item2=MIN(itema,itemb)          ! smaller index
    IF(item2 <= 0.OR.item1 > nd) RETURN
    IF(item1 == item2) THEN         ! diagonal element
        ijadd=item1
        RETURN
    END IF
    !                                   ! off-diagonal element
    iencdb=nencdb                       ! encoding info
    iencdm=ishft(1,iencdb)-1
    isgn=-1
    outer: DO ispc=1,nspc
        kk=sparseMatrixOffsets(1,item1) ! offset in 'd' (column lists)
        ll=sparseMatrixOffsets(2,item1) ! offset in 'j' (matrix)
        kl=0
        ku=sparseMatrixOffsets(1,item1+1)-1-kk
        indid=kk
        item1=item1+nd+1
        isgn=-isgn
        IF (sparseMatrixColumns(indid) == 0) THEN     ! compression ?
    
            ku=((ku+1)*8)/9-1        ! number of regions (-1)
            indid=indid+ku/8+1       ! skip group offsets
            kl=0
            IF(ku < kl) CYCLE outer  ! not found
            DO
                k=(kl+ku)/2                    ! binary search
                jtemc=sparseMatrixColumns(indid+k)              ! compressed information
                jtem =ishft(jtemc,-iencdb)     ! first column of region
                jtemn=jtem+IAND(jtemc,iencdm)  ! first column after region
                IF(item2 >= jtem.AND.item2 < jtemn) EXIT ! found
                IF(item2 < jtem) THEN
                    ku=k-1
                ELSE IF(item2 >= jtemn) THEN
                    kl=k+1
                END IF
                IF(kl <= ku) CYCLE
                CYCLE outer ! not found
            END DO
            k8=k/8                            ! region group (-1)
            ll=ll+sparseMatrixColumns(kk+k8)  ! offset for group of (8) regions
            DO kl=k8*8,k-1
                ll=ll+IAND(sparseMatrixColumns(indid+kl),iencdm) ! add region lengths
            END DO
            ijadd=ll+item2-jtem
    
        ELSE
    
            IF(ku < kl) CYCLE outer ! not found
            DO
                k=(kl+ku)/2                  ! binary search
                jtem=sparseMatrixColumns(indid+k)
                jtemn=jtem
                IF(item2 == jtem) EXIT ! found
                IF(item2 < jtem) THEN
                    ku=k-1
                ELSE IF(item2 > jtem) THEN
                    kl=k+1
                END IF
                IF(kl <= ku) CYCLE
                CYCLE outer  ! not found
            END DO
            ijadd=ll+k

        END IF
        ijadd=ijadd*isgn
        RETURN
    END DO outer

END FUNCTION ijadd

!> Fill 2nd half of matrix for extended storage.
!!

SUBROUTINE mhalf2
    USE mpmod

    IMPLICIT NONE
    INTEGER(mpi) :: i
    INTEGER(mpi) :: ichunk
    INTEGER(mpi) :: iencdb
    INTEGER(mpi) :: iencdm
    INTEGER(mpi) :: ir
    INTEGER(mpi) :: ispc
    INTEGER(mpi) :: j
    INTEGER(mpi) :: jtem
    INTEGER(mpi) :: jtemc
    INTEGER(mpi) :: jtemn
    INTEGER(mpi) :: nd

    INTEGER(mpl) :: ij
    INTEGER(mpl) :: ijadd
    INTEGER(mpl) :: k
    INTEGER(mpl) :: kk
    INTEGER(mpl) :: kl
    INTEGER(mpl) :: ku
    INTEGER(mpl) :: indid
    INTEGER(mpl) :: ll
    INTEGER(mpl) :: k8
    !     ...

    nd=INT(sparseMatrixOffsets(2,1),mpi)-1   ! dimension of matrix
    ichunk=MIN((nd+mthrd-1)/mthrd/8+1,1024)

    iencdb=nencdb                       ! encoding info
    iencdm=ishft(1,iencdb)-1
    DO ispc=1,nspc
        ! parallelize row loop
        ! slot of 1024 'I' for next idle thread
        !$OMP PARALLEL DO &
        !$OMP  PRIVATE(I,IR,K,KK,LL,KL,KU,K8,INDID,IJ,J,JTEMC,JTEM,JTEMN) &
        !$OMP  SCHEDULE(DYNAMIC,ichunk)
        DO i=1,nd
            ir=i+(ispc-1)*(nd+1)
            kk=sparseMatrixOffsets(1,ir) ! offset in 'd' (column lists)
            ll=sparseMatrixOffsets(2,ir) ! offset in 'j' (matrix)
            kl=sparseMatrixCompression(i+(ispc-1)*nd) ! number of regions in 1st half (j<i)
                        
            ku=sparseMatrixOffsets(1,ir+1)-kk
            !IF (sparseMatrixColumns(kk) == 0) THEN     ! compression ?
            ku=(ku*8)/9-1        ! number of regions (-1)
            indid=kk+ku/8+1      ! index of first region (after group offsets)
            k8=kl/8                           ! region group (-1)
            ll=ll+sparseMatrixColumns(kk+k8)  ! offset for group of (8) regions
            DO k=k8*8,kl-1
                ll=ll+IAND(sparseMatrixColumns(indid+k),iencdm) ! add region lengths
            END DO
            DO k=kl,ku
                jtemc=sparseMatrixColumns(indid+k)              ! compressed information
                jtem =ishft(jtemc,-iencdb)     ! first column of region
                jtemn=jtem+IAND(jtemc,iencdm)  ! first column after region
                DO j=jtem,jtemn-1
                    ij=ijadd(i,j)
                    IF (ispc==1) THEN
                        globalMatD(ll)=globalMatD(ij)
                    ELSE
                        globalMatF(ll)=globalMatF(-ij)
                    END IF
                    ll=ll+1
                END DO
            END DO
        END DO
        !$OMP END PARALLEL DO
    END DO

END SUBROUTINE mhalf2

!> Time conversion.
!!
!! Convert from seconds to hours, minues, seconds
!!
!! \param [in]  deltat   time in seconds
!! \param [out] nhour    hours
!! \param [out] minut    minutes
!! \param [out] secnd    seconds

SUBROUTINE sechms(deltat,nhour,minut,secnd)
    USE mpdef

    IMPLICIT NONE
    REAL(mps), INTENT(IN) :: deltat
    INTEGER(mpi), INTENT(OUT) :: minut
    INTEGER(mpi), INTENT(OUT):: nhour
    REAL(mps), INTENT(OUT):: secnd
    INTEGER(mpi) :: nsecd
    !     DELTAT = time in sec  -> NHOUR,MINUT,SECND
    !     ...
    nsecd=nint(deltat,mpi) ! -> integer
    nhour=nsecd/3600
    minut=nsecd/60-60*nhour
    secnd=deltat-60*(minut+60*nhour)
END SUBROUTINE sechms

!> Translate labels to indices (for global parameters).
!!
!! Functions INONE and subroutine UPONE are
!! used to collect items, i.e. labels, and to order and translate them.
!!
!! In the first phase items are collected and stored by calling
!! <tt>IRES=INONE(ITEM)</tt>.
!!
!! At the first entry the two sub-arrays "a" (globalParLabelIndex)
!! and "b" (globalParHashTable) of length 2N
!! are generated with a start length for N=128 entries.
!! In array "a" two words are reserved for each item: (ITEM, count).
!! The function INONE(ITEM) returns the number of the item.
!! At each entry the argument is compared with the already stored items,
!! new items are stored. Search
!! for entries is done using hash-indices, stored in sub-array "b".
!! The initial hash-index is
!!
!!        j = 1 + mod(ITEM, n_prime) + N
!!
!! where n_prime is the largest prime number less than N.
!! At each entry the count is increased by one. If N items are stored,
!! the size of the sub-arrays is increased by calling
!! <tt>CALL UPONE</tt>.
!!
!! \param[in] item  label
!! \return index

INTEGER(mpi) FUNCTION inone(item)             ! translate 1-D identifier to nrs
    USE mpmod
    USE mpdalc

    IMPLICIT NONE
    INTEGER(mpi), INTENT(IN) :: item
    INTEGER(mpi) :: j
    INTEGER(mpi) :: k
    INTEGER(mpi) :: iprime
    INTEGER(mpl) :: length
    INTEGER(mpl), PARAMETER :: two = 2

    inone=0
    IF(item <= 0) RETURN
    IF(globalParHeader(-1) == 0) THEN
        length=128                   ! initial number
        CALL mpalloc(globalParLabelIndex,two,length,'INONE: label & index')
        CALL mpalloc(globalParHashTable,2*length,'INONE: hash pointer')
        globalParHashTable = 0
        globalParHeader(-0)=INT(length,mpi)       ! length of labels/indices
        globalParHeader(-1)=0                 ! number of stored items
        globalParHeader(-2)=0                 ! =0 during build-up
        globalParHeader(-3)=INT(length,mpi)       ! next number
        globalParHeader(-4)=iprime(globalParHeader(-0))    ! prime number
        globalParHeader(-5)=0                 ! number of overflows
        globalParHeader(-6)=0                 ! nr of variable parameters
    END IF
    outer: DO
        j=1+MOD(item,globalParHeader(-4))+globalParHeader(-0)
        inner: DO ! normal case: find item
            k=j
            j=globalParHashTable(k)
            IF(j == 0) EXIT inner    ! unused hash code
            IF(item == globalParLabelIndex(1,j)) EXIT outer ! found
        END DO inner
        ! not found
        IF(globalParHeader(-1) == globalParHeader(-0).OR.globalParHeader(-2) /= 0) THEN
            globalParHeader(-5)=globalParHeader(-5)+1 ! overflow
            j=0
            RETURN
        END IF
        globalParHeader(-1)=globalParHeader(-1)+1      ! increase number of elements
        globalParHeader(-3)=globalParHeader(-1)
        j=globalParHeader(-1)
        globalParHashTable(k)=j                ! hash index
        globalParLabelIndex(1,j)=item          ! add new item
        globalParLabelIndex(2,j)=0             ! reset counter
        IF(globalParHeader(-1) /= globalParHeader(-0)) EXIT outer
        ! update with larger dimension and redefine index
        globalParHeader(-3)=globalParHeader(-3)*2
        CALL upone
        IF (lvllog > 1) WRITE(lunlog,*) 'INONE: array increased to',  &
            globalParHeader(-3),' words'
    END DO outer

    IF(globalParHeader(-2) == 0) THEN
        globalParLabelIndex(2,j)=globalParLabelIndex(2,j)+1 ! increase counter
        globalParHeader(-7)=globalParHeader(-7)+1
    END IF
    inone=j
END FUNCTION inone

!> Update, redefine hash indices.
SUBROUTINE upone
    USE mpmod
    USE mpdalc

    IMPLICIT NONE
    INTEGER(mpi) :: i
    INTEGER(mpi) :: j
    INTEGER(mpi) :: k
    INTEGER(mpi) :: iprime
    INTEGER(mpi) :: nused
    LOGICAL :: finalUpdate
    INTEGER(mpl) :: oldLength
    INTEGER(mpl) :: newLength
    INTEGER(mpl), PARAMETER :: two = 2
    INTEGER(mpi), DIMENSION(:,:), ALLOCATABLE :: tempArr
    SAVE
    !     ...
    finalUpdate=(globalParHeader(-3) == globalParHeader(-1))
    IF(finalUpdate) THEN ! final (cleanup) call
        CALL sort2k(globalParLabelIndex,globalParHeader(-1)) ! sort items
    END IF
    ! save old LabelIndex
    nused = globalParHeader(-1)
    oldLength = globalParHeader(-0)
    CALL mpalloc(tempArr,two,oldLength,'INONE: temp array')
    tempArr(:,1:nused)=globalParLabelIndex(:,1:nused)
    CALL mpdealloc(globalParLabelIndex)
    CALL mpdealloc(globalParHashTable)
    ! create new LabelIndex
    newLength = globalParHeader(-3)
    CALL mpalloc(globalParLabelIndex,two,newLength,'INONE: label & index')
    CALL mpalloc(globalParHashTable,2*newLength,'INONE: hash pointer')
    globalParHashTable = 0
    globalParLabelIndex(:,1:nused) = tempArr(:,1:nused) ! copy back saved content
    CALL mpdealloc(tempArr)
    globalParHeader(-0)=INT(newLength,mpi)   ! length of labels/indices
    globalParHeader(-3)=globalParHeader(-1)
    globalParHeader(-4)=iprime(globalParHeader(-0))          ! prime number < LNDA
    ! redefine hash
    outer: DO i=1,globalParHeader(-1)
        j=1+MOD(globalParLabelIndex(1,i),globalParHeader(-4))+globalParHeader(-0)
        inner: DO
            k=j
            j=globalParHashTable(k)
            IF(j == 0) EXIT inner    ! unused hash code
            IF(j == i) CYCLE outer ! found
        ENDDO inner
        globalParHashTable(k)=i
    END DO outer
    IF(.NOT.finalUpdate) RETURN

    globalParHeader(-2)=1       ! set flag to inhibit further updates
    IF (lvllog > 1) THEN
        WRITE(lunlog,*) ' '
        WRITE(lunlog,*) 'INONE: array reduced to',newLength,' words'
        WRITE(lunlog,*) 'INONE:',globalParHeader(-1),' items stored.'
    END IF
END SUBROUTINE upone                  ! update, redefine

!> largest prime number < N.
!!
!! \param [in] n N
!! \return largest prime number < N

INTEGER(mpi) FUNCTION iprime(n)
    USE mpdef

    IMPLICIT NONE
    INTEGER(mpi), INTENT(IN) :: n
    INTEGER(mpi) :: nprime
    INTEGER(mpi) :: nsqrt
    INTEGER(mpi) :: i
    !     ...
    SAVE
    nprime=n                               ! max number
    IF(MOD(nprime,2) == 0) nprime=nprime+1 ! ... odd number
    outer: DO
        nprime=nprime-2                        ! next lower odd number
        nsqrt=INT(SQRT(REAL(nprime,mps)),mpi)
        DO i=3,nsqrt,2                         !
            IF(i*(nprime/i) == nprime) CYCLE outer   ! test prime number
        END DO
        EXIT outer ! found
    END DO outer
    iprime=nprime
END FUNCTION iprime

!> First data \ref sssec-loop1 "loop" (get global labels).
!!
!! Read all data files and add all labels to global labels table,
!! add labels from parameters, constraints and measurements (from text files).
!!
!! Define variable and fixed global parameters (depending on entries and pre-sigma).
!!
!! Iterate if records had been skipped due to too small read buffer size.
!!
SUBROUTINE loop1
    USE mpmod
    USE mpdalc

    IMPLICIT NONE
    INTEGER(mpi) :: i
    INTEGER(mpi) :: idum
    INTEGER(mpi) :: in
    INTEGER(mpi) :: indab
    INTEGER(mpi) :: itgbi
    INTEGER(mpi) :: itgbl
    INTEGER(mpi) :: ivgbi
    INTEGER(mpi) :: j
    INTEGER(mpi) :: mqi
    INTEGER(mpi) :: nc31
    INTEGER(mpi) :: nr
    INTEGER(mpi) :: nwrd
    INTEGER(mpi) :: inone
    REAL(mpd) :: param
    REAL(mpd) :: presg
    REAL(mpd) :: prewt

    INTEGER(mpl) :: length
    SAVE
    !     ...
    WRITE(lunlog,*) ' '
    WRITE(lunlog,*) 'LOOP1: starting'
    CALL mstart('LOOP1')
    !     add labels from parameter, constraints, measurements -------------
    DO i=1, lenParameters
        idum=inone(listParameters(i)%label)
    END DO
    DO i=1, lenPreSigmas
        idum=inone(listPreSigmas(i)%label)
    END DO
    DO i=1, lenConstraints
        idum=inone(listConstraints(i)%label)
    END DO
    DO i=1, lenMeasurements
        idum=inone(listMeasurements(i)%label)
    END DO

    IF(globalParHeader(-1) /= 0) THEN
        WRITE(lunlog,*) 'LOOP1:',globalParHeader(-1), ' labels from txt data stored'
    END IF
    WRITE(lunlog,*) 'LOOP1: reading data files'

    DO
        DO j=1,globalParHeader(-1)
            globalParLabelIndex(2,j)=0   ! reset count
        END DO

        !     read all data files and add all labels to global labels table ----

        IF(mprint /= 0) THEN
            WRITE(*,*) 'Read all binary data files:'
        END IF
        CALL hmpldf(1,'Number of words/record in binary file')
        CALL hmpdef(8,0.0,60.0,'not_stored data per record')
        !     define read buffer
        nc31=ncache/(31*mthrdr) ! split read cache 1 : 10 : 10*2 for pointers, ints, floats
        nwrd=nc31+1
        length=nwrd*mthrdr
        CALL mpalloc(readBufferPointer,length,'read buffer, pointer')
        nwrd=nc31*10+2+ndimbuf
        length=nwrd*mthrdr
        CALL mpalloc(readBufferDataI,length,'read buffer, integer')
        CALL mpalloc(readBufferDataD,length,'read buffer, double')
        ! to read (old) float binary files
        length=(ndimbuf+2)*mthrdr
        CALL mpalloc(readBufferDataF,length,'read buffer, float')

        DO
            CALL peread(nr)  ! read records
            IF (skippedRecords == 0) CALL peprep(0)   ! prepare records
            IF(nr <= 0) EXIT ! end of data?
        END DO
        !     release read buffer
        CALL mpdealloc(readBufferDataF)
        CALL mpdealloc(readBufferDataD)
        CALL mpdealloc(readBufferDataI)
        CALL mpdealloc(readBufferPointer)
        IF (skippedRecords == 0) THEN
            EXIT
        ELSE
            WRITE(lunlog,*) 'LOOP1: reading data files again'
        END IF
    END DO

    IF(nhistp /= 0) THEN
        CALL hmprnt(1)
        CALL hmprnt(8)
    END IF
    CALL hmpwrt(1)
    CALL hmpwrt(8)
    ntgb = globalParHeader(-1)     ! total number of labels/parameters
    IF (ntgb == 0) THEN
        CALL peend(21,'Aborted, no labels/parameters defined')
        STOP 'LOOP1: no labels/parameters defined'
    END IF
    CALL upone ! finalize the global label table
    WRITE(lunlog,*) 'LOOP1:',ntgb,  &
        ' is total number NTGB of labels/parameters'
    !     histogram number of entries per label ----------------------------
    CALL hmpldf(2,'Number of entries per label')
    DO j=1,ntgb
        CALL hmplnt(2,globalParLabelIndex(2,j))
    END DO
    IF(nhistp /= 0) CALL hmprnt(2) ! print histogram
    CALL hmpwrt(2) ! write to his file

    !     three subarrays for all global parameters ------------------------
    length=ntgb
    CALL mpalloc(globalParameter,length,'global parameters')
    globalParameter=0.0_mpd
    CALL mpalloc(globalParPreSigma,length,'pre-sigmas') ! presigmas
    globalParPreSigma=0.
    CALL mpalloc(globalParStart,length,'global parameters at start')
    globalParStart=0.
    CALL mpalloc(globalParCopy,length,'copy of global parameters')
    CALL mpalloc(globalParCounts,length,'global parameter counts')
    CALL mpalloc(globalParCons,length,'global parameter constraints')
    globalParCons=0

    DO i=1,lenParameters                  ! parameter start values
        param=listParameters(i)%value
        in=inone(listParameters(i)%label)
        IF(in /= 0) THEN
            globalParameter(in)=param
            globalParStart(in)=param
        ENDIF
    END DO

    npresg=0
    DO i=1,lenPreSigmas                 ! pre-sigma values
        presg=listPreSigmas(i)%value
        in=inone(listPreSigmas(i)%label)
        IF(in /= 0) THEN
            IF(presg > 0.0) npresg=npresg+1 ! FIXME: check if enough 'entries'?
            globalParPreSigma(in)=presg     ! insert pre-sigma 0 or > 0
        END IF
    END DO
    WRITE(lunlog,*) 'LOOP1:',npresg,' is number of pre-sigmas'
    WRITE(*,*) 'LOOP1:',npresg,' is number of pre-sigmas'
    IF(npresg == 0) WRITE(*,*) 'Warning: no pre-sigmas defined'

    !     determine flag variable (active) or fixed (inactive) -------------

    indab=0
    DO i=1,ntgb
        globalParCounts(i) = globalParLabelIndex(2,i)
        IF (globalParPreSigma(i) < 0.0) THEN
            globalParLabelIndex(2,i)=-1     ! fixed (pre-sigma), not used in matrix (not active)
        ELSE IF(globalParCounts(i) < mreqenf) THEN
            globalParLabelIndex(2,i)=-2     ! fixed (entries cut), not used in matrix (not active)        
        ELSE
            indab=indab+1
            globalParLabelIndex(2,i)=indab  ! variable, used in matrix (active)        
        END IF
    END DO
    globalParHeader(-6)=indab ! counted variable
    nvgb=indab  ! nr of variable parameters
    WRITE(lunlog,*) 'LOOP1:',nvgb, ' is number NVGB of variable parameters'
    IF(iteren > mreqenf) CALL loop1i ! iterate entries cut

    !     translation table of length NVGB of total global indices ---------
    length=nvgb
    CALL mpalloc(globalParVarToTotal,length,'translation table  var -> total')
    indab=0
    DO i=1,ntgb
        IF(globalParLabelIndex(2,i) > 0) THEN
            indab=indab+1
            globalParVarToTotal(indab)=i
        END IF
    END DO

    !     regularization ---------------------------------------------------
    CALL mpalloc(globalParPreWeight,length,'pre-sigmas weights') ! presigma weights
    WRITE(*,112) ' Default pre-sigma =',regpre,  &
        ' (if no individual pre-sigma defined)'
    WRITE(*,*)   'Pre-sigma factor is',regula

    IF(nregul == 0) THEN
        WRITE(*,*) 'No regularization will be done'
    ELSE
        WRITE(*,*) 'Regularization will be done, using factor',regula
    END IF
112 FORMAT(a,e9.2,a)
    IF (nvgb <= 0) THEN
        CALL peend(22,'Aborted, no variable global parameters')
        STOP '... no variable global parameters'
    ENDIF

    DO ivgbi=1,nvgb         ! IVGBI     = variable parameter index
        itgbi=globalParVarToTotal(ivgbi)     ! ITGBI = global parameter index
        presg=globalParPreSigma(itgbi)   ! get pre-sigma
        prewt=0.0              ! pre-weight
        IF(presg > 0.0) THEN
            prewt=1.0/presg**2            ! 1/presigma^2
        ELSE IF(presg == 0.0.AND.regpre > 0.0) THEN
            prewt=1.0/REAL(regpre**2,mpd) ! default 1/presigma^2
        END IF
        globalParPreWeight(ivgbi)=regula*prewt    ! weight = factor / presigma^2
    END DO

    !      WRITE(*,*) 'GlPa_index  GlPa_label  array1 array6'
    DO i=1,ntgb
        itgbl=globalParLabelIndex(1,i)
        ivgbi=globalParLabelIndex(2,i)
        IF(ivgbi > 0) THEN
        !          WRITE(*,111) I,ITGBL,QM(IND1+I),QM(IND6+IVGBI)
        ELSE
        !          WRITE(*,111) I,ITGBL,QM(IND1+I)
        END IF
    END DO
    ! 111  FORMAT(I5,I10,F10.5,E12.4)
    WRITE(*,101) 'NTGB',ntgb,'total number of parameters'
    WRITE(*,101) 'NVGB',nvgb,'number of variable parameters'

    !     print overview over important numbers ----------------------------

    nrecal=nrec
    IF(mprint /= 0) THEN
        WRITE(*,*) ' '
        WRITE(*,101) '  NREC',nrec,'number of records'
        IF (nrecd > 0) WRITE(*,101) ' NRECD',nrec,'number of records containing doubles'
        WRITE(*,101) 'MREQENF',mreqenf,'required number of entries (from binary files)'
        IF(iteren > mreqenf) &
            WRITE(*,101) 'ITEREN',iteren,'iterate cut for parameters with less entries'
        WRITE(*,101) 'MREQENA',mreqena,'required number of entries (from accepted fits)'            
        IF (mreqpe > 1) WRITE(*,101)  &
            'MREQPE',mreqpe,'required number of pair entries'
        IF (msngpe >= 1) WRITE(*,101)  &
            'MSNGPE',msngpe,'max pair entries single prec. storage'
        WRITE(*,101) 'NTGB',ntgb,'total number of parameters'
        WRITE(*,101) 'NVGB',nvgb,'number of variable parameters'
        IF(mprint > 1) THEN
            WRITE(*,*) ' '
            WRITE(*,*) 'Global parameter labels:'
            mqi=ntgb
            IF(mqi <= 100) THEN
                WRITE(*,*) (globalParLabelIndex(2,i),i=1,mqi)
            ELSE
                WRITE(*,*) (globalParLabelIndex(2,i),i=1,30)
                WRITE(*,*) ' ...'
                mqi=((mqi-20)/20)*20+1
                WRITE(*,*) (globalParLabelIndex(2,i),i=mqi,ntgb)
            END IF
        END IF
        WRITE(*,*) ' '
        WRITE(*,*) ' '
    END IF
    WRITE(8,*)   ' '
    WRITE(8,101) '  NREC',nrec,'number of records'
    IF (nrecd > 0) WRITE(8,101) ' NRECD',nrec,'number of records containing doubles'
    WRITE(8,101) 'MREQENF',mreqenf,'required number of entries (from binary files)'
    IF(iteren > mreqenf) &
        WRITE(8,101) 'ITEREN',iteren,'iterate cut for parameters with less entries'
    WRITE(8,101) 'MREQENA',mreqena,'required number of entries (from accepted fits)'

    WRITE(lunlog,*) 'LOOP1: ending'
    WRITE(lunlog,*) ' '
    CALL mend

101 FORMAT(1X,a8,' =',i10,' = ',a)
END SUBROUTINE loop1

!> Iteration of first data \ref sssec-loop1 "loop".
!!
!! Read all data files again skipping measurements with any parameter below the
!! entries cut to update the number of entries.
!!
!! Redefine variable and fixed global parameters (depending on updated entries).
!!
SUBROUTINE loop1i
    USE mpmod
    USE mpdalc

    IMPLICIT NONE
    INTEGER(mpi) :: i
    INTEGER(mpi) :: ibuf
    INTEGER(mpi) :: ij
    INTEGER(mpi) :: indab
    INTEGER(mpi) :: inder
    INTEGER(mpi) :: isfrst
    INTEGER(mpi) :: islast
    INTEGER(mpi) :: ist
    INTEGER(mpi) :: j
    INTEGER(mpi) :: ja
    INTEGER(mpi) :: jb
    INTEGER(mpi) :: jsp
    INTEGER(mpi) :: nc31
    INTEGER(mpi) :: nr
    INTEGER(mpi) :: nlow
    INTEGER(mpi) :: nst
    INTEGER(mpi) :: nwrd
    REAL(mpr8) :: glder

    INTEGER(mpl) :: length
    INTEGER(mpi), DIMENSION(:), ALLOCATABLE :: newCounter
    SAVE

    isfrst(ibuf)=readBufferPointer(ibuf)+1
    islast(ibuf)=readBufferDataI(readBufferPointer(ibuf))
    inder(i)=readBufferDataI(i)
    glder(i)=readBufferDataD(i)
    !     ...
    WRITE(lunlog,*) ' '
    WRITE(lunlog,*) 'LOOP1: iterating'
    WRITE(*,*) ' '
    WRITE(*,*) 'LOOP1: iterating'

    length=ntgb
    CALL mpalloc(newCounter,length,'new entries counter')
    newCounter=0

    !     define read buffer
    nc31=ncache/(31*mthrdr) ! split read cache 1 : 10 : 10*2 for pointers, ints, floats
    nwrd=nc31+1
    length=nwrd*mthrdr
    CALL mpalloc(readBufferPointer,length,'read buffer, pointer')
    nwrd=nc31*10+2+ndimbuf
    length=nwrd*mthrdr
    CALL mpalloc(readBufferDataI,length,'read buffer, integer')
    CALL mpalloc(readBufferDataD,length,'read buffer, double')
    ! to read (old) float binary files
    length=(ndimbuf+2)*mthrdr
    CALL mpalloc(readBufferDataF,length,'read buffer, float')

    DO
        CALL peread(nr)  ! read records
        CALL peprep(1)  ! prepare records
        DO ibuf=1,numReadBuffer           ! buffer for current record        
            ist=isfrst(ibuf)
            nst=islast(ibuf)
            nwrd=nst-ist+1
            DO ! loop over measurements
                CALL isjajb(nst,ist,ja,jb,jsp)
                IF(ja == 0.AND.jb == 0) EXIT
                IF(ja /= 0) THEN
                    nlow=0
                    DO j=1,ist-jb
                        ij=inder(jb+j)                      ! index of global parameter
                        ij=globalParLabelIndex(2,ij)        ! change to variable parameter
                        IF(ij == -2) nlow=nlow+1            ! fixed by entries cut
                    END DO
                    IF(nlow == 0) THEN
                        DO j=1,ist-jb
                            ij=inder(jb+j)                  ! index of global parameter
                            newCounter(ij)=newCounter(ij)+1 ! count again
                        END DO
                    ENDIF
                END IF
            END DO
            ! end-of-event  
        END DO
        IF(nr <= 0) EXIT ! end of data?
    END DO

    !     release read buffer
    CALL mpdealloc(readBufferDataF)
    CALL mpdealloc(readBufferDataD)
    CALL mpdealloc(readBufferDataI)
    CALL mpdealloc(readBufferPointer)

    indab=0
    DO i=1,ntgb
        IF(globalParLabelIndex(2,i) > 0) THEN
            IF(newCounter(i) >= mreqenf .OR. globalParCounts(i) >= iteren) THEN
                indab=indab+1
                globalParLabelIndex(2,i)=indab  ! variable, used in matrix (active)
            ELSE
                globalParLabelIndex(2,i)=-3     ! fixed (iterated entries cut), not used in matrix (not active)
            END IF
        END IF
    END DO
    globalParHeader(-6)=indab ! counted variable
    nvgb=indab  ! nr of variable parameters
    WRITE(lunlog,*) 'LOOP1:',nvgb, ' is number NVGB of variable parameters'
    CALL mpdealloc(newCounter)

END SUBROUTINE loop1i

!> Second data \ref sssec-loop2 "loop" (number of derivatives, global label pairs).
!!
!! Calculate maximum number of local, global derivatives and equations per record.
!!
!! For sparse storage count index pairs with bit (field) counters to construct sparsity
!! structure (row offsets, (compressed) column lists).
!!
!! Determine read/write cache splitting from average record values (length, global par. vector/matrix).
!!
!! Check constraints for rank deficit.

SUBROUTINE loop2
    USE mpmod
    USE mpdalc

    IMPLICIT NONE
    REAL(mps) :: chin2
    REAL(mps) :: chin3
    REAL(mps) :: cpr
    REAL(mps) :: fsum
    REAL(mps) :: gbc
    REAL(mps) :: gbu
    REAL(mpr8) :: glder
    INTEGER(mpi) :: i
    INTEGER(mpi) :: ia
    INTEGER(mpi) :: ib
    INTEGER(mpi) :: ibuf
    INTEGER(mpi) :: icgb
    INTEGER(mpi) :: iext
    INTEGER(mpi) :: ihis
    INTEGER(mpi) :: ij
    INTEGER(mpi) :: ijn
    INTEGER(mpi) :: inder
    INTEGER(mpi) :: ioff
    INTEGER(mpi) :: iproc
    INTEGER(mpi) :: irecmm
    INTEGER(mpi) :: isfrst
    INTEGER(mpi) :: islast
    INTEGER(mpi) :: ist
    INTEGER(mpi) :: itgbi
    INTEGER(mpi) :: itgbij
    INTEGER(mpi) :: itgbik
    INTEGER(mpi) :: ivgbij
    INTEGER(mpi) :: ivgbik
    INTEGER(mpi) :: j
    INTEGER(mpi) :: ja
    INTEGER(mpi) :: jb
    INTEGER(mpi) :: jext
    INTEGER(mpi) :: jcgb
    INTEGER(mpi) :: jsp
    INTEGER(mpi) :: joff
    INTEGER(mpi) :: k
    INTEGER(mpi) :: kfile
    INTEGER(mpi) :: l
    INTEGER(mpi) :: label
    INTEGER(mpi) :: lu
    INTEGER(mpi) :: lun
    INTEGER(mpi) :: maeqnf
    INTEGER(mpi) :: naeqna
    INTEGER(mpi) :: naeqnf
    INTEGER(mpi) :: naeqng
    INTEGER(mpi) :: nc31
    INTEGER(mpi) :: ncachd
    INTEGER(mpi) :: ncachi
    INTEGER(mpi) :: ncachr
    INTEGER(mpi) :: nda
    INTEGER(mpi) :: ndf
    INTEGER(mpi) :: ndfmax
    INTEGER(mpi) :: nfixed
    INTEGER(mpi) :: nggd
    INTEGER(mpi) :: nggi
    INTEGER(mpi) :: nmatmo
    INTEGER(mpi) :: noff
    INTEGER(mpi) :: nr
    INTEGER(mpi) :: nrecf
    INTEGER(mpi) :: nrecmm
    INTEGER(mpi) :: nst
    INTEGER(mpi) :: nwrd
    INTEGER(mpi) :: inone
    INTEGER(mpi) :: inc
    REAL(mps) :: wgh
    REAL(mps) :: wolfc3
    REAL(mps) :: wrec
    REAL(mps) :: chindl

    REAL(mpd)::dstat(3)
    REAL(mpd)::rerr
    INTEGER(mpl):: noff8
    INTEGER(mpl):: ndimbi
    INTEGER(mpl):: ndimsa(4)
    INTEGER(mpl):: ndgn
    INTEGER(mpl):: matsiz(2)
    INTEGER(mpl):: matwords
    INTEGER(mpl):: length
    INTEGER(mpl):: rows
    INTEGER(mpl):: cols
    INTEGER(mpl), PARAMETER :: two=2
    INTEGER(mpi) :: maxGlobalPar = 0
    INTEGER(mpi) :: maxLocalPar = 0
    INTEGER(mpi) :: maxEquations = 0

    INTERFACE ! needed for assumed-shape dummy arguments
        SUBROUTINE ndbits(ndims,ncmprs,nsparr,ihst)
            USE mpdef
            INTEGER(mpl), DIMENSION(4), INTENT(OUT) :: ndims
            INTEGER(mpi), DIMENSION(:), INTENT(OUT) :: ncmprs
            INTEGER(mpl), DIMENSION(:,:), INTENT(OUT) :: nsparr
            INTEGER(mpi), INTENT(IN) :: ihst
        END SUBROUTINE ndbits
        SUBROUTINE spbits(nsparr,nsparc,ncmprs)
            USE mpdef
            INTEGER(mpl), DIMENSION(:,:), INTENT(IN) :: nsparr
            INTEGER(mpi), DIMENSION(:), INTENT(OUT) :: nsparc
            INTEGER(mpi), DIMENSION(:), INTENT(IN) :: ncmprs
        END SUBROUTINE spbits
        SUBROUTINE gpbmap(npair)
            USE mpdef
            INTEGER(mpi), DIMENSION(:), INTENT(OUT) :: npair
        END SUBROUTINE gpbmap
    END INTERFACE
    
    SAVE

    !$ INTEGER(mpi) :: OMP_GET_THREAD_NUM

    isfrst(ibuf)=readBufferPointer(ibuf)+1
    islast(ibuf)=readBufferDataI(readBufferPointer(ibuf))
    inder(i)=readBufferDataI(i)
    glder(i)=readBufferDataD(i)
    !     ...
    WRITE(lunlog,*) ' '
    WRITE(lunlog,*) 'LOOP2: starting'
    CALL mstart('LOOP2')

    !     two subarrays to get the global parameter indices, used in an event
    length=nvgb
    CALL mpalloc(globalIndexUsage,length,'global index')
    CALL mpalloc(backIndexUsage,length,'back index')
    backIndexUsage=0

    ! prepare constraints - determine number of constraints NCGB
    !                     - sort and split into blocks
    CALL prpcon

    IF (icelim > 0) THEN ! elimination
        nagb=nvgb         ! total number of parameters
        nfgb=nvgb-ncgb    ! number of fit parameters
        nprecond(1)=0     ! number of constraints for preconditioner
        nprecond(2)=nfgb  ! matrix size for preconditioner
    ELSE                 ! Lagrange multipliers
        nagb=nvgb+ncgb    ! total number of parameters
        nfgb=nagb         ! number of fit parameters
        nprecond(1)=ncgb  ! number of constraints for preconditioner
        nprecond(2)=nvgb  ! matrix size for preconditioner
    ENDIF
    noff8=int8(nagb)*int8(nagb-1)/2

    !     read all data files and add all variable index pairs -------------

    IF (icheck > 1) CALL clbmap(ntgb)

    IF(matsto == 2) THEN
        CALL clbits(nagb,mreqpe,mhispe,msngpe,mcmprs,mextnd,ndimbi,nencdb,nspc) ! get dimension for bit storage, encoding, precision info
    END IF
    
    IF (imonit /= 0) THEN
        length=ntgb
        CALL mpalloc(measIndex,length,'measurement counter/index')
        measIndex=0
        CALL mpalloc(measRes,length,'measurement resolution')
        measRes=0.0_mps
        lunmon=9
        CALL mvopen(lunmon,'millepede.mon')
    ENDIF

    !     reading events===reading events===reading events===reading events=
    nrecf =0  ! records with fixed global parameters
    naeqng=0  ! count number of equations (with global der.)
    naeqnf=0  ! count number of equations ( " , fixed)
    naeqna=0  ! all
    WRITE(lunlog,*) 'LOOP2: start event reading'
    !     monitoring for sparse matrix?
    irecmm=0
    IF (matsto == 2.AND.matmon /= 0) THEN
        nmatmo=0
        IF (matmon > 0) THEN
            nrecmm=matmon
        ELSE
            nrecmm=1
        END IF
    END IF
    DO k=1,3
        dstat(k)=0.0_mpd
    END DO
    !     define read buffer
    nc31=ncache/(31*mthrdr) ! split read cache 1 : 10 : 10*2 for pointers, ints, floats
    nwrd=nc31+1
    length=nwrd*mthrdr
    CALL mpalloc(readBufferPointer,length,'read buffer, pointer')
    nwrd=nc31*10+2+ndimbuf
    length=nwrd*mthrdr
    CALL mpalloc(readBufferDataI,length,'read buffer, integer')
    CALL mpalloc(readBufferDataD,length,'read buffer, real')
    ! to read (old) float binary files
    length=(ndimbuf+2)*mthrdr
    CALL mpalloc(readBufferDataF,length,'read buffer, float')
    
    ! for checking appearance 
    IF (icheck > 1) THEN
        length=5*ntgb
        CALL mpalloc(appearanceCounter,length,'appearance statistics')
        appearanceCounter=0
        length=ntgb
        CALL mpalloc(pairCounter,length,'pair statistics')
        pairCounter=0
    END IF

    DO
        CALL peread(nr) ! read records
        CALL peprep(1)  ! prepare records
        ioff=0
        DO ibuf=1,numReadBuffer           ! buffer for current record
            nrec=readBufferDataI(isfrst(ibuf)-2)   ! record
            !     Printout for DEBUG
            IF(nrec <= mdebug) THEN
                nda=0
                kfile=NINT(readBufferDataD(isfrst(ibuf)-1),mpi) ! file
                wrec =REAL(readBufferDataD(isfrst(ibuf)-2),mps) ! weight
                WRITE(*,*) ' '
                WRITE(*,*) 'Record number ',nrec,' from file ',kfile
                IF (wgh /= 1.0) WRITE(*,*) '       weight ',wrec
                ist=isfrst(ibuf)
                nst=islast(ibuf)
                DO ! loop over measurements
                    CALL isjajb(nst,ist,ja,jb,jsp)
                    IF(ja == 0) EXIT
                    nda=nda+1
                    IF(nda > mdebg2) THEN
                        IF(nda == mdebg2+1)  WRITE(*,*) '... and more data'
                        CYCLE
                    END IF
                    WRITE(*,*) ' '
                    WRITE(*,*) nda, ' Measured value =',glder(ja),' +- ',glder(jb)
                    WRITE(*,*) 'Local derivatives:'
                    WRITE(*,107) (inder(ja+j),glder(ja+j),j=1,jb-ja-1)
107                 FORMAT(6(i3,g12.4))
                    IF (jb < ist) THEN
                        WRITE(*,*) 'Global derivatives:'
                        WRITE(*,108) (globalParLabelIndex(1,inder(jb+j)),inder(jb+j),  &
                            globalParLabelIndex(2,inder(jb+j)),glder(jb+j),j=1,ist-jb)
108                     FORMAT(3I11,g12.4)
                    END IF
                    IF(nda == 1) THEN
                        WRITE(*,*) 'total_par_label  __label__   var_par_index   derivative'
                    END IF
                END DO
                WRITE(*,*) ' '
            END IF
  
            nagbn =0                     ! count number of global derivatives
            nalcn =0                     ! count number of local  derivatives
            naeqn =0                     ! count number of equations
            maeqnf=naeqnf
            ist=isfrst(ibuf)
            nst=islast(ibuf)
            nwrd=nst-ist+1
            DO ! loop over measurements
                CALL isjajb(nst,ist,ja,jb,jsp)
                IF(ja == 0.AND.jb == 0) EXIT
                naeqn=naeqn+1
                naeqna=naeqna+1
                IF(ja /= 0) THEN
                    IF (ist > jb) THEN
                        naeqng=naeqng+1
                        ! monitoring, group measurements, sum up entries and errors
                        IF (imonit /= 0) THEN
                            rerr =REAL(glder(jb),mpd)     ! the error
                            ij=inder(jb+1)               ! index of first global parameter, used to group measurements
                            measIndex(ij)=measIndex(ij)+1
                            measRes(ij)=measRes(ij)+rerr
                        END IF
                    END IF    
                    nfixed=0
                    DO j=1,ist-jb
                        ij=inder(jb+j)                     ! index of global parameter
                        ! check appearance 
                        IF (icheck > 1) THEN
                            joff = 5*(ij-1)
                            kfile=NINT(readBufferDataD(isfrst(ibuf)-1),mpi) ! file
                            IF (appearanceCounter(joff+1) == 0) THEN
                                appearanceCounter(joff+1) = kfile
                                appearanceCounter(joff+2) = nrec-ifd(kfile) ! (local) record number
                            END IF
                            IF (appearanceCounter(joff+3) /= kfile) appearanceCounter(joff+5)=appearanceCounter(joff+5)+1
                            appearanceCounter(joff+3) = kfile
                            appearanceCounter(joff+4) = nrec-ifd(kfile) ! (local) record number
                            ! count pairs
                            DO k=1,j
                                CALL inbmap(ij,inder(jb+k))
                            END DO
                        END IF
                        
                        ij=globalParLabelIndex(2,ij)       ! change to variable parameter
                        IF(ij > 0) THEN
                            ijn=backIndexUsage(ij)         ! get index of index
                            IF(ijn == 0) THEN              ! not yet included
                                nagbn=nagbn+1              ! count
                                globalIndexUsage(nagbn)=ij ! store variable index
                                backIndexUsage(ij)=nagbn   ! store back index
                            END IF
                        ELSE
                            nfixed=nfixed+1
                        END IF
                    END DO
                    IF (nfixed > 0) naeqnf=naeqnf+1
                END IF
  
                IF(ja /= 0.AND.jb /= 0) THEN
                    DO j=1,jb-ja-1           ! local parameters
                        ij=inder(ja+j)
                        nalcn=MAX(nalcn,ij)
                    END DO
                END IF
            END DO
  
            ! end-of-event
            IF (naeqnf > maeqnf) nrecf=nrecf+1
            irecmm=irecmm+1
            !     end-of-event-end-of-event-end-of-event-end-of-event-end-of-event-e
  
            maxGlobalPar=MAX(nagbn,maxGlobalPar) ! maximum number of global parameters
            maxLocalPar=MAX(nalcn,maxLocalPar)   ! maximum number of local parameters
            maxEquations=MAX(naeqn,maxEquations) ! maximum number of equations
  
            !     sample statistics for caching
            dstat(1)=dstat(1)+REAL((nwrd+2)*2,mpd)               ! record size
            dstat(2)=dstat(2)+REAL(nagbn+2,mpd)                  ! indices,
            dstat(3)=dstat(3)+REAL(nagbn*nagbn+nagbn,mpd)        ! data for MUPDAT
  
            CALL sort1k(globalIndexUsage,nagbn) ! sort global par.
            ! overwrite read buffer with lists of global labels
            ioff=ioff+1
            readBufferPointer(ibuf)=ioff
            readBufferDataI(ioff)=ioff+nagbn
            DO i=1,nagbn                  ! reset global index array
                iext=globalIndexUsage(i)
                backIndexUsage(iext)=0
                readBufferDataI(ioff+i)=iext
            END DO
            ioff=ioff+nagbn
  
        END DO
        ioff=0

        IF (matsto == 2) THEN
            !$OMP  PARALLEL &
            !$OMP  DEFAULT(PRIVATE) &
            !$OMP  SHARED(numReadBuffer,readBufferPointer,readBufferDataI,MTHRD)
            iproc=0
            !$ IPROC=OMP_GET_THREAD_NUM()         ! thread number
            DO ibuf=1,numReadBuffer
                ist=isfrst(ibuf)
                nst=islast(ibuf)
                DO i=ist,nst                 ! store all combinations
                    iext=readBufferDataI(i)             ! variable global index
                    !$ IF (MOD(IEXT,MTHRD).EQ.IPROC) THEN  ! distinct rows per thread
                    DO l=ist,i
                        jext=readBufferDataI(l)
                        CALL inbits(iext,jext,1) ! save space
                    END DO
                    !$ ENDIF
                END DO
            END DO
            !$OMP END PARALLEL
            ! monitoring
            IF (matmon /= 0.AND.  &
                (irecmm >= nrecmm.OR.irecmm == mxrec)) THEN
                IF (nmatmo == 0) THEN
                    WRITE(*,*)
                    WRITE(*,*) 'Monitoring of sparse matrix construction'
                    WRITE(*,*) ' records ........ off-diagonal elements ',  &
                        '....... compression   memory'
                    WRITE(*,*) '             non-zero used(double)  used',  &
                        '(float)       [%]       [GB]'
                END IF
                nmatmo=nmatmo+1
                CALL ckbits(ndimsa)
                gbc=1.0E-9*REAL((mpi*ndimsa(2)+mpd*ndimsa(3)+mps*ndimsa(4))/mpi*(BIT_SIZE(1_mpi)/8),mps) ! GB compressed
                gbu=1.0E-9*REAL(((mpi+mpd)*(ndimsa(3)+ndimsa(4)))/mpi*(BIT_SIZE(1_mpi)/8),mps)             ! GB uncompressed
                cpr=100.0*gbc/gbu
                WRITE(*,1177) irecmm,ndimsa(1),ndimsa(3),ndimsa(4),cpr,gbc
1177            FORMAT(i9,3I13,f10.2,f11.6)
                DO WHILE(irecmm >= nrecmm)
                    IF (matmon > 0) THEN
                        nrecmm=nrecmm+matmon
                    ELSE
                        nrecmm=nrecmm*2
                    END IF
                END DO
            END IF

        END IF

        IF (nr <= 0) EXIT ! next block of events ?
    END DO
    !     release read buffer
    CALL mpdealloc(readBufferDataF)
    CALL mpdealloc(readBufferDataD)
    CALL mpdealloc(readBufferDataI)
    CALL mpdealloc(readBufferPointer)

    WRITE(lunlog,*) 'LOOP2: event reading ended - end of data'
    DO k=1,3
        dstat(k)=dstat(k)/REAL(nrec,mpd)
    END DO
    !     end=of=data=end=of=data=end=of=data=end=of=data=end=of=data=end=of

    IF (icheck > 1) THEN
        CALL gpbmap(pairCounter)
    END IF    

    IF(matsto == 2) THEN
          
        !     constraints and index pairs with Lagrange multiplier


        !     constraints - determine number of constraints NCGB and index-pairs
        !        Lagrange multiplier and global parameters


        inc=MAX(mreqpe, msngpe+1) !  keep constraints in double precision

        !  loop over (sorted) constraints
        DO jcgb=1,ncgb
            icgb=matConsSort(3,jcgb) ! unsorted constraint index
            DO i=vecConsStart(icgb)+2,vecConsStart(icgb+1)-1
                label=listConstraints(i)%label
                itgbi=inone(label)
                ij=globalParLabelIndex(2,itgbi)         ! change to variable parameter
                IF(ij > 0 .AND. nagb > nvgb) THEN
                    CALL inbits(nvgb+jcgb,ij,inc)
                END IF
            END DO
        END DO

        !     measurements - determine index-pairs

  
        i=1
        DO WHILE (i <= lenMeasurements)
            i=i+2
            !        loop over label/factor pairs
            ia=i
            DO
                i=i+1
                IF(i > lenMeasurements) EXIT
                IF(listMeasurements(i)%label == 0) EXIT
            END DO
            ib=i-1
  
            DO j=ia,ib
                itgbij=inone(listMeasurements(j)%label) ! total parameter index
                !         first index
                ivgbij=0
                IF(itgbij /= 0) ivgbij=globalParLabelIndex(2,itgbij) ! variable-parameter index
                DO k=ia,j
                    itgbik=inone(listMeasurements(k)%label) ! total parameter index
                    !         second index
                    ivgbik=0
                    IF(itgbik /= 0) ivgbik=globalParLabelIndex(2,itgbik) ! variable-parameter index
                    IF(ivgbij > 0.AND.ivgbik > 0) THEN
                        CALL inbits(ivgbij,ivgbik,mreqpe)
                        IF (mprint > 1) WRITE(*,*) 'add index pair ',ivgbij,ivgbik
                    END IF
                END DO
            END DO

        END DO
    END IF

    numMeas=0 ! number of measurement groups
    IF (imonit /= 0) THEN
        DO i=1,ntgb
            IF (measIndex(i) > 0) THEN
                numMeas=numMeas+1
                measRes(i) = measRes(i)/REAL(measIndex(i),mpd)
                measIndex(i) = numMeas
            END IF
        END DO
        length=numMeas*mthrd*measBins
        CALL mpalloc(measHists,length,'measurement counter')
    END IF
    !     print numbers ----------------------------------------------------

    IF (nagb >= 65536) THEN
        noff=INT(noff8/1000,mpi)
    ELSE
        noff=INT(noff8,mpi)
    END IF
    ndgn=0
    matwords=0
    IF(matsto == 2) THEN
        ihis=0
        IF (mhispe > 0) THEN
            ihis=15
            CALL hmpdef(ihis,0.0,REAL(mhispe,mps), 'NDBITS: #off-diagonal elements')
        END IF
        length=nagb*nspc
        CALL mpalloc(sparseMatrixCompression,length, 'sparse matrix row compression')
        sparseMatrixCompression=0
        length=(nagb+1)*nspc
        CALL mpalloc(sparseMatrixOffsets,two,length, 'sparse matrix row offsets')
        CALL ndbits(ndimsa,sparseMatrixCompression,sparseMatrixOffsets,ihis)
        ndgn=ndimsa(3)+ndimsa(4) ! actual number of off-diagonal elements
        matwords=ndimsa(2)+length ! size of sparsity structure
    
        IF (mhispe > 0) THEN
            IF (nhistp /= 0) CALL hmprnt(ihis)
            CALL hmpwrt(ihis)
        END IF
    END IF

    nagbn=maxGlobalPar ! max number of global parameters in one event
    nalcn=maxLocalPar  ! max number of local parameters in one event
    naeqn=maxEquations ! max number of equations in one event
    CALL mpdealloc(globalIndexUsage)
    CALL mpdealloc(backIndexUsage)
    !     matrices for event matrices
    !       split up cache
    IF (fcache(2) == 0.0) THEN ! from data (DSTAT)
        fcache(1)=REAL(dstat(1),mps)*fcache(1) ! leave some part free for fluctuations
        fcache(2)=REAL(dstat(2),mps)
        fcache(3)=REAL(dstat(3),mps)
    END IF
    fsum=fcache(1)+fcache(2)+fcache(3)
    DO k=1,3
        fcache(k)=fcache(k)/fsum
    END DO
    ncachr=NINT(REAL(ncache,mps)*fcache(1),mpi) ! read cache
    !     define read buffer
    nc31=ncachr/(31*mthrdr) ! split read cache 1 : 10 : 10*2 for pointers, ints, floats
    nwrd=nc31+1
    length=nwrd*mthrdr
    CALL mpalloc(readBufferPointer,length,'read buffer, pointer')
    nwrd=nc31*10+2+ndimbuf
    length=nwrd*mthrdr
    CALL mpalloc(readBufferDataI,length,'read buffer, integer')
    CALL mpalloc(readBufferDataD,length,'read buffer, real')
    ! to read (old) float binary files
    length=(ndimbuf+2)*mthrdr
    CALL mpalloc(readBufferDataF,length,'read buffer, float')

    ncachi=NINT(REAL(ncache,mps)*fcache(2),mpi) ! index cache
    ncachd=ncache-ncachr-ncachi              ! data cache
    nggd=(nagbn*nagbn+nagbn)/2+ncachd/(2*mthrd) ! number of double
    nggi=2+nagbn+ncachi/mthrd                   ! number of ints
    length=nagbn*mthrd
    CALL mpalloc(globalIndexUsage,length, 'global parameters (dim =max/event)')
    length=nvgb*mthrd
    CALL mpalloc(backIndexUsage,length,'global variable-index array')
    backIndexUsage=0
    length=nagbn*nalcn
    CALL mpalloc(localGlobalMatrix,length,'local/global matrix')
    length=nggd*mthrd
    CALL mpalloc(writeBufferUpdates,length,'symmetric update matrices')
    writeBufferHeader(-1)=nggd                  ! number of words per thread
    writeBufferHeader(-2)=(nagbn*nagbn+nagbn)/2 ! min free (double) words
    length=nggi*mthrd
    CALL mpalloc(writeBufferIndices,length,'symmetric update matrix indices')
    rows=7; cols=mthrd
    CALL mpalloc(writeBufferInfo,rows,cols,'write buffer status (I)')
    rows=2; cols=mthrd
    CALL mpalloc(writeBufferData,rows,cols,'write buffer status (F)')
    writeBufferHeader(1)=nggi                  ! number of words per thread
    writeBufferHeader(2)=nagbn+2               ! min free words

    !     print all relevant dimension parameters

    DO lu=6,8,2  ! unit 6 and 8
  
        WRITE(*,*) ' '
        WRITE(lu,101) 'NTGB',ntgb,'total number of parameters'
        WRITE(lu,102) '(all parameters, appearing in binary files)'
        WRITE(lu,101) 'NVGB',nvgb,'number of variable parameters'
        WRITE(lu,102) '(appearing in fit matrix/vectors)'
        WRITE(lu,101) 'NAGB',nagb,'number of all parameters'
        WRITE(lu,102) '(including Lagrange multiplier or reduced)'
        WRITE(lu,101) 'NFGB',nfgb,'number of fit parameters'
        WRITE(lu,101) 'MBANDW',mbandw,'band width of band matrix'
        WRITE(lu,102) '(if =0, no band matrix)'
        IF (nagb >= 65536) THEN
            WRITE(lu,101) 'NOFF/K',noff,'max number of off-diagonal elements'
        ELSE
            WRITE(lu,101) 'NOFF',noff,'max number of off-diagonal elements'
        END IF
        IF(ndgn /= 0) THEN
            IF (nagb >= 65536) THEN
                WRITE(lu,101) 'NDGN/K',ndgn/1000,'actual number of off-diagonal elements'
            ELSE
                WRITE(lu,101) 'NDGN',ndgn,'actual number of off-diagonal elements'
            ENDIF
        ENDIF
        WRITE(lu,101) 'NCGB',ncgb,'number of constraints'
        WRITE(lu,101) 'NAGBN',nagbn,'max number of global parameters in an event'
        WRITE(lu,101) 'NALCN',nalcn,'max number of local parameters in an event'
        WRITE(lu,101) 'NAEQN',naeqn,'max number of equations in an event'
        IF (mprint > 1) THEN
            WRITE(lu,101) 'NAEQNA',naeqna,'number of equations'
            WRITE(lu,101) 'NAEQNG',naeqng,  &
                'number of equations with       global derivatives'
            WRITE(lu,101) 'NAEQNF',naeqnf,  &
                'number of equations with fixed global derivatives'
            WRITE(lu,101) 'NRECF',nrecf,  &
                'number of records   with fixed global derivatives'
        END IF
        IF (ncache > 0) THEN
            WRITE(lu,101) 'NCACHE',ncache,'number of words for caching'
            WRITE(lu,111) (fcache(k)*100.0,k=1,3)
111         FORMAT(22X,'cache splitting ',3(f6.1,' %'))
        END IF
        WRITE(lu,*) ' '
  
        WRITE(lu,*) ' '
        WRITE(lu,*) 'Solution method and matrix-storage mode:'
        IF(metsol == 1) THEN
            WRITE(lu,*) '     METSOL = 1:  matrix inversion'
        ELSE IF(metsol == 2) THEN
            WRITE(lu,*) '     METSOL = 2:  diagonalization'
        ELSE IF(metsol == 3) THEN
            WRITE(lu,*) '     METSOL = 3:  MINRES (rtol', mrestl,')'
        ELSE IF(metsol == 4) THEN
            WRITE(lu,*) '     METSOL = 4:  MINRES-QLP (rtol', mrestl,')'
        ELSE IF(metsol == 5) THEN
            WRITE(lu,*) '     METSOL = 5:  GMRES'
        END IF
        WRITE(lu,*) '                  with',mitera,' iterations'
        IF(matsto == 1) THEN
            WRITE(lu,*) '     MATSTO = 1:  symmetric matrix, ', '(n*n+n)/2 elements'
        ELSE IF(matsto == 2) THEN
            WRITE(lu,*) '     MATSTO = 2:  sparse matrix'
        END IF
        IF(mextnd>0) WRITE(lu,*) '                  with extended storage'
        IF(dflim /= 0.0) THEN
            WRITE(lu,103) 'Convergence assumed, if expected dF <',dflim
        END IF
        IF(ncgb > 0) THEN
            IF(nfgb < nvgb) THEN
                WRITE(lu,*) 'Constraints handled by elimination'
            ELSE
                WRITE(lu,*) 'Constraints handled by Lagrange multipliers'
            ENDIF
        END IF
  
    END DO ! print loop

    !     Wolfe conditions

    IF(0.0 < wolfc1.AND.wolfc1 < wolfc2.AND.wolfc2 < 1.0) GO TO 32
    IF(wolfc1 == 0.0) wolfc1=1.0E-4
    IF(wolfc2 == 0.0) wolfc2=0.9
    IF(0.0 < wolfc1.AND.wolfc1 < wolfc2.AND.wolfc2 < 1.0) GO TO 32
    IF(wolfc1 <= 0.0) wolfc1=1.0E-4
    IF(wolfc2 >= 1.0) wolfc2=0.9
    IF(wolfc1 > wolfc2) THEN ! exchange
        wolfc3=wolfc1
        wolfc1=wolfc2
        wolfc2=wolfc3
    ELSE
        wolfc1=1.0E-4
        wolfc2=0.9
    END IF
    WRITE(*,105) wolfc1,wolfc2
    WRITE(lun,105) wolfc1,wolfc2
105 FORMAT(' Constants C1, C2 for Wolfe conditions:',g12.4,', ',g12.4)

    !     prepare matrix and gradient storage ------------------------------
    !32 CONTINUE
32  matsiz(1)=int8(nagb)*int8(nagb+1)/2 ! number of words for double precision storage 'j'
    matsiz(2)=0                         ! number of words for single precision storage '.'
    IF(matsto == 2) THEN     ! sparse matrix
        matsiz(1)=ndimsa(3)+nagb
        matsiz(2)=ndimsa(4)
        CALL mpalloc(sparseMatrixColumns,ndimsa(2),'sparse matrix column list')
        CALL spbits(sparseMatrixOffsets,sparseMatrixColumns,sparseMatrixCompression)
    END IF
    matwords=matwords+matsiz(1)*2+matsiz(2) ! #words for matrix storage

    CALL feasma    ! prepare constraint matrices

    CALL vmprep(matsiz)    ! prepare matrix and gradient storage
    WRITE(*,*) ' '
    IF (matwords < 250000) THEN
        WRITE(*,*) 'Size of global matrix: < 1 MB'
    ELSE
        WRITE(*,*) 'Size of global matrix:',INT(REAL(matwords,mps)*4.0E-6,mpi),' MB'
    ENDIF
    !     print chi^2 cut tables

    ndfmax=naeqn-1
    WRITE(lunlog,*) ' '
    WRITE(lunlog,*) '   Cut values of Chi^2/Ndf and Chi2,'
    WRITE(lunlog,*) '   corresponding to 2 and 3 standard deviations'
    WRITE(lunlog,*) '   Ndf  Chi^2/Ndf(2)  Chi^2(2)   ',  &
        '  Chi^2/Ndf(3)  Chi^2(3)'
    ndf=0
    DO
        IF(ndf > naeqn) EXIT
        IF(ndf < 10) THEN
            ndf=ndf+1
        ELSE IF(ndf < 20) THEN
            ndf=ndf+2
        ELSE IF(ndf < 100) THEN
            ndf=ndf+5
        ELSE IF(ndf < 200) THEN
            ndf=ndf+10
        ELSE
            EXIT
        END IF
        chin2=chindl(2,ndf)
        chin3=chindl(3,ndf)
        WRITE(lunlog,106) ndf,chin2,chin2*REAL(ndf,mps),chin3, chin3*REAL(ndf,mps)
    END DO

    WRITE(lunlog,*) 'LOOP2: ending'
    WRITE(lunlog,*) ' '
    CALL mend
101 FORMAT(1X,a8,' =',i10,' = ',a)
102 FORMAT(22X,a)
103 FORMAT(1X,a,g12.4)
106 FORMAT(i6,2(3X,f9.3,f12.1,3X))
END SUBROUTINE loop2

!> Monitor input residuals.
!!
!! Read all data files again to monitor input residuals
!!
SUBROUTINE monres
    USE mpmod
    USE mpdalc

    IMPLICIT NONE
    INTEGER(mpi) :: i
    INTEGER(mpi) :: ij
    INTEGER(mpi) :: imed
    INTEGER(mpi) :: j
    INTEGER(mpi) :: k
    INTEGER(mpi) :: nent
    INTEGER(mpi), DIMENSION(measBins) :: isuml ! location
    INTEGER(mpi), DIMENSION(measBins) :: isums ! scale
    REAL(mps) :: amed
    REAL(mps) :: amad
    
    INTEGER(mpl) :: ioff
    LOGICAL :: lfirst
    SAVE
    DATA lfirst /.TRUE./

    ! combine data from threads
    ioff=0
    DO i=2,mthrd
        ioff=ioff+measBins*numMeas
        DO j=1,measBins*numMeas
            measHists(j)=measHists(j)+measHists(ioff+j)
        END DO
    END DO
    
    IF (lfirst) THEN
        IF (imonmd == 0) THEN
            WRITE(lunmon,'(A)') '*** Normalized residuals grouped by first global label (per local fit cycle) ***'
        ELSE
            WRITE(lunmon,'(A)') '*** Pulls grouped by first global label (per local fit cycle) ***'
        ENDIF
        WRITE(lunmon,'(A)') '! LFC     Label   Entries        Median  RMS(MAD)          <error>'
        lfirst=.false.
    END IF

    ! analyze histograms
    ioff=0
    DO i=1,ntgb
        IF (measIndex(i) > 0) THEN
            isuml=0
            ! sum up content                                                                     
            isuml(1)=measHists(ioff+1)                                                           
            DO j=2,measBins                                                                      
                isuml(j)=isuml(j-1)+measHists(ioff+j)                                            
            END DO                                                                              
            nent=isuml(measBins)                                                                 
            ! get median (for location)                                                          
            DO j=2,measBins                                                                      
                IF (2*isuml(j) > nent) EXIT                                                      
            END DO                                                                               
            imed=j                                                                               
            amed=REAL(j,mps)
            IF (isuml(j) > isuml(j-1)) amed=amed+REAL(nent-2*isuml(j-1),mps)/REAL(2*isuml(j)-2*isuml(j-1),mps)     
            amed=REAL(measBinSize,mps)*(amed-REAL(measBins/2,mps))
            ! sum up differences                                                                 
            isums = 0                                                                            
            DO j=imed,measBins                                                                   
                k=j-imed+1                                                                       
                isums(k)=isums(k)+measHists(ioff+j)                                              
            END DO                                                                               
            DO j=imed-1,1,-1                                                                     
                k=imed-j                                                                         
                isums(k)=isums(k)+measHists(ioff+j)                                              
            END DO                                                                               
            DO j=2, measBins                                                                     
                isums(j)=isums(j)+isums(j-1)
            END DO                                                                               
            ! get median (for scale)                                                             
            DO j=2,measBins                                                                      
                IF (2*isums(j) > nent) EXIT                                                      
            END DO                                                                               
            amad=REAL(j-1,mps)
            IF (isums(j) > isums(j-1)) amad=amad+REAL(nent-2*isums(j-1),mps)/REAL(2*isums(j)-2*isums(j-1),mps)     
            amad=REAL(measBinSize,mps)*amad
            ij=globalParLabelIndex(1,i)                                                    
            WRITE(lunmon,110) nloopn, ij, nent, amed, amad*1.4826, REAL(measRes(i),mps)                                        
            !                                                                                    
            ioff=ioff+measBins
        END IF                                                                   
    END DO
 
110 FORMAT(i5,2i10,3G14.5)
END SUBROUTINE monres


!> Prepare storage for vectors and matrices.
!!
!! \param[in] msize number of words for storage of global matrix (double, single prec.)

SUBROUTINE vmprep(msize)
    USE mpmod
    USE mpdalc

    IMPLICIT NONE
    INTEGER(mpi) :: i
    INTEGER(mpi) :: ncon
                         !
    INTEGER(mpl), INTENT(IN) :: msize(2)

    INTEGER(mpl) :: length
    SAVE
    !     ...
    !                         Vector/matrix storage
    length=nagb*mthrd
    CALL mpalloc(globalVector,length,'rhs vector') ! double precision vector
    CALL mpalloc(globalCounter,length,'rhs counter') ! integer vector
    lenGlobalVec=nagb
    length=naeqn
    CALL mpalloc(localCorrections,length,'residual vector of one record')
    length=nalcn*nalcn
    CALL mpalloc(aux,length,' local fit scratch array: aux')
    CALL mpalloc(vbnd,length,' local fit scratch array: vbnd')
    CALL mpalloc(vbdr,length,' local fit scratch array: vbdr')
    length=((nalcn+1)*nalcn)/2
    CALL mpalloc(clmat,length,' local fit matrix: clmat')
    CALL mpalloc(vbk,length,' local fit scratch array: vbk')
    length=nalcn
    CALL mpalloc(blvec,length,' local fit vector: blvec')
    CALL mpalloc(vzru,length,' local fit scratch array: vzru')
    CALL mpalloc(scdiag,length,' local fit scratch array: scdiag')
    CALL mpalloc(scflag,length,' local fit scratch array: scflag')
    CALL mpalloc(ibandh,2*length,' local fit band width hist.: ibandh')

    CALL mpalloc(globalMatD,msize(1),'global matrix (D)' )
    CALL mpalloc(globalMatF,msize(2),'global matrix (F)')

    IF(metsol >= 3) THEN                  ! GMRES/MINRES algorithms
        !        array space is:
        !           variable-width band matrix or diagonal matrix for parameters
        !           followed by rectangular matrix for constraints
        !           followed by symmetric matrix for constraints
        ncon=nagb-nvgb
        IF(mbandw > 0) THEN               ! variable-width band matrix
            length=nagb
            CALL mpalloc(indPreCond,length,'pointer-array variable-band matrix')
            DO i=1,MIN(mbandw,nvgb)
                indPreCond(i)=(i*i+i)/2           ! increasing number
            END DO
            DO i=MIN(mbandw,nvgb)+1,nvgb
                indPreCond(i)=indPreCond(i-1)+mbandw ! fixed band width
            END DO
            DO i=nvgb+1,nagb                ! reset
                indPreCond(i)=0
            END DO
            length=indPreCond(nvgb)+ncon*nvgb+(ncon*ncon+ncon)/2
            CALL mpalloc(matPreCond,length,'variable-band matrix')
        ELSE                               ! default preconditioner
            length=nvgb+ncon*nvgb+(ncon*ncon+ncon)/2
            CALL mpalloc(matPreCond,length,'default preconditioner matrix')
        END IF
    END IF


    length=nagb
    CALL mpalloc(globalCorrections,length,'corrections')      ! double prec corrections

    CALL mpalloc(workspaceD,length,'auxiliary array (D1)')  ! double aux 1
    CALL mpalloc(workspaceLinesearch,length,'auxiliary array (D2)')  ! double aux 2
    CALL mpalloc(workspaceI, length,'auxiliary array (I)')   ! int aux 1

    IF(metsol == 1) THEN
        CALL mpalloc(workspaceDiag,length,'diagonal of global matrix)')  ! double aux 1
    !         CALL MEGARR('t D',2*NAGB,'auxiliary array')  ! double aux 8
    END IF

    IF(metsol == 2) THEN
        CALL mpalloc(workspaceDiag,length,'diagonal of global matrix')  ! double aux 1
        CALL mpalloc(workspaceDiagonalization,length,'auxiliary array (D3)')  ! double aux 3
        CALL mpalloc(workspaceEigenValues,length,'auxiliary array (D6)')  ! double aux 6
        length=nagb*nagb
        CALL mpalloc(workspaceEigenVectors,length,'(rotation) matrix U')   ! rotation matrix
    END IF

    IF(metsol >= 3) THEN
        CALL mpalloc(vecXav,length,'vector X (AVPROD)')  ! double aux 1
        CALL mpalloc(vecBav,length,'vector B (AVPROD)')  ! double aux 1
    END IF

END SUBROUTINE vmprep

!> Solution by matrix inversion.
!!
!! Parallelized (SQMINL), solve A*x=b.

SUBROUTINE minver
    USE mpmod

    IMPLICIT NONE
    INTEGER(mpi) :: i
    INTEGER(mpl) :: ioff1
    INTEGER(mpi) :: j
    INTEGER(mpi) :: lun
    INTEGER(mpi) :: nrank
    INTEGER(mpl) :: ii
    EXTERNAL avprd0

    SAVE
    !     ...
    lun=lunlog                       ! log file
    IF(lunlog == 0) lunlog=6

    ! save diagonal (for global correlation)
    IF(icalcm == 1) THEN
        DO i=1,nagb 
            ii=i
            workspaceDiag(i)=globalMatD((ii*ii+ii)/2) ! save diagonal elements
        END DO
    ENDIF

    !      WRITE(*,*) 'MINVER ICALCM=',ICALCM
    !use elimination for constraints ?
    IF(nfgb < nvgb) THEN
        IF(icalcm == 1) CALL qlssq(avprd0,globalMatD,.true.) ! Q^t*A*Q
        ! solve L^t*y=d by backward substitution
        CALL qlbsub(vecConsResiduals,vecConsSolution)
        ! transform, reduce rhs
        CALL qlmlq(globalCorrections,1,.true.) ! Q^t*b
        ! correction from eliminated part
        DO i=1,nfgb
            ioff1=((nfgb+1)*nfgb)/2+i
            DO j=1,ncgb
                globalCorrections(i)=globalCorrections(i)-globalMatD(ioff1)*vecConsSolution(j)
                ioff1=ioff1+nfgb+j
            END DO
        END DO
    END IF

    IF(icalcm == 1) THEN
        ! invert and solve
        CALL sqminl(globalMatD, globalCorrections,nfgb,nrank,  &
            workspaceD,workspaceI)
        IF(nfgb /= nrank) THEN
            WRITE(*,*)   'Warning: the rank defect of the symmetric',nfgb,  &
                '-by-',nfgb,' matrix is ',nfgb-nrank,' (should be zero).'
            WRITE(lun,*) 'Warning: the rank defect of the symmetric',nfgb,  &
                '-by-',nfgb,' matrix is ',nfgb-nrank,' (should be zero).'
            IF (iforce == 0 .AND. isubit == 0) THEN
                isubit=1
                WRITE(*,*)   '         --> enforcing SUBITO mode'
                WRITE(lun,*) '         --> enforcing SUBITO mode'
            END IF
        ELSE IF(ndefec == 0) THEN
            WRITE(lun,*) 'No rank defect of the symmetric matrix'
        END IF
        ndefec=max(nfgb-nrank, ndefec)   ! rank defect

    ELSE             ! multiply gradient by inverse matrix
        workspaceD(:nfgb)=globalCorrections(:nfgb)
        CALL dbsvxl(globalMatD,workspaceD,globalCorrections,nfgb)
    END IF

    !use elimination for constraints ?
    IF(nfgb < nvgb) THEN  
        ! extend, transform back solution
        globalCorrections(nfgb+1:nvgb)=vecConsSolution(1:ncgb)
        CALL qlmlq(globalCorrections,1,.false.) ! Q*x
    END IF

END SUBROUTINE minver

!> Solution by diagonalization.
SUBROUTINE mdiags
    USE mpmod

    IMPLICIT NONE
    REAL(mps) :: evalue
    INTEGER(mpi) :: i
    INTEGER(mpi) :: iast
    INTEGER(mpi) :: idia
    INTEGER(mpi) :: imin
    INTEGER(mpl) :: ioff1
    INTEGER(mpi) :: j
    INTEGER(mpi) :: lun
    INTEGER(mpi) :: nmax
    INTEGER(mpi) :: nmin
    INTEGER(mpi) :: ntop
                                       !
    INTEGER(mpl) :: ii
    EXTERNAL avprd0

    SAVE
    !     ...

    lun=lunlog                       ! log file
    IF(lunlog == 0) lun=6

    ! save diagonal (for global correlation)
    IF(icalcm == 1) THEN
        DO i=1,nagb 
            ii=i
            workspaceDiag(i)=globalMatD((ii*ii+ii)/2) ! save diagonal elements
        END DO
    ENDIF

    !use elimination for constraints ?
    IF(nfgb < nvgb) THEN
        IF(icalcm == 1) CALL qlssq(avprd0,globalMatD,.true.) ! Q^t*A*Q
        ! solve L^t*y=d by backward substitution
        CALL qlbsub(vecConsResiduals,vecConsSolution)
        ! transform, reduce rhs
        CALL qlmlq(globalCorrections,1,.true.) ! Q^t*b
        ! correction from eliminated part
        DO i=1,nfgb
            ioff1=((nfgb+1)*nfgb)/2+i
            DO j=1,ncgb
                globalCorrections(i)=globalCorrections(i)-globalMatD(ioff1)*vecConsSolution(j)
                ioff1=ioff1+nfgb+j
            END DO
        END DO
    END IF

    IF(icalcm == 1) THEN
        !                         eigenvalues   eigenvectors   symm_input
        workspaceEigenValues=0.0_mpd
        CALL devrot(nfgb,workspaceEigenValues,workspaceEigenVectors,globalMatD,  &
            workspaceDiagonalization,workspaceI)
  
        !        histogram of positive eigenvalues
  
        nmax=INT(1.0+LOG10(REAL(workspaceEigenValues(1),mps)),mpi) ! > log of largest eigenvalue
        imin=1
        DO i=nagb,1,-1
            IF(workspaceEigenValues(i) > 0.0_mpd) THEN
                imin=i ! index of smallest pos. eigenvalue
                EXIT
            END IF
        END DO
        nmin=INT(LOG10(REAL(workspaceEigenValues(imin),mps)),mpi)   ! log of smallest pos. eigenvalue
        ntop=nmin+6
        DO WHILE(ntop < nmax)
            ntop=ntop+3
        END DO
  
        CALL hmpdef(7,REAL(nmin,mps),REAL(ntop,mps), 'log10 of positive eigenvalues')
        DO idia=1,nagb
            IF(workspaceEigenValues(idia) > 0.0_mpd) THEN ! positive
                evalue=LOG10(REAL(workspaceEigenValues(idia),mps))
                CALL hmpent(7,evalue)
            END IF
        END DO
        IF(nhistp /= 0) CALL hmprnt(7)
        CALL hmpwrt(7)
  
        iast=MAX(1,imin-60)
        CALL gmpdef(3,2,'low-value end of eigenvalues')
        DO i=iast,nagb
            evalue=REAL(workspaceEigenValues(i),mps)
            CALL gmpxy(3,REAL(i,mps),evalue)
        END DO
        IF(nhistp /= 0) CALL gmprnt(3)
        CALL gmpwrt(3)
  
        DO i=1,nfgb
            workspaceDiagonalization(i)=0.0_mpd
            IF(workspaceEigenValues(i) /= 0.0_mpd) THEN
                workspaceDiagonalization(i)=MAX(0.0_mpd,LOG10(ABS(workspaceEigenValues(i)))+3.0_mpd)
                IF(workspaceEigenValues(i) < 0.0_mpd) workspaceDiagonalization(i)=-workspaceDiagonalization(i)
            END IF
        END DO
        WRITE(lun,*) ' '
        WRITE(lun,*) 'The first (largest) eigenvalues ...'
        WRITE(lun,102) (workspaceEigenValues(i),i=1,MIN(20,nagb))
        WRITE(lun,*) ' '
        WRITE(lun,*) 'The last eigenvalues ... up to',nvgb
        WRITE(lun,102) (workspaceEigenValues(i),i=MAX(1,nvgb-19),nvgb)
        WRITE(lun,*) ' '
        IF(nagb > nvgb) THEN
            WRITE(lun,*) 'The eigenvalues from',nvgb+1,' to',nagb
            WRITE(lun,102) (workspaceEigenValues(i),i=nvgb+1,nagb)
            WRITE(lun,*) ' '
        ENDIF
        WRITE(lun,*) 'Log10 + 3 of ',nagb,' eigenvalues in decreasing', ' order'
        WRITE(lun,*) '(for Eigenvalue < 0.001 the value 0.0 is shown)'
        WRITE(lun,101) (workspaceDiagonalization(i),i=1,nagb)
        IF(workspaceDiagonalization(nfgb) < 0) WRITE(lun,*) 'Negative values are ',  &
            'printed for negative eigenvalues'
        CALL devsig(nfgb,workspaceEigenValues,workspaceEigenVectors,globalVector,workspaceDiagonalization)
        WRITE(lun,*) ' '
        WRITE(lun,*) nvgb,' significances: insignificant if ',  &
            'compatible with  N(0,1)'
        WRITE(lun,101) (workspaceDiagonalization(i),i=1,nvgb)
  
  
101     FORMAT(10F7.1)
102     FORMAT(5E14.6)

    END IF

    !     solution ---------------------------------------------------------
    workspaceD(:nfgb)=globalCorrections(:nfgb)
    !                      eigenvalues   eigenvectors
    CALL devsol(nfgb,workspaceEigenValues,workspaceEigenVectors,workspaceD,globalCorrections,workspaceDiagonalization)

    !use elimination for constraints ?
    IF(nfgb < nvgb) THEN  
        ! extend, transform back solution
        globalCorrections(nfgb+1:nvgb)=vecConsSolution(1:ncgb)
        CALL qlmlq(globalCorrections,1,.false.) ! Q*x
    END IF

END SUBROUTINE mdiags

!> Covariance matrix for diagonalization (,correction of eigenvectors).
SUBROUTINE zdiags
    USE mpmod

    IMPLICIT NONE
    INTEGER(mpi) :: i
    INTEGER(mpl) :: ioff1
    INTEGER(mpl) :: ioff2
    INTEGER(mpi) :: j

    !                      eigenvalue    eigenvectors  cov.matrix
    CALL devinv(nfgb,workspaceEigenValues,workspaceEigenVectors,globalMatD)  ! inv

    !use elimination for constraints ?
    IF(nfgb < nvgb) THEN  
        ! extend, transform eigenvectors
        ioff1=nfgb*nfgb
        ioff2=nfgb*nvgb
        workspaceEigenVectors(ioff2+1:)=0.0_mpd
        DO i=nfgb,1,-1
            ioff1=ioff1-nfgb
            ioff2=ioff2-nvgb
            DO j=nfgb,1,-1
                workspaceEigenVectors(ioff2+j)=workspaceEigenVectors(ioff1+j)
            END DO
            workspaceEigenVectors(ioff2+nfgb+1:ioff2+nvgb)=0.0_mpd
        END DO
        CALL qlmlq(workspaceEigenVectors,nvgb,.false.) ! Q*U
    END IF

END SUBROUTINE zdiags

!> Solution with \ref minresmodule::minres "MINRES".
!!
!! Solve A*x=b by minimizing |A*x-b| iteratively. Parallelized (AVPROD).
!!
!! Use preconditioner with zero (precon) or finite (equdec) band width.

SUBROUTINE mminrs
    USE mpmod
    USE minresModule, ONLY: minres

    IMPLICIT NONE
    INTEGER(mpi) :: istop
    INTEGER(mpi) :: itn
    INTEGER(mpi) :: itnlim
    INTEGER(mpi) :: lun
    INTEGER(mpi) :: nout
    INTEGER(mpi) :: nrkd
    INTEGER(mpi) :: nrkd2

    REAL(mpd) :: shift
    REAL(mpd) :: rtol
    REAL(mpd) :: anorm
    REAL(mpd) :: acond
    REAL(mpd) :: arnorm
    REAL(mpd) :: rnorm
    REAL(mpd) :: ynorm
    LOGICAL :: checka
    EXTERNAL avprd0, avprod, mvsolv, mcsolv
    SAVE
    !     ...
    lun=lunlog                       ! log file
    IF(lunlog == 0) lun=6

    nout=lun
    itnlim=2000    ! iteration limit
    shift =0.0_mpd   ! not used
    rtol = mrestl ! from steering
    checka=.FALSE.

    workspaceD = globalCorrections
    !use elimination for constraints ?
    IF(nfgb < nvgb) THEN
        ! solve L^t*y=d by backward substitution
        CALL qlbsub(vecConsResiduals,vecConsSolution)
        ! input to AVPRD0
        vecXav(1:nfgb)=0.0_mpd
        vecXav(nfgb+1:nagb)=vecConsSolution
        CALL qlmlq(vecXav,1,.false.) ! Q*x
        ! calclulate vecBav=globalMat*vecXav
        CALL AVPRD0(nagb,vecXav,vecBav)
        ! correction from eliminated part
        workspaceD=workspaceD-vecBav
        ! transform, reduce rhs
        CALL qlmlq(workspaceD,1,.true.) ! Q^t*b
    END IF

    IF(mbandw == 0) THEN           ! default preconditioner
        IF(icalcm == 1) THEN
            IF(nfgb < nvgb) CALL qlpssq(avprd0,matPreCond,1,.true.) ! transform preconditioner matrix
            CALL precon(nprecond(1),nprecond(2),matPreCond,matPreCond, matPreCond(1+nvgb),  &
                matPreCond(1+nvgb+ncgb*nvgb),nrkd)
        END IF
        CALL minres(nfgb,  avprod, mcsolv, workspaceD, shift, checka ,.TRUE. , &
            globalCorrections, itnlim, nout, rtol, istop, itn, anorm, acond, rnorm, arnorm, ynorm)
    ELSE IF(mbandw > 0) THEN                          ! band matrix preconditioner
        IF(icalcm == 1) THEN
            IF(nfgb < nvgb) CALL qlpssq(avprd0,matPreCond,mbandw,.true.) ! transform preconditioner matrix
            WRITE(lun,*) 'MMINRS: EQUDEC started', nprecond(2), nprecond(1)
            CALL equdec(nprecond(2),nprecond(1),lprecm,matPreCond,indPreCond,nrkd,nrkd2)
            WRITE(lun,*) 'MMINRS: EQUDEC ended  ', nrkd, nrkd2
        END IF
        CALL minres(nfgb,  avprod, mvsolv, workspaceD, shift, checka ,.TRUE. , &
            globalCorrections, itnlim, nout, rtol, istop, itn, anorm, acond, rnorm, arnorm, ynorm)
    ELSE
        CALL minres(nfgb,  avprod, mvsolv, workspaceD, shift, checka ,.FALSE. , &
            globalCorrections, itnlim, nout, rtol, istop, itn, anorm, acond, rnorm, arnorm, ynorm)
    END IF

    !use elimination for constraints ?
    IF(nfgb < nvgb) THEN  
        ! extend, transform back solution
        globalCorrections(nfgb+1:nvgb)=vecConsSolution(1:ncgb)
        CALL qlmlq(globalCorrections,1,.false.) ! Q*x
    END IF

    iitera=itn
    istopa=istop
    mnrsit=mnrsit+itn

    IF (istopa == 0) PRINT *, 'MINRES: istop=0, exact solution x=0.'

END SUBROUTINE mminrs

!> Solution with \ref minresqlpmodule::minresqlp "MINRES-QLP".
!!
!! Solve A*x=b by minimizing |A*x-b| iteratively. Parallelized (AVPROD).
!!
!! Use preconditioner with zero (precon) or finite (equdec) band width.

SUBROUTINE mminrsqlp
    USE mpmod
    USE minresqlpModule, ONLY: minresqlp

    IMPLICIT NONE
    INTEGER(mpi) :: istop
    INTEGER(mpi) :: itn
    INTEGER(mpi) :: itnlim
    INTEGER(mpi) :: lun
    INTEGER(mpi) :: nout
    INTEGER(mpi) :: nrkd
    INTEGER(mpi) :: nrkd2

    REAL(mpd) :: rtol
    REAL(mpd) :: mxxnrm
    REAL(mpd) :: trcond

    EXTERNAL avprd0, avprod, mvsolv, mcsolv
    SAVE
    !     ...
    lun=lunlog                       ! log file
    IF(lunlog == 0) lun=6

    nout=lun
    itnlim=2000    ! iteration limit
    rtol = mrestl ! from steering
    mxxnrm = REAL(nagb,mpd)/SQRT(epsilon(mxxnrm))
    IF(mrmode == 1) THEN
        trcond = 1.0_mpd/epsilon(trcond) ! only QR
    ELSE IF(mrmode == 2) THEN
        trcond = 1.0_mpd ! only QLP
    ELSE
        trcond = mrtcnd ! QR followed by QLP
    END IF

    workspaceD = globalCorrections
    !use elimination for constraints ?
    IF(nfgb < nvgb) THEN
        ! solve L^t*y=d by backward substitution
        CALL qlbsub(vecConsResiduals,vecConsSolution)
        ! input to AVPRD0
        vecXav(1:nfgb)=0.0_mpd
        vecXav(nfgb+1:nagb)=vecConsSolution
        CALL qlmlq(vecXav,1,.false.) ! Q*x
        ! calclulate vecBav=globalMat*vecXav
        CALL AVPRD0(nagb,vecXav,vecBav)
        ! correction from eliminated part
        workspaceD=workspaceD-vecBav
        ! transform, reduce rhs
        CALL qlmlq(workspaceD,1,.true.) ! Q^t*b
    END IF

    IF(mbandw == 0) THEN           ! default preconditioner
        IF(icalcm == 1) THEN
            IF(nfgb < nvgb) CALL qlpssq(avprd0,matPreCond,1,.true.) ! transform preconditioner matrix
            CALL precon(nprecond(1),nprecond(2),matPreCond,matPreCond, matPreCond(1+nvgb),  &
                matPreCond(1+nvgb+ncgb*nvgb),nrkd)
        END IF
        CALL minresqlp( n=nfgb, Aprod=avprod, b=workspaceD,  Msolve=mcsolv, nout=nout, &
            itnlim=itnlim, rtol=rtol, maxxnorm=mxxnrm, trancond=trcond, &
            x=globalCorrections, istop=istop, itn=itn)
    ELSE IF(mbandw > 0) THEN                          ! band matrix preconditioner
        IF(icalcm == 1) THEN
            IF(nfgb < nvgb) CALL qlpssq(avprd0,matPreCond,mbandw,.true.) ! transform preconditioner matrix
            WRITE(lun,*) 'MMINRS: EQUDEC started', nprecond(2), nprecond(1)
            CALL equdec(nprecond(2),nprecond(1),lprecm,matPreCond,indPreCond,nrkd,nrkd2)
            WRITE(lun,*) 'MMINRS: EQUDEC ended  ', nrkd, nrkd2
        END IF

        CALL minresqlp( n=nfgb, Aprod=avprod, b=workspaceD,  Msolve=mvsolv, nout=nout, &
            itnlim=itnlim, rtol=rtol, maxxnorm=mxxnrm, trancond=trcond, &
            x=globalCorrections, istop=istop, itn=itn)
    ELSE
        CALL minresqlp( n=nfgb, Aprod=avprod, b=workspaceD, nout=nout, &
            itnlim=itnlim, rtol=rtol, maxxnorm=mxxnrm, trancond=trcond, &
            x=globalCorrections, istop=istop, itn=itn)
    END IF

    !use elimination for constraints ?
    IF(nfgb < nvgb) THEN  
        ! extend, transform back solution
        globalCorrections(nfgb+1:nvgb)=vecConsSolution(1:ncgb)
        CALL qlmlq(globalCorrections,1,.false.) ! Q*x
    END IF

    iitera=itn
    istopa=istop
    mnrsit=mnrsit+itn

    IF (istopa == 3) PRINT *, 'MINRES: istop=0, exact solution x=0.'

END SUBROUTINE mminrsqlp

!> Solution for zero band width preconditioner.
!!
!! Used by \ref minresmodule::minres "MINRES".
!!
!! \param[in]      n     size of vectors
!! \param [in]     x     rhs vector
!! \param [out]    y     result vector

SUBROUTINE mcsolv(n,x,y)         !  solve M*y = x
    USE mpmod

    IMPLICIT NONE
    INTEGER(mpi),INTENT(IN) :: n
    REAL(mpd), INTENT(IN)  :: x(n)
    REAL(mpd), INTENT(OUT) :: y(n)
    SAVE
    !     ...
    CALL presol(nprecond(1),nprecond(2),matPreCond,matPreCond(1+nvgb),matPreCond(1+nvgb+ncgb*nvgb),y,x)
END SUBROUTINE mcsolv

!> Solution for finite band width preconditioner.
!!
!! Used by \ref minresmodule::minres "MINRES".
!!
!! \param[in]      n     size of vectors
!! \param [in]     x     rhs vector
!! \param [out]    y     result vector

SUBROUTINE mvsolv(n,x,y)         !  solve M*y = x
    USE mpmod

    IMPLICIT NONE

    INTEGER(mpi), INTENT(IN) :: n
    REAL(mpd), INTENT(IN)  :: x(n)
    REAL(mpd), INTENT(OUT) :: y(n)
    
    SAVE
    !     ...
    y=x                    ! copy to output vector

    CALL equslv(nprecond(2),nprecond(1),matPreCond,indPreCond,y)
END SUBROUTINE mvsolv



!***********************************************************************

!> Standard solution algorithm.
!!
!! \ref sssec-solmetover "Iterative solution".
!! In current \ref par-iter "iteration" calculate:
!!
!!     ICALCM = +1   Matrix, gradient, Function value & solution
!!     ICALCM =  0   gradient, Function value
!!     ICALCM = -1   solution
!!     ICALCM = -2   end
!!
!! \ref sssec-glofit "Solution" is obtained by selected method and
!! improved by \ref par-linesearch "line search".

SUBROUTINE xloopn                !
    USE mpmod

    IMPLICIT NONE
    REAL(mps) :: catio
    REAL(mps) :: concu2
    REAL(mps) :: concut
    REAL, DIMENSION(2) :: ta
    INTEGER(mpi) :: i
    INTEGER(mpi) :: iact
    INTEGER(mpi) :: iagain
    INTEGER(mpi) :: idx
    INTEGER(mpi) :: info
    INTEGER(mpl) :: ioff
    INTEGER(mpi) :: itgbi
    INTEGER(mpi) :: ivgbi
    INTEGER(mpi) :: jcalcm
    INTEGER(mpi) :: k
    INTEGER(mpi) :: labelg
    INTEGER(mpi) :: litera
    INTEGER(mpi) :: lrej
    INTEGER(mpi) :: lun
    INTEGER(mpi) :: lunp
    INTEGER(mpi) :: minf
    INTEGER(mpi) :: mrati
    INTEGER(mpi) :: nan
    INTEGER(mpi) :: nfaci
    INTEGER(mpi) :: nloopsol
    INTEGER(mpi) :: nrati
    INTEGER(mpi) :: nrej
    INTEGER(mpi) :: nsol
    INTEGER(mpi) :: inone

    REAL(mpd) :: stp
    REAL(mpd) :: dratio
    REAL(mpd) :: dwmean
    REAL(mpd) :: db
    REAL(mpd) :: db1
    REAL(mpd) :: db2
    REAL(mpd) :: dbdot
    LOGICAL :: btest
    LOGICAL :: warner
    LOGICAL :: warners
    LOGICAL :: warnerss
    LOGICAL :: lsflag
    CHARACTER (LEN=7) :: cratio
    CHARACTER (LEN=7) :: cfacin
    CHARACTER (LEN=7) :: crjrat
    EXTERNAL avprd0
    SAVE
    !     ...

    !     Printout of algorithm for solution and important parameters ------

    lun=lunlog                       ! log file
    IF(lunlog == 0) lunlog=6

    DO lunp=6,lunlog,lunlog-6
        WRITE(lunp,*) ' '
        WRITE(lunp,*) 'Solution algorithm: '
        WRITE(lunp,121) '=================================================== '
  
        IF(metsol == 1) THEN
            WRITE(lunp,121) 'solution method:','matrix inversion'
        ELSE IF(metsol == 2) THEN
            WRITE(lunp,121) 'solution method:','diagonalization'
        ELSE IF(metsol == 3) THEN
            WRITE(lunp,121) 'solution method:', 'minres (Paige/Saunders)'
        ELSE IF(metsol == 4) THEN
            WRITE(lunp,121) 'solution method:', 'minres-qlp (Choi/Paige/Saunders)'
            IF(mrmode == 1) THEN
                WRITE(lunp,121) ' ', '   using QR factorization' ! only QR
            ELSE IF(mrmode == 2) THEN
                WRITE(lunp,121) ' ', '   using QLP factorization' ! only QLP
            ELSE
                WRITE(lunp,121) ' ', '   using QR and QLP factorization' ! QR followed by QLP
                WRITE(lunp,123) 'transition condition', mrtcnd
            END IF
        ELSE IF(metsol == 5) THEN
            WRITE(lunp,121) 'solution method:',  &
                'gmres (generalized minimzation of residuals)'
        END IF
        WRITE(lunp,123) 'convergence limit at Delta F=',dflim
        WRITE(lunp,122) 'maximum number of iterations=',mitera
        matrit=MIN(matrit,mitera)
        IF(matrit > 1) THEN
            WRITE(lunp,122) 'matrix recalculation up to ',matrit, '. iteration'
        END IF
        IF(metsol >= 3) THEN
            IF(matsto == 1) THEN
                WRITE(lunp,121) 'matrix storage:','full'
            ELSE IF(matsto == 2) THEN
                WRITE(lunp,121) 'matrix storage:','sparse'
            END IF
            WRITE(lunp,122) 'pre-con band-width parameter=',mbandw
            IF(mbandw == 0) THEN
                WRITE(lunp,121) 'pre-conditioning:','default'
            ELSE IF(mbandw < 0) THEN
                WRITE(lunp,121) 'pre-conditioning:','none!'
            ELSE IF(mbandw > 0) THEN
                IF(lprecm > 0) THEN
                    WRITE(lunp,121) 'pre-conditioning=','skyline-matrix (rank preserving)'
                ELSE
                    WRITE(lunp,121) 'pre-conditioning=','band-matrix'
                ENDIF
            END IF
        END IF
        IF(regpre == 0.0_mpd.AND.npresg == 0) THEN
            WRITE(lunp,121) 'using pre-sigmas:','no'
        ELSE
            ! FIXME: NPRESG contains parameters that failed the 'entries' cut...
            WRITE(lunp,124) 'pre-sigmas defined for',  &
                REAL(100*npresg,mps)/REAL(nvgb,mps),' % of variable parameters'
            WRITE(lunp,123) 'default pre-sigma=',regpre
        END IF
        IF(nregul == 0) THEN
            WRITE(lunp,121) 'regularization:','no'
        ELSE
            WRITE(lunp,121) 'regularization:','yes'
            WRITE(lunp,123) 'regularization factor=',regula
        END IF
  
        IF(chicut /= 0.0) THEN
            WRITE(lunp,121) 'Chi square cut equiv 3 st.dev applied'
            WRITE(lunp,123) '... in first iteration with factor',chicut
            WRITE(lunp,123) '... in second iteration with factor',chirem
            WRITE(lunp,121) ' (reduced by sqrt in next iterations)'
        END IF
        IF(iscerr > 0) THEN
            WRITE(lunp,121) 'Scaling of measurement errors applied'
            WRITE(lunp,123) '... factor for "global" measuements',dscerr(1)
            WRITE(lunp,123) '... factor for "local"  measuements',dscerr(2)
        END IF 
        IF(lhuber /= 0) THEN
            WRITE(lunp,122) 'Down-weighting of outliers in', lhuber,' iterations'
            WRITE(lunp,123) 'Cut on downweight fraction',dwcut
        END IF
  
  
121     FORMAT(1X,a40,3X,a)
122     FORMAT(1X,a40,3X,i0,a)
123     FORMAT(1X,a40,2X,e9.2)
124     FORMAT(1X,a40,3X,f5.1,a)
    END DO

    !     initialization of iterations -------------------------------------

    iitera=0
    nsol  =0                  ! counter for solutions
    info  =0
    lsinfo=0
    stp   =0.0_mpd
    stepl =REAL(stp,mps)
    concut=1.0E-12            ! initial constraint accuracy
    concu2=1.0E-06            ! constraint accuracy
    icalcm=1                  ! require matrix calculation
    iterat=0                  ! iteration counter
    iterat=-1
    litera=-2
    nloopsol=0                ! (new) solution from this nloopn
    nrej=0                    ! reset number of rejects
    IF(metsol == 1) THEN
        wolfc2=0.5             ! not accurate
        minf=1
    ELSE IF(metsol == 2) THEN
        wolfc2=0.5             ! not acurate
        minf=2
    ELSE IF(metsol == 3) THEN
        wolfc2=0.1             ! accurate
        minf=3
    ELSE IF(metsol == 4) THEN
        wolfc2=0.1             ! accurate
        minf=3
    ELSE IF(metsol == 5) THEN
        wolfc2=0.1             ! accurate
        minf=3
    END IF

    !     check initial feasibility of constraint equations ----------------

    WRITE(*,*) ' '
    IF(nofeas == 0) THEN        ! make parameter feasible
        WRITE(lunlog,*) 'Checking feasibility of parameters:'
        WRITE(*,*) 'Checking feasibility of parameters:'
        CALL feasib(concut,iact) ! check feasibility
        IF(iact /= 0) THEN       ! done ...
            WRITE(*,102) concut
            WRITE(*,*) '   parameters are made feasible'
            WRITE(lunlog,102) concut
            WRITE(lunlog,*) '   parameters are made feasible'
        ELSE                     ! ... was OK
            WRITE(*,*) '   parameters are feasible  (i.e. satisfy constraints)'
            WRITE(lunlog,*) '   parameters are feasible  (i.e. satisfy constraints)'
        END IF
        concut=concu2            ! cut for constraint check
    END IF
    iact=1                      ! set flag for new data loop
    nofeas=0                    ! set check-feasibility flag

    WRITE(*,*) ' '
    WRITE(*,*)'Reading files and accumulating vectors/matrices ...'
    WRITE(*,*) ' '

    CALL etime(ta,rstart)
    iterat=-1
    litera= 0
    jcalcm=-1
    iagain= 0

    icalcm=1

    !     Block 1: data loop with vector (and matrix) calculation ----------

    DO
        IF(iterat >= 0) THEN
            lcalcm=jcalcm+3 ! mode (1..4) of last loop
            IF(jcalcm+1 /= 0) THEN
                IF(iterat == 0) THEN
                    CALL ploopa(6) ! header
                    CALL ploopb(6)
                    CALL ploopa(lunlog) ! iteration line
                    CALL ploopb(lunlog)
                    iterat=1
                    CALL gmpxyd(1,REAL(nloopn,mps),REAL(fvalue,mps),0.5,0.) ! fcn-value graph (no Delta)
                ELSE
                    IF(iterat /= litera) THEN
                        CALL ploopb(6)
                        !                  CALL PLOOPA(LUNLOG)
                        CALL ploopb(lunlog)
                        litera=iterat
                        CALL gmpxyd(1,REAL(nloopn,mps),REAL(fvalue,mps),0.5,delfun) ! fcn-value (with expected)
                        IF(metsol == 3 .OR. metsol == 4) THEN ! extend to 4, i.e. GMRES?
                            CALL gmpxy(2,REAL(iterat,mps),REAL(iitera,mps)) ! MINRES iterations
                        END IF
                    ELSE
                        CALL ploopc(6) ! sub-iteration line
                        CALL ploopc(lunlog)
                        CALL gmpxyd(1,REAL(nloopn,mps),REAL(fvalue,mps),0.5,0.) ! fcn-value graph (no Delta)
                    END IF
                END IF
            ELSE
                CALL ploopd(6) ! solution line
                CALL ploopd(lunlog)
            END IF
            CALL etime(ta,rstart)
            ! CHK
            IF (IABS(jcalcm) <= 1) THEN
                idx=jcalcm+4
                times(idx  )=(times(idx  )*times(idx+3)+deltim) /(times(idx+3)+1.0)
                times(idx+3)= times(idx+3)+1.0
            END IF
        END IF
        jcalcm=icalcm

        IF(icalcm >= 0) THEN             ! ICALCM = +1 & 0
            CALL loopn                       ! data loop
            CALL addcst                      ! constraints
            lrej=nrej
            nrej=nrejec(0)+nrejec(1)+nrejec(2)+nrejec(3) ! total number of rejects
            IF(3*nrej > nrecal) THEN
                WRITE(*,*) ' '
                WRITE(*,*) 'Data rejected in previous loop:   '
                WRITE(*,*) '   ',  &
                    nrejec(0), ' (rank deficit/NaN) ',nrejec(1),' (Ndf=0)   ',  &
                    nrejec(2), ' (huge)   ',nrejec(3),' (large)'
                WRITE(*,*) 'Too many rejects (>33.3%) - stop'
                CALL peend(26,'Aborted, too many rejects')
                STOP
            END IF
        END IF
          !     Block 2: new iteration with calculation of solution --------------

        IF(ABS(icalcm) == 1) THEN    ! ICALCM = +1 & -1
            DO i=1,nagb
                globalCorrections(i)=globalVector(i)     ! copy rhs
            END DO
            DO i=1,nvgb
                itgbi=globalParVarToTotal(i)
                workspaceLinesearch(i)=globalParameter(itgbi)  ! copy X for line search
            END DO
            iterat=iterat+1                  ! increase iteration count
            IF(metsol == 1) THEN
                CALL minver                   ! inversion
            ELSE IF(metsol == 2) THEN
                CALL mdiags                   ! diagonalization
            ELSE IF(metsol == 3) THEN
                CALL mminrs                   ! MINRES
            ELSE IF(metsol == 4) THEN
                CALL mminrsqlp                ! MINRES-QLP
            ELSE IF(metsol == 5) THEN
                WRITE(*,*) '... reserved for GMRES (not yet!)'
                CALL mminrs                   ! GMRES not yet
            END IF
            nloopsol=nloopn                   ! (new) solution for this nloopn

            !     check feasibility and evtl. make step vector feasible

            DO i=1,nvgb
                itgbi=globalParVarToTotal(i)
                globalParCopy(itgbi)=globalParameter(itgbi)               ! save
                globalParameter(itgbi)=globalParameter(itgbi)+globalCorrections(i) ! update
            END DO
            CALL feasib(concut,iact)  ! improve constraints
            concut=concu2             ! new cut for constraint check
            DO i=1,nvgb
                itgbi=globalParVarToTotal(i)
                globalCorrections(i)=globalParameter(itgbi)-globalParCopy(itgbi) ! feasible stp
                globalParameter(itgbi)=globalParCopy(itgbi)               ! restore
            END DO

            db=dbdot(nvgb,globalCorrections,globalVector)
            db1=dbdot(nvgb,globalCorrections,globalCorrections)
            db2=dbdot(nvgb,globalVector,globalVector)
            delfun=REAL(db,mps)
            angras=REAL(db/SQRT(db1*db2),mps)

            ! do line search for this iteration/solution ?
            ! lsearch >2: all, =2: all with (next) chicut =1., =1: last, <1: none
            lsflag=(lsearch > 2 .OR. (lsearch == 2 .AND. chicut < 2.25) .OR. &
                (lsearch == 1 .AND. chicut < 2.25 .AND. (delfun <= dflim .OR. iterat >= mitera)))
            IF (lsflag) THEN
                ! initialize line search based on slopes and prepare next
                CALL ptldef(wolfc2, 10.0, minf,10)
                IF(metsol == 1) THEN
                    wolfc2=0.5            ! not accurate
                    minf=3
                ELSE IF(metsol == 2) THEN
                    wolfc2=0.5            ! not acurate
                    minf=3
                ELSE IF(metsol == 3) THEN
                    wolfc2=0.1            ! accurate
                    minf=4
                ELSE IF(metsol == 4) THEN
                    wolfc2=0.1            ! accurate
                    minf=4
                ELSE IF(metsol == 5) THEN
                    wolfc2=0.1            ! accurate
                    minf=4
                END IF
            ENDIF

            ! change significantly negative ?
            IF(db <= -16.0_mpd*SQRT(max(db1,db2))*epsilon(db)) THEN
                WRITE(*,*) 'Function not decreasing:',db
                IF(db > -1.0E-3_mpd) THEN ! 100311, VB/CK: allow some margin for numerics
                    iagain=iagain+1
                    IF (iagain <= 1) THEN
                        WRITE(*,*) '... again matrix calculation'
                        icalcm=1
                        CYCLE
                    ELSE
                        WRITE(*,*) '... aborting iterations'
                        GO TO 90
                    END IF
                ELSE
                    WRITE(*,*) '... stopping iterations'
                    iagain=-1
                    GO TO 90
                END IF
            ELSE
                iagain=0
            END IF
            icalcm=0                         ! switch
        ENDIF
        !     Block 3: line searching ------------------------------------------

        IF(icalcm+2 == 0) EXIT
        IF (lsflag) THEN
            CALL ptline(nvgb,workspaceLinesearch, &   ! current parameter values
                flines, &          ! chi^2 function value
                globalVector, &    ! gradient
                globalCorrections, &   ! step vector stp
                stp, &             ! returned step factor
                info)              ! returned information
        !      WRITE(*,*) 'PTLINE returns INFO, STP=',INFO, STP
        ELSE ! skip line search
            info=10
            stepl=1.0
            IF (nloopn == nloopsol) THEN  ! new solution: update corrections
                workspaceLinesearch=workspaceLinesearch+globalCorrections
            ENDIF
        ENDIF
        lsinfo=info

        stepl=REAL(stp,mps)
        nan=0
        DO i=1,nvgb
            itgbi=globalParVarToTotal(i)
            IF ((.NOT.(workspaceLinesearch(i) <= 0.0_mpd)).AND.  &
                (.NOT.(workspaceLinesearch(i) > 0.0_mpd))) nan=nan+1
            globalParameter(itgbi)=workspaceLinesearch(i) ! current parameter values
        END DO

        IF (nan > 0) THEN
            WRITE(*,*) 'Result vector containes ', nan,' NaNs - stop'
            CALL peend(25,'Aborted, result vector contains NaNs')
            STOP
        END IF

        !     subito exit, if required -----------------------------------------

        IF(isubit /= 0) THEN ! subito
            WRITE(*,*) 'Subito!     Exit after first step.'
            GO TO 90
        END IF

        IF(info == 0) THEN
            WRITE(*,*) 'INFO=0 should not happen (line search input err)'
            IF (iagain <= 0) THEN
                icalcm=1
                CYCLE
            ENDIF
        END IF
        IF(info < 0 .OR. nloopn == nloopsol) CYCLE
        !     Block 4: line search convergence ---------------------------------

        CALL ptlprt(lunlog)
        CALL feasib(concut,iact)               ! check constraints
        IF(iact /= 0.OR.chicut > 1.0) THEN
            icalcm=-1
            IF(iterat < matrit) icalcm=+1
            CYCLE ! iterate
        END IF
        IF(delfun <= dflim)  GO TO 90           ! convergence
        IF(iterat >= mitera) GO TO 90           ! ending
        icalcm=-1
        IF(iterat < matrit) icalcm=+1
        CYCLE                                ! next iteration

        !     Block 5: iteration ending ----------------------------------------

90      icalcm=-2
    END DO
    IF(nrejec(0)+nrejec(1)+nrejec(2)+nrejec(3) /= 0) THEN
        WRITE(*,*) ' '
        WRITE(*,*) 'Data rejected in last loop:   '
        WRITE(*,*) '   ',  &
            nrejec(0), ' (rank deficit/NaN) ',nrejec(1),' (Ndf=0)   ',  &
            nrejec(2), ' (huge)   ',nrejec(3),' (large)'
    END IF
    
    ! monitoring of residuals
    IF (imonit > 0 .AND. btest(imonit,1)) CALL monres
    IF (lunmon > 0) CLOSE(UNIT=lunmon)

    dwmean=sumndf/REAL(ndfsum,mpd)
    dratio=fvalue/dwmean/REAL(ndfsum-nfgb,mpd)
    catio=REAL(dratio,mps)
    IF(nloopn /= 1.AND.lhuber /= 0) THEN
        catio=catio/0.9326  ! correction Huber downweighting (in global chi2)       
    END IF
    mrati=nint(100.0*catio,mpi)

    DO lunp=6,lunlog,lunlog-6
        WRITE(lunp,*) ' '
        IF (nfilw <= 0) THEN
            WRITE(lunp,*) 'Sum(Chi^2)/Sum(Ndf) =',fvalue
            WRITE(lunp,*) '                    / (',ndfsum,'-',nfgb,')'
            WRITE(lunp,*) '                    =',dratio
        ELSE
            WRITE(lunp,*) 'Sum(W*Chi^2)/Sum(Ndf)/<W> =',fvalue
            WRITE(lunp,*) '                          / (',ndfsum,'-', nfgb,')'
            WRITE(lunp,*) '                          /',dwmean
            WRITE(lunp,*) '                          =',dratio
        END IF
        WRITE(lunp,*) ' '
        IF(nloopn /= 1.AND.lhuber /= 0) WRITE(lunp,*)  &
            '            with correction for down-weighting   ',catio
    END DO
    nrej=nrejec(0)+nrejec(1)+nrejec(2)+nrejec(3) ! total number of rejects

    !     ... the end with exit code ???????????????????????????????????????

    !      WRITE(*,199)              ! write exit code
    !     + '-----------------------------------------------------------'
    !      IF(ITEXIT.EQ.0) WRITE(*,199)
    !     +  'Exit code = 0:  Convergence reached'
    !      IF(ITEXIT.EQ.1) WRITE(*,199)
    !     +  'Exit code = 1:  No improvement in last iteration'
    !      IF(ITEXIT.EQ.2) WRITE(*,199)
    !     +  'Exit code = 2:  Maximum number of iterations reached'
    !      IF(ITEXIT.EQ.3) WRITE(*,199)
    !     +  'Exit code = 3:  Failure'
    !      WRITE(*,199)
    !     + '-----------------------------------------------------------'
    !      WRITE(*,199) ' '


    nrati=nint(10000.0*REAL(nrej,mps)/REAL(nrecal,mps),mpi)
    WRITE(crjrat,197) 0.01_mpd*REAL(nrati,mpd)
    nfaci=nint(100.0*SQRT(catio),mpi)

    WRITE(cratio,197) 0.01_mpd*REAL(mrati,mpd)
    WRITE(cfacin,197) 0.01_mpd*REAL(nfaci,mpd)

    warner=.FALSE. ! warnings
    IF(mrati < 90.OR.mrati > 110) warner=.TRUE.
    IF(nrati > 100) warner=.TRUE.
    IF(ncgbe /= 0) warner=.TRUE.
    warners = .FALSE. ! severe warnings
    IF(nalow /= 0) warners=.TRUE.
    warnerss = .FALSE. ! more severe warnings
    IF(nmiss1 /= 0) warnerss=.TRUE.
    IF(iagain /= 0) warnerss=.TRUE.
    IF(ndefec /= 0) warnerss=.TRUE.

    IF(warner.OR.warners.OR.warnerss) THEN
        WRITE(*,199) ' '
        WRITE(*,199) ' '
        WRITE(*,199) 'WarningWarningWarningWarningWarningWarningWarningWarningWar'
        WRITE(*,199) 'arningWarningWarningWarningWarningWarningWarningWarningWarn'
        WRITE(*,199) 'rningWarningWarningWarningWarningWarningWarningWarningWarni'
        WRITE(*,199) 'ningWarningWarningWarningWarningWarningWarningWarningWarnin'
        WRITE(*,199) 'ingWarningWarningWarningWarningWarningWarningWarningWarning'
        WRITE(*,199) 'ngWarningWarningWarningWarningWarningWarningWarningWarningW'
        WRITE(*,199) 'gWarningWarningWarningWarningWarningWarningWarningWarningWa'

        IF(mrati < 90.OR.mrati > 110) THEN
            WRITE(*,199) ' '
            WRITE(*,*) '        Chi^2/Ndf = ',cratio, '  (should be close to 1)'
            WRITE(*,*) '        => multiply all input standard ',  &
                'deviations by factor',cfacin
        END IF

        IF(nrati > 100) THEN
            WRITE(*,199) ' '
            WRITE(*,*) '        Fraction of rejects =',crjrat,' %',  &
                '  (should be far below 1 %)'
            WRITE(*,*) '        => please provide correct mille data'
        END IF

        IF(iagain /= 0) THEN
            WRITE(*,199) ' '
            WRITE(*,*) '        Matrix not positiv definite '//  &
                '(function not decreasing)'
            WRITE(*,*) '        => please provide correct mille data'
        END IF

        IF(ndefec /= 0) THEN
            WRITE(*,199) ' '
            WRITE(*,*) '        Rank defect =',ndefec,  &
                '  for global matrix, should be 0'
            WRITE(*,*) '        => please provide correct mille data'
        END IF
        
        IF(nmiss1 /= 0) THEN
            WRITE(*,199) ' '
            WRITE(*,*) '        Rank defect =',nmiss1,  &
                '  for constraint equations, should be 0'
            WRITE(*,*) '        => please correct constraint definition'
        END IF
                
        IF(ncgbe /= 0) THEN
            WRITE(*,199) ' '
            WRITE(*,*) '        Number of empty constraints =',ncgbe, ', should be 0'
            WRITE(*,*) '        => please check constraint definition, mille data'
        END IF

        IF(nalow /= 0) THEN
            WRITE(*,199) ' '
            WRITE(*,*) '        Possible rank defects =',nalow,  &
                '  for global vector (too few entries)'
            WRITE(*,*) '        => please check mille data and ENTRIES cut'
        END IF
        
        WRITE(*,199) ' '
        WRITE(*,199) 'WarningWarningWarningWarningWarningWarningWarningWarningWar'
        WRITE(*,199) 'arningWarningWarningWarningWarningWarningWarningWarningWarn'
        WRITE(*,199) 'rningWarningWarningWarningWarningWarningWarningWarningWarni'
        WRITE(*,199) 'ningWarningWarningWarningWarningWarningWarningWarningWarnin'
        WRITE(*,199) 'ingWarningWarningWarningWarningWarningWarningWarningWarning'
        WRITE(*,199) 'ngWarningWarningWarningWarningWarningWarningWarningWarningW'
        WRITE(*,199) 'gWarningWarningWarningWarningWarningWarningWarningWarningWa'
        WRITE(*,199) ' '

    ENDIF

    CALL mend                ! modul ending

    !     ------------------------------------------------------------------

    IF(metsol == 1) THEN

    ELSE IF(metsol == 2) THEN
        CALL zdiags
    ELSE IF(metsol == 3 .OR. metsol == 4) THEN
        !        errors and correlations from MINRES
        DO  k=1,mnrsel
            labelg=lbmnrs(k)
            IF(labelg == 0) CYCLE
            itgbi=inone(labelg)
            ivgbi=0
            IF(itgbi /= 0) ivgbi=globalParLabelIndex(2,itgbi)
            IF(ivgbi < 0) ivgbi=0
            IF(ivgbi == 0) CYCLE
            !          determine error and global correlation for parameter IVGBI
            IF (metsol == 3) THEN
                CALL solglo(ivgbi)
            ELSE
                CALL solgloqlp(ivgbi)
            ENDIF
        END DO
  
    ELSE IF(metsol == 5) THEN
  
    END IF

    IF(metsol <= 2) THEN ! inversion or diagonalization ?
        !use elimination for constraints ?
        IF(nfgb < nvgb) THEN
            ! extend, transform matrix
            DO i=nvgb-ncgb+1,nvgb
                ioff=((i-1)*i)/2
                globalMatD(ioff+1:ioff+i)=0.0_mpd
            END DO
            CALL qlssq(avprd0,globalMatD,.false.) ! Q^t*A*Q
        END IF
    END IF

    CALL prtglo              ! print result

    IF (warnerss) THEN
        CALL peend(3,'Ended with severe warnings (bad global matrix)')
    ELSE IF (warners) THEN
        CALL peend(2,'Ended with severe warnings (insufficient measurements)')
    ELSE IF (warner) THEN
        CALL peend(1,'Ended with warnings (bad measurements)')
    ELSE
        CALL peend(0,'Ended normally')
    END IF

102 FORMAT(' Call FEASIB with cut=',g10.3)
    ! 103  FORMAT(1X,A,G12.4)
197 FORMAT(F7.2)    
199 FORMAT(7X,a)
END SUBROUTINE xloopn                ! standard solution

!> Interprete command line option, steering file.
!!
!! Fetch and interprete command line options,
!! if steering file specified, check file existence (calling NUFILE)
!!
!! If no steering file specified, check default steering file.
!!
!! Create test files for command line option '-t'.
!!
!! Read steering file, print some lines, detect names of text and
!! binary files, check file existence, store all file names.
!!
!! Open all binary files.

SUBROUTINE filetc
    USE mpmod
    USE mpdalc

    IMPLICIT NONE
    INTEGER(mpi) :: i
    INTEGER(mpi) :: ia
    INTEGER(mpi) :: iargc
    INTEGER(mpi) :: ib
    INTEGER(mpi) :: ie
    INTEGER(mpi) :: ierrf
    INTEGER(mpi) :: ieq
    INTEGER(mpi) :: ifilb
    INTEGER(mpi) :: ioff
    INTEGER(mpi) :: iopt
    INTEGER(mpi) :: ios
    INTEGER(mpi) :: iosum
    INTEGER(mpi) :: it
    INTEGER(mpi) :: k
    INTEGER(mpi) :: mat
    INTEGER(mpi) :: nab
    INTEGER(mpi) :: nline
    INTEGER(mpi) :: npat
    INTEGER(mpi) :: ntext
    INTEGER(mpi) :: nu
    INTEGER(mpi) :: nuf
    INTEGER(mpi) :: nums
    INTEGER(mpi) :: nufile
    INTEGER(mpi) :: lenfileInfo
    INTEGER(mpi) :: lenFileNames
    INTEGER(mpi) :: matint
    INTEGER(mpi), DIMENSION(:,:), ALLOCATABLE :: vecfileInfo
    INTEGER(mpi), DIMENSION(:,:), ALLOCATABLE :: tempArray
    INTEGER(mpl) :: rows
    INTEGER(mpl) :: cols
    INTEGER(mpl) :: newcols
    INTEGER(mpl) :: length

    CHARACTER (LEN=1024) :: text
    CHARACTER (LEN=1024) :: fname
    CHARACTER (LEN=14) :: bite(3)
    CHARACTER (LEN=32) :: keystx
    REAL(mpd) :: dnum(100)
    SAVE
    DATA bite/'C_binary','text  ','Fortran_binary'/
    !     ...
    CALL mstart('FILETC/X')

    nuf=1  ! C binary is default
    DO i=1,8
        times(i)=0.0
    END DO

    !     read command line options ----------------------------------------

    filnam=' '   ! print command line options and find steering file
    DO i=1,iargc()
        IF(i == 1) THEN
            WRITE(*,*) ' '
            WRITE(*,*) 'Command line options: '
            WRITE(*,*) '--------------------- '
        END IF
        CALL getarg(i,text)         ! get I.th text from command line
        CALL rltext(text,ia,ib,nab) ! return indices for non-blank area
        WRITE(*,101) i,text(1:nab)  ! echo print
        IF(text(ia:ia) /= '-') THEN
            nu=nufile(text(ia:ib))   ! inquire on file existence
            IF(nu == 2) THEN         ! existing text file
                IF(filnam /= ' ') THEN
                    WRITE(*,*) 'Second text file in command line - stop'
                    CALL peend(12,'Aborted, second text file in command line')
                    STOP
                ELSE
                    filnam=text
                END IF
            ELSE
                WRITE(*,*) 'Open error for file:',text(ia:ib),' - stop'
                CALL peend(16,'Aborted, open error for file')
                STOP
            END IF
        ELSE
            IF(INDEX(text(ia:ib),'b') /= 0) THEN
                mdebug=3 ! debug flag
                WRITE(*,*) 'Debugging requested'
            END IF
            it=INDEX(text(ia:ib),'t')
            IF(it /= 0) THEN
                ictest=1  ! internal test files
                ieq=INDEX(text(ia+it:ib),'=')+it
                IF (it /= ieq) THEN
                    IF (INDEX(text(ia+ieq:ib),'SL0' ) /= 0) ictest=2
                    IF (INDEX(text(ia+ieq:ib),'SLE' ) /= 0) ictest=3
                    IF (INDEX(text(ia+ieq:ib),'BP'  ) /= 0) ictest=4
                    IF (INDEX(text(ia+ieq:ib),'BRLF') /= 0) ictest=5
                    IF (INDEX(text(ia+ieq:ib),'BRLC') /= 0) ictest=6
                END IF
            END IF
            IF(INDEX(text(ia:ib),'s') /= 0) isubit=1  ! like "subito"
            IF(INDEX(text(ia:ib),'f') /= 0) iforce=1  ! like "force"
            IF(INDEX(text(ia:ib),'c') /= 0) icheck=1  ! like "checkinput"
            IF(INDEX(text(ia:ib),'C') /= 0) icheck=2  ! like "checkinput 2"
        END IF
        IF(i == iargc()) WRITE(*,*) '--------------------- '
    END DO


    !     create test files for option -t ----------------------------------

    IF(ictest >= 1) THEN
        WRITE(*,*) ' '
        IF (ictest == 1) THEN
            CALL mptest ! 'wire chamber'
        ELSE
            CALL mptst2(ictest-2) ! 'silicon tracker'
        END IF
        IF(filnam == ' ') filnam='mp2str.txt'
        WRITE(*,*) ' '
    END IF

    !     check default steering file with file-name "steerfile" -----------

    IF(filnam == ' ') THEN  ! check default steering file
        text='steerfile'
        CALL rltext(text,ia,ib,nab) ! return indices for non-blank area
        nu=nufile(text(ia:ib))      ! inquire on file existence and type
        IF(nu > 0) THEN
            filnam=text
        ELSE
            CALL peend(10,'Aborted, no steering file')
            STOP 'in FILETC: no steering file.                      .'
        END IF
    END IF


    !     open, read steering file:
    !                               end
    !                               fortranfiles
    !                               cfiles


    CALL rltext(filnam,ia,ib,nfnam) ! return indices for non-blank area
    WRITE(*,*) ' '
    WRITE(*,*) 'Listing of steering file: ',filnam(1:nfnam)
    WRITE(*,*) '-------------------------'
    OPEN(10,FILE=filnam(1:nfnam),IOSTAT=ios)
    IF(ios /= 0) THEN
        WRITE(*,*) 'Open error for steering file - stop'
        CALL peend(11,'Aborted, open error for steering file')
        STOP
    END IF
    ifile =0
    nfiles=0

    lenfileInfo=2
    lenFileNames=0
    rows=6; cols=lenFileInfo
    CALL mpalloc(vecfileInfo,rows,cols,'file info from steering')
    nline=0
    DO
        READ(10,102,IOSTAT=ierrf) text        ! read steering file
        IF (ierrf < 0) EXIT ! eof
        CALL rltext(text,ia,ib,nab)     ! return indices for non-blank area
        nline=nline+1
        IF(nline <= 50) THEN   ! print up to 50 lines
            WRITE(*,101) nline,text(1:nab)
            IF(nline == 50)  WRITE(*,*) '     ...'
        END IF

        CALL rltext(text,ia,ib,nab)        ! test content   'end'
        IF(ib == ia+2) THEN
            mat=matint(text(ia:ib),'end',npat,ntext)
            IF(mat == 3) THEN
                text=' '
                CALL intext(text,nline)
                WRITE(*,*) '    end-statement after',nline,' text lines'
                EXIT
            END IF
        END IF

        keystx='fortranfiles'
        mat=matint(text(ia:ib),keystx,npat,ntext)
        IF(mat == ntext) THEN ! exact matching
            nuf=3
            !         WRITE(*,*) 'Fortran files'
            CYCLE
        END IF

        keystx='Cfiles'
        mat=matint(text(ia:ib),keystx,npat,ntext)
        IF(mat == ntext) THEN ! exact matching
            nuf=1
            !         WRITE(*,*) 'Cfiles'
            CYCLE
        END IF

        keystx='closeandreopen' ! don't keep binary files open
        mat=matint(text(ia:ib),keystx,npat,ntext)
        IF(mat == ntext) THEN ! exact matching
            keepOpen=0
            CYCLE
        END IF

        ! file names
        !     check for file options (' -- ')
        ie=ib
        iopt=INDEX(text(ia:ib),' -- ')
        IF (iopt > 0) ie=iopt-1

        IF(nab == 0) CYCLE
        nu=nufile(text(ia:ie))           ! inquire on file existence
        IF(nu > 0) THEN                  ! existing file
            IF (nfiles == lenFileInfo) THEN ! increase length
                CALL mpalloc(tempArray,rows,cols,'temp file info from steering')
                tempArray=vecfileInfo
                CALL mpdealloc(vecfileInfo)
                lenFileInfo=lenFileInfo*2
                newcols=lenFileInfo
                CALL mpalloc(vecfileInfo,rows,newcols,'file info from steering')
                vecfileInfo(:,1:cols)=tempArray(:,1:cols)
                CALL mpdealloc(tempArray)
                cols=newcols
            ENDIF
            nfiles=nfiles+1              ! count number of files
            IF(nu == 1) nu=nuf           !
            lenFileNames=lenFileNames+ie-ia+1 ! total length of file names
            vecFileInfo(1,nfiles)=nline  ! line number
            vecFileInfo(2,nfiles)=nu     ! cbinary =1, text =2, fbinary=3
            vecFileInfo(3,nfiles)=ia     ! file name start
            vecFileInfo(4,nfiles)=ie     ! file name end
            vecFileInfo(5,nfiles)=iopt   ! option start
            vecFileInfo(6,nfiles)=ib     ! option end
        ELSE
        !         WRITE(*,*) 'Open error for file ',TEXT(IA:IB)
        !         STOP
        END IF
    END DO
    REWIND 10
    ! read again to fill dynamic arrays with file info
    length=nfiles
    CALL mpalloc(mfd,length,'file type')
    CALL mpalloc(nfd,length,'file line (in steering)')
    CALL mpalloc(lfd,length,'file name length')
    CALL mpalloc(ofd,length,'file option')
    length=lenFileNames
    CALL mpalloc(tfd,length,'file name')
    nline=0
    i=1
    ioff=0
    DO
        READ(10,102,IOSTAT=ierrf) text        ! read steering file
        IF (ierrf < 0) EXIT ! eof
        nline=nline+1
        IF (nline == vecFileInfo(1,i)) THEN
            nfd(i)=vecFileInfo(1,i)
            mfd(i)=vecFileInfo(2,i)
            ia=vecFileInfo(3,i)-1
            lfd(i)=vecFileInfo(4,i)-ia ! length file name
            FORALL (k=1:lfd(i)) tfd(ioff+k)=text(ia+k:ia+k)
            !            tfd(i)=text(vecFileInfo(3,i):vecFileInfo(4,i))      ! file name
            ioff=ioff+lfd(i)
            ofd(i)=1.0              ! option for file
            IF (vecFileInfo(5,i) > 0) THEN
                CALL ratext(text(vecFileInfo(5,i)+4:vecFileInfo(6,i)),nums,dnum) ! translate text to DP numbers
                IF (nums > 0) ofd(i)=REAL(dnum(1),mps)
            END IF
            i=i+1
            IF (i > nfiles) EXIT
        ENDIF
    ENDDO
    CALL mpdealloc(vecfileInfo)
    REWIND 10
    ! additional info for binary files
    length=nfiles; rows=2
    CALL mpalloc(ifd,length,'integrated record numbers (=offset)')
    CALL mpalloc(jfd,length,'number of accepted records')
    CALL mpalloc(kfd,rows,length,'number of records in file, file order')
    CALL mpalloc(dfd,length,'ndf sum')
    CALL mpalloc(xfd,length,'max. record size')
    CALL mpalloc(wfd,length,'file weight')
    CALL mpalloc(cfd,length,'chi2 sum')
    CALL mpalloc(sfd,rows,length,'start, end of file name in TFD')
    CALL mpalloc(yfd,length,'modification date')
    yfd=0
    !
    WRITE(*,*) '-------------------------'
    WRITE(*,*) ' '

    !     print table of files ---------------------------------------------

    IF (mprint > 1) THEN
        WRITE(*,*) 'Table of files:'
        WRITE(*,*) '---------------'
    END IF
    WRITE(8,*) ' '
    WRITE(8,*) 'Text and data files:'
    ioff=0
    DO i=1,nfiles
        FORALL (k=1:lfd(i)) fname(k:k)=tfd(ioff+k)
        !        fname=tfd(i)(1:lfd(i))
        IF (mprint > 1) WRITE(*,103) i,bite(mfd(i)),fname(1:lfd(i))
        WRITE(8,103) i,bite(mfd(i)),fname(1:lfd(i))
        ioff=ioff+lfd(i)
    END DO
    IF (mprint > 1) THEN
        WRITE(*,*) '---------------'
        WRITE(*,*) ' '
    END IF

    !     open the binary Fortran (data) files on unit 11, 12, ...

    iosum=0
    nfilf=0
    nfilb=0
    nfilw=0
    ioff=0
    ifilb=0
    IF (keepOpen < 1) ifilb=1
    DO i=1,nfiles
        IF(mfd(i) == 3) THEN
            nfilf=nfilf+1
            nfilb=nfilb+1
            ! next file name
            sfd(1,nfilb)=ioff
            sfd(2,nfilb)=lfd(i)
            CALL binopn(nfilb,ifilb,ios)
            IF(ios == 0) THEN
                wfd(nfilb)=ofd(i)
                IF (keepOpen < 1) CALL bincls(nfilb,ifilb)  
            ELSE ! failure
                iosum=iosum+1
                nfilf=nfilf-1
                nfilb=nfilb-1 
            END IF
        END IF
        ioff=ioff+lfd(i)
    END DO

    !     open the binary C files

    nfilc=-1
    ioff=0
    DO i=1,nfiles                                 ! Cfiles
        IF(mfd(i) == 1) THEN
#ifdef READ_C_FILES
            IF(nfilc < 0) THEN ! initialize
                CALL initc(max(nfiles,mthrdr)) ! uncommented by GF
                nfilc=0
            END IF
            nfilc=nfilc+1
            nfilb=nfilb+1
            ! next file name
            sfd(1,nfilb)=ioff
            sfd(2,nfilb)=lfd(i)
            CALL binopn(nfilb,ifilb,ios)
            IF(ios == 0) THEN
                wfd(nfilb)=ofd(i)
                IF (keepOpen < 1) CALL bincls(nfilb,ifilb)
            ELSE ! failure
                iosum=iosum+1
                nfilc=nfilc-1
                nfilb=nfilb-1                     
            END IF
#else
            WRITE(*,*) 'Opening of C-files not supported.'
            ! GF add
            iosum=iosum+1
            ! GF add end
#endif
        END IF
        ioff=ioff+lfd(i)
    END DO

    DO k=1,nfilb
        kfd(1,k)=1   ! reset (negated) record counters
        kfd(2,k)=k   ! set file number
        ifd(k)=0     ! reset integrated record numbers
        xfd(k)=0     ! reset max record size
    END DO

    IF(iosum /= 0) THEN
        CALL peend(15,'Aborted, open error(s) for binary files')
        STOP 'FILETC: open error                                      '
    END IF
    IF(nfilb == 0) THEN
        CALL peend(14,'Aborted, no binary files')
        STOP 'FILETC: no binary files                                 '
    END IF
    IF (keepOpen > 0) THEN 
        WRITE(*,*) nfilb,' binary files opened' ! corrected by GF
    ELSE
        WRITE(*,*) nfilb,' binary files opened and closed' ! corrected by GF
    END IF     
101 FORMAT(i3,2X,a)
102 FORMAT(a)
103 FORMAT(i3,2X,a14,3X,a)
    !    CALL mend
    RETURN
END SUBROUTINE filetc

!> Interprete \ref ssec-textfiles "text files".
!!
!! Reset flags and read steering and all other text files.
!! Print some lines from each file.
!!
!! Store parameter values, constraints and measurements.
!!
!! Check flags METSOL (method of solution) and
!! MATSTO (matrix storage mode).
!! Set default values for flags, which are undefined.
!!
!! Parameter values, format:
!!
!!       1  label
!!       2  (initial) parameter value
!!       3  pre-sigma
!!       4  label
!!       5  (initial) parameter value
!!       6  pre-sigma
!!       7  label
!!     ...  ...
!!     (number of words is multiple of 3)
!!
!! Constraint data, format:
!!
!!       1  0                 ! constraint header of four words:
!!       2  right-hand-side   ! 0 and -1 ...
!!       3  -1; -2            ! ... indicate (weighting) ...
!!       4  sigma             ! ... header
!!       5  label
!!       6  factor
!!       7  label
!!       8  factor
!!       9  ...
!!     ...  ...
!!     (number of words is multiple of 2, at least 6)
!!
!! Measured data, format:
!!
!!       1  0                 ! constraint header of four words:
!!       2  right-hand-side   ! 0 and -1 ...
!!       3  -1                ! ... indicate ...
!!       4  sigma             ! ... header
!!       5  label
!!       6  factor
!!       7  label
!!       8  factor
!!       9  ...
!!     ...  ...
!!     (number of words is multiple of 2, at least 6)

SUBROUTINE filetx ! ---------------------------------------------------
    USE mpmod

    IMPLICIT NONE
    INTEGER(mpi) :: i
    INTEGER(mpi) :: ia
    INTEGER(mpi) :: ib
    INTEGER(mpi) :: ierrf
    INTEGER(mpi) :: ioff
    INTEGER(mpi) :: ios
    INTEGER(mpi) :: iosum
    INTEGER(mpi) :: k
    INTEGER(mpi) :: mat
    INTEGER(mpi) :: nab
    INTEGER(mpi) :: nfiln
    INTEGER(mpi) :: nline
    INTEGER(mpi) :: nlinmx
    INTEGER(mpi) :: npat
    INTEGER(mpi) :: ntext
    INTEGER(mpi) :: matint

    !      CALL MSTART('FILETX')

    CHARACTER (LEN=1024) :: text
    CHARACTER (LEN=1024) :: fname

    WRITE(*,*) ' '
    WRITE(*,*) 'Processing text files ...'
    WRITE(*,*) ' '

    iosum=0
    ioff=0
    DO i=0,nfiles
        IF(i == 0) THEN
            WRITE(*,*) 'File ',filnam(1:nfnam)
            nlinmx=100
        ELSE
            nlinmx=10
            ia=ioff
            ioff=ioff+lfd(i)
            IF(mfd(i) /= 2) CYCLE ! exclude binary files
            FORALL (k=1:lfd(i)) fname(k:k)=tfd(ia+k)
            WRITE(*,*) 'File ',fname(1:lfd(i))
            IF (mprint > 1) WRITE(*,*) ' '
            OPEN(10,FILE=fname(1:lfd(i)),IOSTAT=ios,FORM='FORMATTED')
            IF(ios /= 0) THEN
                WRITE(*,*) 'Open error for file ',fname(1:lfd(i))
                iosum=iosum+1
                CYCLE
            END IF
        END IF
  
        nline=0
        nfiln=1
        !      read text file
        DO
            READ(10,102,IOSTAT=ierrf) text
            IF (ierrf < 0) THEN
                text=' '
                CALL intext(text,nline)
                WRITE(*,*) '    end-of-file after',nline,' text lines'
                EXIT ! eof
            ENDIF
            nline=nline+1
            IF(nline <= nlinmx.AND.mprint > 1) THEN ! print first 10 lines of every text fiLE
                CALL rltext(text,ia,ib,nab)
                nab=MAX(1,nab)
                WRITE(*,101) nline,text(1:nab)
                IF(nline == nlinmx) WRITE(*,*) '    ...'
            END IF
  
            CALL rltext(text,ia,ib,nab)        ! test content   'end'
            IF(ib == ia+2) THEN
                mat=matint(text(ia:ib),'end',npat,ntext)
                IF(mat == 3) THEN
                    text=' '
                    CALL intext(text,nline)
                    WRITE(*,*) '    end-statement after',nline,' text lines'
                    EXIT
                END IF
            END IF
  
            IF(i == 0) THEN ! first text file - exclude lines with file names
                IF(nfiln <= nfiles.AND.nline == nfd(nfiln)) THEN
                    nfiln=nfiln+1
                    text=' '
                !             WRITE(*,*) 'line is excluded ',TEXT(1:10)
                END IF
            END IF
            !       WRITE(*,*) TEXT(1:40),'  < interprete text'
            CALL intext(text,nline)   ! interprete text
        END DO
        WRITE(*,*) ' '
        REWIND 10
        CLOSE(UNIT=10)
    END DO

    IF(iosum /= 0) THEN
        CALL peend(16,'Aborted, open error(s) for text files')
        STOP 'FILETX: open error(s) in text files                     '
    END IF

    WRITE(*,*) '... end of text file processing.'
    WRITE(*,*) ' '

    IF(lunkno /= 0) THEN
        WRITE(*,*) ' '
        WRITE(*,*) lunkno,' unknown keywords in steering files, ',  &
            'or file non-existing,'
        WRITE(*,*) '   see above!'
        WRITE(*,*) '------------>    stop'
        WRITE(*,*) ' '
        CALL peend(13,'Aborted, unknown keywords in steering file')
        STOP
    END IF

    !     check methods

    IF(metsol == 0) THEN        ! if undefined
        IF(matsto == 0) THEN     ! if undefined
        !            METSOL=1 ! default is matrix inversion
        !            MATSTO=1 ! default is symmetric matrix
        ELSE IF(matsto == 1) THEN ! if symmetric
            metsol=3 ! MINRES
        ELSE IF(matsto == 2) THEN ! if sparse
            metsol=3 ! MINRES
        END IF
    ELSE IF(metsol == 1) THEN   ! if inversion
        matsto=1    !
    ELSE IF(metsol == 2) THEN   ! if diagonalization
        matsto=1
    ELSE IF(metsol == 3) THEN   ! if MINRES
    !        MATSTO=2 or 1
    ELSE IF(metsol == 4) THEN   ! if MINRES-QLP
    !        MATSTO=2 or 1
    ELSE IF(metsol == 5) THEN   ! if GMRES
    !        MATSTO=2 or 1
    ELSE
        WRITE(*,*) 'MINRES forced with sparse matrix!'
        WRITE(*,*) ' '
        WRITE(*,*) 'MINRES forced with sparse matrix!'
        WRITE(*,*) ' '
        WRITE(*,*) 'MINRES forced with sparse matrix!'
        metsol=3 ! forced
        matsto=2 ! forced
    END IF
    IF(matsto > 2) THEN
        WRITE(*,*) 'MINRES forced with sparse matrix!'
        WRITE(*,*) ' '
        WRITE(*,*) 'MINRES forced with sparse matrix!'
        WRITE(*,*) ' '
        WRITE(*,*) 'MINRES forced with sparse matrix!'
        metsol=3 ! forced
        matsto=2 ! forced
    END IF

    !     print information about methods and matrix storage modes

    WRITE(*,*) ' '
    WRITE(*,*) 'Solution method and matrix-storage mode:'
    IF(metsol == 1) THEN
        WRITE(*,*) '     METSOL = 1:  matrix inversion'
    ELSE IF(metsol == 2) THEN
        WRITE(*,*) '     METSOL = 2:  diagonalization'
    ELSE IF(metsol == 3) THEN
        WRITE(*,*) '     METSOL = 3:  MINRES'
    ELSE IF(metsol == 4) THEN
        WRITE(*,*) '     METSOL = 4:  MINRES-QLP'
    ELSE IF(metsol == 5) THEN
        WRITE(*,*) '     METSOL = 5:  GMRES (-> MINRES)'
  
    END IF

    WRITE(*,*) '                  with',mitera,' iterations'

    IF(matsto == 1) THEN
        WRITE(*,*) '     MATSTO = 1:  symmetric matrix, ', '(n*n+n)/2 elements'
    ELSE IF(matsto == 2) THEN
        WRITE(*,*) '     MATSTO = 2:  sparse matrix'
    END IF
    IF(mbandw /= 0) THEN
        WRITE(*,*) '                  and band matrix, width',mbandw
    END IF

    IF(chicut /= 0.0) THEN
        WRITE(*,*) 'Chi square cut equiv 3 st.dev applied ...'
        WRITE(*,*) ' in  first iteration with factor',chicut
        WRITE(*,*) ' in second iteration with factor',chirem
        WRITE(*,*) ' (reduced by sqrt in next iterations)'
    END IF

    IF(lhuber /= 0) THEN
        WRITE(*,*) '   Down-weighting of outliers in', lhuber,' iterations'
        WRITE(*,*) '   Cut on downweight fraction',dwcut
    END IF

    WRITE(*,*) 'Iterations (solutions) with line search:'
    IF(lsearch > 2) THEN
        WRITE(*,*) ' All'
    ELSEIF (lsearch == 1) THEN
        WRITE(*,*) ' Last'
    ELSEIF (lsearch < 1) THEN
        WRITE(*,*) ' None'
    ELSE
        IF (chicut /= 0.0) THEN
            WRITE(*,*) ' All with Chi square cut scaling factor <= 1.'
        ELSE
            WRITE(*,*) ' All'
        ENDIF
    ENDIF

    IF(numMeasurements>0) THEN
        WRITE(*,*) 
        WRITE(*,*) ' Number of external measurements ', numMeasurements
    ENDIF
    
    CALL mend

101 FORMAT(i3,2X,a)
102 FORMAT(a)
END SUBROUTINE filetx

!> Inquire on file.
!!
!! Result = 1 for existing binary file, =2 for existing text file, else =0,
!! < 0 open error.
!!
!! Text file names are recognized by the filename extension, which
!! should contain 'xt' or 'tx'.
!!
!! \param [in,out] fname file name, optionaly strip prefix.

INTEGER(mpi) FUNCTION nufile(fname)
    USE mpdef

    IMPLICIT NONE
    INTEGER(mpi) :: ios
    INTEGER(mpi) :: l1
    INTEGER(mpi) :: ll
    INTEGER(mpi) :: nm
    INTEGER(mpi) :: npat
    INTEGER(mpi) :: ntext
    INTEGER(mpi) :: nuprae
    INTEGER(mpi) :: matint

    CHARACTER (LEN=*), INTENT(INOUT) :: fname
    LOGICAL :: ex
    SAVE
    !     ...
    nufile=0
    IF(fname(1:5) == 'rfio:') nuprae=1
    IF(fname(1:5) == 'dcap:') nuprae=2
    IF(fname(1:5) == 'root:') nuprae=3
    IF(nuprae == 0) THEN
        INQUIRE(FILE=fname,IOSTAT=ios,EXIST=ex)
        IF(ios /= 0) nufile=-ABS(ios)
        IF(ios /= 0) RETURN
    ELSE IF(nuprae == 1) THEN  ! rfio:
        ll=LEN(fname)
        fname=fname(6:ll)
        ex=.TRUE.
        nufile=1
        RETURN
    ELSE
        ex=.TRUE.   ! assume file existence
    END IF
    IF(ex) THEN
        nufile=1                                   ! binary
        ll=LEN(fname)
        l1=MAX(1,ll-3)
        nm=matint('xt',fname(l1:ll),npat,ntext)
        IF(nm == 2) nufile=2                       ! text
        IF(nm < 2) THEN
            nm=matint('tx',fname(l1:ll),npat,ntext)
            IF(nm == 2) nufile=2                   ! text
        END IF
    END IF
END FUNCTION nufile

!> Interprete text.
!!
!! Look for keywords and argument in text line.
!!
!! \param[in]  text   text
!! \param[in]  nline  line number
!!
SUBROUTINE intext(text,nline)
    USE mpmod
    USE mptext

    IMPLICIT NONE
    INTEGER(mpi) :: i
    INTEGER(mpi) :: ia
    INTEGER(mpi) :: ib
    INTEGER(mpi) :: ier
    INTEGER(mpi) :: iomp
    INTEGER(mpi) :: k
    INTEGER(mpi) :: kkey
    INTEGER(mpi) :: label
    INTEGER(mpi) :: lkey
    INTEGER(mpi) :: mat
    INTEGER(mpi) :: miter
    INTEGER(mpi) :: nab
    INTEGER(mpi) :: nkey
    INTEGER(mpi) :: nkeys
    INTEGER(mpi) :: nl
    INTEGER(mpi) :: nmeth
    INTEGER(mpi) :: npat
    INTEGER(mpi) :: ntext
    INTEGER(mpi) :: nums
    INTEGER(mpi) :: matint

    CHARACTER (LEN=*), INTENT(IN) :: text
    INTEGER(mpi), INTENT(IN) :: nline

    PARAMETER (nkeys=5,nmeth=6)
    CHARACTER (LEN=16) :: methxt(nmeth)
    CHARACTER (LEN=16) :: keylst(nkeys)
    CHARACTER (LEN=32) :: keywrd
    CHARACTER (LEN=32) :: keystx
    REAL(mpd) :: dnum(100)
    INTEGER(mpi) :: lpvs    ! ... integer
    REAL(mpd)    :: plvs    ! ... float

    INTERFACE
        SUBROUTINE addItem(length,list,label,value)
            USE mpmod
            INTEGER(mpi), INTENT(IN OUT) :: length
            TYPE(listItem), DIMENSION(:), INTENT(IN OUT), ALLOCATABLE :: list
            INTEGER(mpi), INTENT(IN) :: label
            REAL(mpd), INTENT(IN) :: value
        END SUBROUTINE addItem
    END INTERFACE

    DATA keylst/'unknown','parameter','constraint','measurement','method'/

    SAVE
    DATA methxt/'diagonalization','inversion','fullMINRES', 'sparseMINRES', &
        'fullMINRES-QLP', 'sparseMINRES-QLP'/
    DATA lkey/-1/                 ! last keyword

    !     ...
    nkey=-1                       ! new keyword
    CALL rltext(text,ia,ib,nab)   ! return indices for non-blank area
    IF(nab == 0) GOTO 10
    CALL ratext(text(1:nab),nums,dnum) ! translate text to DP numbers

    IF(nums /= 0) nkey=0
    IF(keyb /= 0) THEN
        keywrd=text(keya:keyb) !          text is TEXT(KEYA)...TEXT(KEYB)
        !         WRITE(*,*) 'Keyword is ',KEYWRD
  
        !        compare keywords
  
        DO nkey=2,nkeys           ! loop over all pede keywords
            keystx=keylst(nkey)   ! copy NKEY.th pede keyword
            mat=matint(text(keya:keyb),keystx,npat,ntext) ! comparison
            IF(mat >= ntext-ntext/5) GO TO 10
        END DO
  
        !        more comparisons
  
        keystx='print'
        mat=matint(text(keya:keyb),keystx,npat,ntext) ! comparison
        !         WRITE(*,*) KEYSTX,MAT,NTEXT
        !         IF(MAT.GE.NTEXT) THEN
        IF(mat >= (npat-npat/5)) THEN
            !         IF(MAT.GE.(NTEXT+NTEXT+3)/3) THEN
            mprint=1
            IF(nums > 0) mprint=NINT(dnum(1),mpi)
            RETURN
        END IF
  
        keystx='debug'
        mat=matint(text(keya:keyb),keystx,npat,ntext) ! comparison
        IF(mat >= (npat-npat/5)) THEN
            !         IF(MAT.GE.(NTEXT+NTEXT+3)/3) THEN
            mdebug=3
            ! GF            IF(NUMS.GT.0) MPRINT=DNUM(1)
            IF(nums > 0) mdebug=NINT(dnum(1),mpi)
            IF(nums > 1) mdebg2=NINT(dnum(2),mpi)
            RETURN
        END IF

        keystx='entries'
        mat=matint(text(keya:keyb),keystx,npat,ntext) ! comparison
        IF(mat >= (npat-npat/5)) THEN
            !         IF(MAT.GE.(NTEXT+NTEXT+3)/3) THEN
            IF(nums > 0 .AND. dnum(1) > 0.5) mreqenf=NINT(dnum(1),mpi)
            IF(nums > 1 .AND. dnum(2) > 0.5) mreqena=NINT(dnum(2),mpi)
            IF(nums > 2 .AND. dnum(3) > 0.5) iteren=NINT(dnum(1)*dnum(3),mpi)
            RETURN
        END IF

        keystx='printrecord'
        mat=matint(text(keya:keyb),keystx,npat,ntext) ! comparison
        IF(mat >= (npat-npat/5)) THEN
            IF(nums > 0) nrecpr=NINT(dnum(1),mpi)
            IF(nums > 1) nrecp2=NINT(dnum(2),mpi)
            RETURN
        END IF

        keystx='maxrecord'
        mat=matint(text(keya:keyb),keystx,npat,ntext) ! comparison
        IF(mat >= (npat-npat/5)) THEN
            IF (nums > 0.AND.dnum(1) > 0.) mxrec=NINT(dnum(1),mpi)
            RETURN
        END IF
  
        keystx='cache'
        mat=matint(text(keya:keyb),keystx,npat,ntext) ! comparison
        IF(mat >= (npat-npat/5)) THEN
            IF (nums > 0.AND.dnum(1) >= 0.) ncache=NINT(dnum(1),mpi) ! cache size, <0 keeps default
            IF (nums == 2.AND.dnum(2) > 0..AND.dnum(2) <= 1.0)  &  ! read cache fill level
                fcache(1)=REAL(dnum(2),mps)
            IF (nums >= 4) THEN                                    ! explicit cache splitting
                DO k=1,3
                    fcache(k)=REAL(dnum(k+1),mps)
                END DO
            END IF
            RETURN
        END IF
  
        keystx='chisqcut'
        mat=matint(text(keya:keyb),keystx,npat,ntext) ! comparison
        IF(mat >= (npat-npat/5)) THEN
            IF(nums == 0) THEN ! always 3-sigma cut
                chicut=1.0
                chirem=1.0
            ELSE
                chicut=REAL(dnum(1),mps)
                IF(chicut < 1.0) chicut=-1.0
                IF(nums == 1) THEN
                    chirem=1.0  ! 3-sigma cut, if not specified
                ELSE
                    chirem=REAL(dnum(2),mps)
                    IF(chirem < 1.0) chirem=1.0
                    IF(chicut >= 1.0) chirem=MIN(chirem,chicut)
                END IF
            END IF
            RETURN
        END IF
  
        ! GF added:
        keystx='hugecut'
        mat=matint(text(keya:keyb),keystx,npat,ntext) ! comparison
        IF(mat >= (npat-npat/5)) THEN
            IF(nums > 0) chhuge=REAL(dnum(1),mps)
            IF(chhuge < 1.0) chhuge=1.0 ! at least (!!) 3-sigma
            RETURN
        END IF
        ! GF added end
  
        keystx='linesearch'
        mat=matint(text(keya:keyb),keystx,npat,ntext) ! comparison
        IF(mat >= (npat-npat/5)) THEN
            IF(nums > 0) lsearch=NINT(dnum(1),mpi)
            RETURN
        END IF

        keystx='localfit'
        mat=matint(text(keya:keyb),keystx,npat,ntext) ! comparison
        IF(mat >= (npat-npat/5)) THEN
            IF(nums > 0) lfitnp=NINT(dnum(1),mpi)
            IF(nums > 1) lfitbb=NINT(dnum(2),mpi)
            RETURN
        END IF

        keystx='regularization'
        mat=matint(text(keya:keyb),keystx,npat,ntext) ! comparison
        IF(mat >= (npat-npat/5)) THEN
            nregul=1
            regula=REAL(dnum(1),mps)
            IF(nums >= 2) regpre=REAL(dnum(2),mps)
            RETURN
        END IF
  
        keystx='regularisation'
        mat=matint(text(keya:keyb),keystx,npat,ntext) ! comparison
        IF(mat >= (npat-npat/5)) THEN
            nregul=1
            regula=REAL(dnum(1),mps)
            IF(nums >= 2) regpre=REAL(dnum(2),mps)
            RETURN
        END IF
  
        keystx='presigma'
        mat=matint(text(keya:keyb),keystx,npat,ntext) ! comparison
        IF(mat >= (npat-npat/5)) THEN
            regpre=REAL(dnum(1),mps)
            RETURN
        END IF
  
        keystx='matiter'
        mat=matint(text(keya:keyb),keystx,npat,ntext) ! comparison
        IF(mat >= (npat-npat/5)) THEN
            matrit=NINT(dnum(1),mpi)
            RETURN
        END IF
  
        keystx='matmoni'
        mat=matint(text(keya:keyb),keystx,npat,ntext) ! comparison
        IF(mat >= (npat-npat/5)) THEN
            matmon=-1
            IF (nums > 0.AND.dnum(1) > 0.) matmon=NINT(dnum(1),mpi)
            RETURN
        END IF
  
        keystx='bandwidth'
        mat=matint(text(keya:keyb),keystx,npat,ntext) ! comparison
        !         IF(MAT.GE.(NTEXT+NTEXT+3)/3) THEN
        IF(mat >= (npat-npat/5)) THEN
            IF(nums > 0)   mbandw=NINT(dnum(1),mpi)
            IF(mbandw < 0) mbandw=-1
            IF(nums > 1)   lprecm=NINT(dnum(2),mpi)
            RETURN
        END IF
  
        !         KEYSTX='outlierrejection'
        !         MAT=MATINT(TEXT(KEYA:KEYB),KEYSTX,NPAT,NTEXT) ! comparison
        !         WRITE(*,*) KEYSTX,MAT,(NTEXT+NTEXT)/3
        !         IF(MAT.GE.(NTEXT+NTEXT+NTEXT-2)/3) THEN
        !         IF(MAT.GE.(NPAT-NPAT/5)) THEN
        !            CHDFRJ=DNUM(1)
        !            IF(CHDFRJ.LT.3.0) CHDFRJ=100.0
        !            RETURN
        !         END IF
  
        !         KEYSTX='outliersuppression'
        !         MAT=MATINT(TEXT(KEYA:KEYB),KEYSTX,NPAT,NTEXT) ! comparison
        !         WRITE(*,*) KEYSTX,MAT,(NTEXT+NTEXT)/3
        !         IF(MAT.GE.(NTEXT+NTEXT+NTEXT-2)/3) THEN
        !         IF(MAT.GE.(NPAT-NPAT/5)) THEN
        !            LHUBER=DNUM(1)
        !            IF(LHUBER.LE.2) LHUBER=2 ! at least 2 Huber iterations
        !            RETURN
        !         END IF
  
        keystx='outlierdownweighting'
        mat=matint(text(keya:keyb),keystx,npat,ntext) ! comparison
        !         WRITE(*,*) KEYSTX,MAT,(NTEXT+NTEXT)/3
        !         IF(MAT.GE.(NTEXT+NTEXT+NTEXT-2)/3) THEN
        IF(mat >= (npat-npat/5)) THEN
            lhuber=NINT(dnum(1),mpi)
            IF(lhuber > 0.AND.lhuber <= 2) lhuber=2 ! at least 2 Huber iterations (if any)
            RETURN
        END IF
  
        keystx='dwfractioncut'
        mat=matint(text(keya:keyb),keystx,npat,ntext) ! comparison
        IF(mat >= (npat-npat/5)) THEN
            dwcut=REAL(dnum(1),mps)
            IF(dwcut > 0.5) dwcut=0.5
            RETURN
        END IF
  
        keystx='pullrange'
        mat=matint(text(keya:keyb),keystx,npat,ntext) ! comparison
        IF(mat >= (npat-npat/5)) THEN
            prange=ABS(REAL(dnum(1),mps))
            RETURN
        END IF
  
        keystx='subito'
        mat=matint(text(keya:keyb),keystx,npat,ntext) ! comparison
        IF(mat >= (npat-npat/5)) THEN
            isubit=1
            RETURN
        END IF
  
        keystx='force'
        mat=matint(text(keya:keyb),keystx,npat,ntext) ! comparison
        IF(mat >= (npat-npat/5)) THEN
            iforce=1
            RETURN
        END IF

        keystx='memorydebug'
        mat=matint(text(keya:keyb),keystx,npat,ntext) ! comparison
        IF(mat >= (npat-npat/5)) THEN
            memdbg=1
            IF (nums > 0.AND.dnum(1) > 0.0) memdbg=NINT(dnum(1),mpi)
            RETURN
        END IF
  
        keystx='globalcorr'
        mat=matint(text(keya:keyb),keystx,npat,ntext) ! comparison
        IF(mat >= (npat-npat/5)) THEN
            igcorr=1
            RETURN
        END IF

        keystx='printcounts'
        mat=matint(text(keya:keyb),keystx,npat,ntext) ! comparison
        IF(mat >= (npat-npat/5)) THEN
            ipcntr=1
            IF (nums > 0.AND.dnum(1) > 0.0) ipcntr=NINT(dnum(1),mpi)
            RETURN
        END IF

        keystx='weightedcons'
        mat=matint(text(keya:keyb),keystx,npat,ntext) ! comparison
        IF(mat >= (npat-npat/5)) THEN
            iwcons=1
            IF (nums > 0) iwcons=NINT(dnum(1),mpi)
            RETURN
        END IF

        keystx='skipemptycons'
        mat=matint(text(keya:keyb),keystx,npat,ntext) ! comparison
        IF(mat >= (npat-npat/5)) THEN
            iskpec=1
            RETURN
        END IF

        keystx='withelimination'
        mat=matint(text(keya:keyb),keystx,npat,ntext) ! comparison
        IF(mat >= (npat-npat/5)) THEN
            icelim=1
            RETURN
        END IF

        keystx='withmultipliers'
        mat=matint(text(keya:keyb),keystx,npat,ntext) ! comparison
        IF(mat >= (npat-npat/5)) THEN
            icelim=0
            RETURN
        END IF

        keystx='checkinput'
        mat=matint(text(keya:keyb),keystx,npat,ntext) ! comparison
        IF(mat >= (npat-npat/5)) THEN
            icheck=1
            IF (nums > 0) icheck=NINT(dnum(1),mpi)            
            RETURN
        END IF

        keystx='monitorresiduals'
        mat=matint(text(keya:keyb),keystx,npat,ntext) ! comparison
        IF(mat >= (npat-npat/5)) THEN
            imonit=3
            IF (nums > 0) imonit=NINT(dnum(1),mpi)
            IF (nums > 1) measBins=max(measBins,NINT(dnum(2),mpi))
            RETURN
        END IF

        keystx='monitorpulls'
        mat=matint(text(keya:keyb),keystx,npat,ntext) ! comparison
        IF(mat >= (npat-npat/5)) THEN
            imonit=3
            imonmd=1
            IF (nums > 0) imonit=NINT(dnum(1),mpi)
            IF (nums > 1) measBins=max(measBins,NINT(dnum(2),mpi))
            RETURN
        END IF
        
        keystx='scaleerrors'
        mat=matint(text(keya:keyb),keystx,npat,ntext) ! comparison
        IF(mat >= (npat-npat/5)) THEN
            iscerr=1
            IF (nums > 0) dscerr(1:2)=dnum(1)
            IF (nums > 1) dscerr(2)=dnum(2)
            RETURN
        END IF
        
        keystx='iterateentries'
        mat=matint(text(keya:keyb),keystx,npat,ntext) ! comparison
        IF(mat >= (npat-npat/5)) THEN
            iteren=huge(iteren)
            IF (nums > 0) iteren=NINT(dnum(1),mpi)
            RETURN
        END IF

        keystx='threads'
        mat=matint(text(keya:keyb),keystx,npat,ntext) ! comparison
        IF(mat >= (npat-npat/5)) THEN
            iomp=0
            !$          IOMP=1
            !$          IF (IOMP.GT.0) THEN
            !$             IF (NUMS.GE.1.AND.DNUM(1).GT.0.) MTHRD =NINT(dnum(1),mpi)
            !$             IF (NUMS.GE.2) THEN
            !$                MTHRDR=MTHRD
            !$                IF (DNUM(2).GT.0.) MTHRDR=NINT(dnum(2),mpi)
            !$             ENDIF
            !$          ELSE
            WRITE(*,*) 'WARNING: multithreading not available'
            !$          ENDIF
            RETURN
        END IF
  
        keystx='compress'
        mat=matint(text(keya:keyb),keystx,npat,ntext) ! comparison
        IF(mat >= (npat-npat/5)) THEN
            mcmprs=1
            RETURN
        END IF
        
        ! still experimental
        !keystx='extendedStorage'
        !mat=matint(text(keya:keyb),keystx,npat,ntext) ! comparison
        !IF(mat >= (npat-npat/5)) THEN
        !    mextnd=1
        !    ! compression enforced for extended storage (in mpbits)
        !    RETURN
        !END IF
          
        keystx='errlabels'
        mat=matint(text(keya:keyb),keystx,npat,ntext) ! comparison
        IF(mat >= (npat-npat/5).AND.mnrsel < 100) THEN
            nl=MIN(nums,100-mnrsel)
            DO k=1,nl
                lbmnrs(mnrsel+k)=NINT(dnum(k),mpi)
            END DO
            mnrsel=mnrsel+nl
            RETURN
        END IF
  
        keystx='pairentries'
        mat=matint(text(keya:keyb),keystx,npat,ntext) ! comparison
        IF(mat >= (npat-npat/5)) THEN
            !     This option could be implemented to get rid of parameter pairs
            !     that have very few entries - to save matrix memory size.
            IF (nums > 0.AND.dnum(1) > 0.0) THEN
                mreqpe=NINT(dnum(1),mpi)
                IF (nums >= 2.AND.dnum(2) >= dnum(1)) mhispe=NINT(dnum(2),mpi)
                IF (nums >= 3.AND.dnum(3) >= dnum(1)) msngpe=NINT(dnum(3),mpi)
            END IF
            RETURN
        END IF
  
        keystx='wolfe'
        mat=matint(text(keya:keyb),keystx,npat,ntext) ! comparison
        IF(mat >= (npat-npat/5)) THEN
            wolfc1=REAL(dnum(1),mps)
            wolfc2=REAL(dnum(2),mps)
            RETURN
        END IF
  
        ! GF added:
        ! convergence tolerance for minres:
        keystx='mrestol'
        mat=matint(text(keya:keyb),keystx,npat,ntext) ! comparison
        IF(mat >= (npat-npat/5)) THEN
            IF(nums > 0) THEN
                IF (dnum(1) < 1.0E-10_mpd.OR.dnum(1) > 1.0E-04_mpd) THEN
                    WRITE(*,*) 'ERROR: need 1.0D-10 <= MRESTL ',  &
                        '<= 1.0D-04, but get ', dnum(1)
                ELSE
                    mrestl=dnum(1)
                END IF
            END IF
            RETURN
        END IF
        ! GF added end

        keystx='mrestranscond'
        mat=matint(text(keya:keyb),keystx,npat,ntext) ! comparison
        IF(mat >= (npat-npat/5)) THEN
            IF(nums > 0) THEN
                mrtcnd = dnum(1)
            END IF
            RETURN
        END IF

        keystx='mresmode'
        mat=matint(text(keya:keyb),keystx,npat,ntext) ! comparison
        IF(mat >= (npat-npat/5)) THEN
            IF(nums > 0) THEN
                mrmode = INT(dnum(1),mpi)
            END IF
            RETURN
        END IF

        keystx='nofeasiblestart'
        mat=matint(text(keya:keyb),keystx,npat,ntext) ! comparison
        IF(mat >= (npat-npat/5)) THEN
            nofeas=1 ! do not make parameters feasible at start
            RETURN
        END IF
  
        keystx='histprint'
        mat=matint(text(keya:keyb),keystx,npat,ntext) ! comparison
        IF(mat >= ntext-ntext/10) THEN
            !         IF(MAT.GE.(NPAT-NPAT/5)) THEN
            nhistp=1 ! print histograms
            RETURN
        END IF
  
        keystx='fortranfiles'
        mat=matint(text(ia:ib),keystx,npat,ntext) ! comparison
        IF(mat >= ntext-ntext/10) RETURN
  
        keystx='Cfiles'
        mat=matint(text(ia:ib),keystx,npat,ntext) ! comparison
        IF(mat >= ntext-ntext/10) RETURN

        keystx='closeandreopen'
        mat=matint(text(ia:ib),keystx,npat,ntext) ! comparison
        IF(mat >= ntext-ntext/10) RETURN
          
        keystx=keylst(1)
        nkey=1                 ! unknown keyword
        IF(nums /= 0) nkey=0
  
        WRITE(*,*) ' '
        WRITE(*,*) '**************************************************'
        WRITE(*,*) ' '
        WRITE(*,*) 'Unknown keyword(s): ',text(1:MIN(nab,50))
        WRITE(*,*) ' '
        WRITE(*,*) '**************************************************'
        WRITE(*,*) ' '
        lunkno=lunkno+1
  
    END IF
    !     result: NKEY = -1    blank
    !             NKEY =  0    numerical data, no text keyword or unknown
    !             NKEY >  0    keyword NKEY from list, keyword = KEYSTX


    !     content/lastcontent
    !     -------------------
    !     blank            -1
    !     data              0
    !     keyword
    !      unknown          1
    !      parameter        2
    !      constraint       3
    !      measurement      4 
    !      method           5


10  IF(nkey > 0) THEN     ! new keyword
        lkey=nkey
        IF(lkey == 2) THEN              ! parameter
            IF(nums == 3) THEN
                lpvs=NINT(dnum(1),mpi)  ! label
                IF(lpvs /= 0) THEN
                    CALL addItem(lenParameters,listParameters,lpvs,dnum(2)) ! start value
                    CALL addItem(lenPreSigmas,listPresigmas,lpvs,dnum(3))   ! pre-sigma
                ELSE
                    WRITE(*,*) 'Line',nline,' error, label=',lpvs
                END IF
            ELSE IF(nums /= 0) THEN
                kkey=1   ! switch to "unknown"  ?
                WRITE(*,*) 'Wrong text in line',nline
                WRITE(*,*) 'Status: new parameter'
                WRITE(*,*) '> ',text(1:nab)
            END IF
        ELSE IF(lkey == 3) THEN         ! constraint
            !            WRITE(*,*) 'Keyword is constraint!',NUMS,' numerical data'
            IF(nums >= 1.AND.nums <= 2) THEN ! start constraint
                lpvs=0   ! r = r.h.s. value
                CALL addItem(lenConstraints,listConstraints,lpvs,dnum(1))
                lpvs=-1                    ! constraint
                IF(iwcons > 0) lpvs=-2     ! weighted constraint 
                plvs=0.0
                IF(nums == 2) plvs=dnum(2) ! sigma
                CALL addItem(lenConstraints,listConstraints,lpvs,plvs)
            ELSE
                kkey=1   ! switch to "unknown"
                WRITE(*,*) 'Wrong text in line',nline
                WRITE(*,*) 'Status: new keyword constraint'
                WRITE(*,*) '> ',text(1:nab)
            END IF
        ELSE IF(lkey == 4) THEN         ! measurement
            IF(nums == 2) THEN ! start measurement
                numMeasurements=numMeasurements+1
                lpvs=0   ! r = r.h.s. value
                CALL addItem(lenMeasurements,listMeasurements,lpvs,dnum(1))
                lpvs=-1  ! sigma
                CALL addItem(lenMeasurements,listMeasurements,lpvs,dnum(2))
            ELSE
                kkey=1   ! switch to "unknown"
                WRITE(*,*) 'Wrong text in line',nline
                WRITE(*,*) 'Status: new keyword measurement'
                WRITE(*,*) '> ',text(1:nab)
            END IF
    
        ELSE IF(lkey == 5) THEN         ! method
            miter=mitera
            IF(nums >= 1) miter=NINT(dnum(1),mpi)
            IF(miter >= 1) mitera=miter
            dflim=REAL(dnum(2),mps)
            lkey=0
            DO i=1,nmeth
                keystx=methxt(i)
                mat=matint(text(keya:keyb),keystx,npat,ntext) ! comparison
                IF(mat >= ntext-ntext/5) THEN
                    IF(i == 1) THEN            ! diagonalization
                        metsol=2
                        matsto=1
                    ELSE IF(i == 2) THEN       ! inversion
                        metsol=1
                        matsto=1
                    ELSE IF(i == 3) THEN       ! fullMINRES
                        metsol=3
                        matsto=1
                    ELSE IF(i == 4) THEN       ! sparseMINRES
                        metsol=3
                        matsto=2
                    ELSE IF(i == 5) THEN       ! fullMINRES-QLP
                        metsol=4
                        matsto=1
                    ELSE IF(i == 6) THEN       ! sparseMINRES-QLP
                        metsol=4
                        matsto=2
                    END IF
                END IF
            END DO
        END IF
    ELSE IF(nkey == 0) THEN  ! data for continuation
        IF(lkey == 2) THEN              ! parameter
            IF(nums >= 3) THEN   ! store data from this line
                lpvs=NINT(dnum(1),mpi) ! label
                IF(lpvs /= 0) THEN
                    CALL addItem(lenParameters,listParameters,lpvs,dnum(2))  ! start value
                    CALL addItem(lenPreSigmas,listPresigmas,lpvs,dnum(3))    ! pre-sigma
                ELSE
                    WRITE(*,*) 'Line',nline,' error, label=',lpvs
                END IF
            ELSE IF(nums > 1.AND.nums < 3) THEN
                kkey=1   ! switch to "unknown"  ?
                WRITE(*,*) 'Wrong text in line',nline
                WRITE(*,*) 'Status continuation parameter'
                WRITE(*,*) '> ',text(1:nab)
            END IF
    
        ELSE IF(lkey == 3) THEN         ! constraint
            ier=0
            DO i=1,nums,2
                label=NINT(dnum(i),mpi)
                IF(label <= 0) ier=1
            END DO
            IF(MOD(nums,2) /= 0) ier=1 ! reject odd number
            IF(ier == 0) THEN
                DO i=1,nums,2
                    lpvs=NINT(dnum(i),mpi) ! label
                    plvs=dnum(i+1)         ! factor
                    CALL addItem(lenConstraints,listConstraints,lpvs,plvs)
                END DO
            ELSE
                kkey=0
                WRITE(*,*) 'Wrong text in line',nline
                WRITE(*,*) 'Status continuation constraint'
                WRITE(*,*) '> ',text(1:nab)
            END IF
    
        ELSE IF(lkey == 4) THEN         ! measurement
            !            WRITE(*,*) 'continuation                          < ',NUMS
            ier=0
            DO i=1,nums,2
                label=NINT(dnum(i),mpi)
                IF(label <= 0) ier=1
            END DO
            IF(MOD(nums,2) /= 0) ier=1 ! reject odd number
            !            WRITE(*,*) 'IER NUMS ',IER,NUMS
            IF(ier == 0) THEN
                DO i=1,nums,2
                    lpvs=NINT(dnum(i),mpi) ! label
                    plvs=dnum(i+1)         ! factor
                    CALL addItem(lenMeasurements,listMeasurements,lpvs,plvs)
                END DO
            ELSE
                kkey=0
                WRITE(*,*) 'Wrong text in line',nline
                WRITE(*,*) 'Status continuation measurement'
                WRITE(*,*) '> ',text(1:nab)
            END IF
    
        END IF
    END IF
END SUBROUTINE intext

!> add item to list
!!
!! \param [in,out]    length     length of list
!! \param [in,out]    list       list of items
!! \param [in]        label      item label
!! \param [in]        value      item value
!!
SUBROUTINE addItem(length,list,label,value)
    USE mpdef
    USE mpdalc

    INTEGER(mpi), INTENT(IN OUT) :: length
    TYPE(listItem), DIMENSION(:), INTENT(IN OUT), ALLOCATABLE :: list
    INTEGER(mpi), INTENT(IN) :: label
    REAL(mpd), INTENT(IN) :: value

    INTEGER(mpl) :: newSize
    INTEGER(mpl) :: oldSize
    TYPE(listItem), DIMENSION(:), ALLOCATABLE :: tempList

    IF (label > 0.AND.value == 0.) RETURN ! skip zero for valid labels
    IF (length == 0 ) THEN  ! initial list with size = 100
        newSize = 100
        CALL mpalloc(list,newSize,' list ')
    ENDIF
    oldSize=size(list,kind=mpl)
    IF (length >= oldSize) THEN ! increase sizeby 20% + 100
        newSize = oldSize + oldSize/5 + 100
        CALL mpalloc(tempList,oldSize,' temp. list ')
        tempList=list
        CALL mpdealloc(list)
        CALL mpalloc(list,newSize,' list ')
        list(1:oldSize)=tempList(1:oldSize)
        CALL mpdealloc(tempList)
    ENDIF
    ! add to end of list
    length=length+1
    list(length)%label=label
    list(length)%value=value

END SUBROUTINE addItem

!> Start of 'module' printout.
SUBROUTINE mstart(text)
    USE mpdef
    USE mpmod, ONLY: textl

    IMPLICIT NONE
    INTEGER(mpi) :: i
    INTEGER(mpi) :: ka
    INTEGER(mpi) :: kb
    INTEGER(mpi) :: l
    CHARACTER (LEN=*), INTENT(IN)  :: text
    CHARACTER (LEN=16) :: textc
    SAVE
    !     ...
    DO i=1,74
        textl(i:i)='_'
    END DO
    l=LEN(text)
    ka=(74-l)/2
    kb=ka+l-1
    textl(ka:kb)=text(1:l)
    WRITE(*,*) ' '
    WRITE(*,*) textl
    WRITE(*,*) ' '
    textc=text(1:l)//'-end'

    DO i=1,74
        textl(i:i)='_'
    END DO
    l=l+4
    ka=(74-l)/2
    kb=ka+l-1
    textl(ka:kb)=textc(1:l)
    RETURN
END SUBROUTINE mstart

!> End of 'module' printout.
SUBROUTINE mend
    USE mpmod, ONLY: textl

    IMPLICIT NONE
    WRITE(*,*) ' '
    WRITE(*,*) textl
    CALL petime
    WRITE(*,*) ' '
END SUBROUTINE mend

!> Open file.
!!
!! Evtl. move existing file to ~ version.
!!
!! \param[in]  lun    unit number
!! \param[in]  fname  file name

SUBROUTINE mvopen(lun,fname)
    USE mpdef

    IMPLICIT NONE
    INTEGER(mpi) :: l
    INTEGER(mpi), INTENT(IN) :: lun
    CHARACTER (LEN=*), INTENT(IN) :: fname
    CHARACTER (LEN=33) :: nafile
    CHARACTER (LEN=33) :: nbfile
    LOGICAL :: ex
    SAVE
    !     ...
    l=LEN(fname)
    IF(l > 32) THEN
        CALL peend(17,'Aborted, file name too long')
        STOP 'File name too long                    '
    END IF
    nafile=fname
    nafile(l+1:l+1)='~'

    INQUIRE(FILE=nafile(1:l),EXIST=ex)
    IF(ex) THEN
        INQUIRE(FILE=nafile(1:l+1),EXIST=ex)
        IF(ex) THEN
            CALL system('rm '//nafile)
        END IF
        nbfile=nafile
        nafile(l+1:l+1)=' '
        CALL system('mv '//nafile//nbfile)
    END IF
    OPEN(UNIT=lun,FILE=fname)
END SUBROUTINE mvopen

!> Print times.
!!
!! Print the elapsed and total time.

SUBROUTINE petime
    USE mpdef

    IMPLICIT NONE
    REAL, DIMENSION(2) :: ta
    REAL :: rst
    REAL :: delta
    REAL :: rstp
    REAL :: secnd1
    REAL :: secnd2
    INTEGER :: ncount
    INTEGER :: nhour1
    INTEGER :: minut1
    INTEGER :: nsecd1
    INTEGER :: nhour2
    INTEGER :: minut2
    INTEGER :: nsecd2

    SAVE
    DATA ncount/0/
    !     ...
    ncount=ncount+1
    CALL etime(ta,rst)
    IF(ncount > 1) THEN
        delta=rst
        nsecd1=INT(delta,mpi) ! -> integer
        nhour1=nsecd1/3600
        minut1=nsecd1/60-60*nhour1
        secnd1=delta-60*(minut1+60*nhour1)
        delta=rst-rstp
        nsecd2=INT(delta,mpi) ! -> integer
        nhour2=nsecd2/3600
        minut2=nsecd2/60-60*nhour2
        secnd2=delta-60*(minut2+60*nhour2)
        WRITE(*,101) nhour1,minut1,secnd1, nhour2,minut2,secnd2
    END IF

    rstp=rst
    RETURN
101 FORMAT(i4,' h',i3,' min',f5.1,' sec total',18X,'elapsed',  &
        i4,' h',i3,' min',f5.1,' sec')
END SUBROUTINE petime                          ! print

!> Print exit code.
!!
!! Print exit code and message.
!!
!! \param[in]  icode     exit code
!! \param[in]  cmessage  exit massage

SUBROUTINE peend(icode, cmessage)
    USE mpdef

    IMPLICIT NONE
    INTEGER(mpi), INTENT(IN) :: icode
    CHARACTER (LEN=*), INTENT(IN) :: cmessage

    CALL mvopen(9,'millepede.end')
    WRITE(9,101) icode, cmessage
101 FORMAT(1X,I4,3X,A)
    RETURN

END SUBROUTINE peend

!> Open binary file.
!!
!! \param[in]  kfile     file number
!! \param[in]  ithr      thread number ([1..nthrd] - close and reopen) or 0 (next file - keep open) for C files
!! \param[out] ierr      error flag
!!
SUBROUTINE binopn(kfile, ithr, ierr)
    USE mpmod

    IMPLICIT NONE
    INTEGER(mpi), INTENT(IN) :: kfile
    INTEGER(mpi), INTENT(IN) :: ithr
    INTEGER(mpi), INTENT(OUT) :: ierr

    INTEGER(mpi), DIMENSION(13) :: ibuff
    INTEGER(mpi) :: ioff
    INTEGER(mpi) :: ios
    INTEGER(mpi) :: k
    INTEGER(mpi) :: lfn
    INTEGER(mpi) :: lun
    INTEGER(mpi) :: moddate
    CHARACTER (LEN=1024) :: fname

    ierr=0
    lun=ithr
    ! modification date (=0: open for first time, >0: reopen, <0: unknown )
    moddate=yfd(kfile) 
    ! file name
    ioff=sfd(1,kfile)
    lfn=sfd(2,kfile)
    FORALL (k=1:lfn) fname(k:k)=tfd(ioff+k)
    !print *, " opening binary ", kfile, ithr, moddate, " : ", fname(1:lfn)
    ! open
    ios=0 
    IF(kfile <= nfilf) THEN
        ! Fortran file
        lun=kfile+10 
        OPEN(lun,FILE=fname(1:lfn),IOSTAT=ios, FORM='UNFORMATTED')
        print *, ' lun ', lun, ios
#ifdef READ_C_FILES
    ELSE
        ! C file
        CALL openc(fname(1:lfn),lun,ios)
#else
        WRITE(*,*) 'Opening of C-files not supported.'
        ierr=1
        RETURN
#endif
    END IF
    IF(ios /= 0) THEN
        ierr=1
        WRITE(*,*) 'Open error for file ',fname(1:lfn), ios
        IF (moddate /= 0) THEN
            CALL peend(15,'Aborted, open error(s) for binary files')
            STOP 'PEREAD: open error                                      '
        ENDIF
        RETURN
    END IF
    ! get status
    CALL stat(fname(1:lfn),ibuff,ios)
    !print *, ' STAT ', ios, ibuff(10), moddate
    IF(ios /= 0) THEN
        ierr=1
        WRITE(*,*) 'STAT error for file ',fname(1:lfn), ios
        ibuff(10)=-1
    END IF
    ! check/store modification date
    IF (moddate /= 0) THEN    
        IF (ibuff(10) /= moddate) THEN
            CALL peend(19,'Aborted, binary file(s) modified')
            STOP 'PEREAD: file modified                                   '
        END IF
    ELSE
        yfd(kfile)=ibuff(10)
    END IF          
    RETURN

END SUBROUTINE binopn

!> Close binary file.
!!
!! \param[in]  kfile     file number
!! \param[in]  ithr      thread number ([1..nthrd] - close and reopen) for C files
!!
SUBROUTINE bincls(kfile, ithr)
    USE mpmod

    IMPLICIT NONE
    INTEGER(mpi), INTENT(IN) :: kfile
    INTEGER(mpi), INTENT(IN) :: ithr

    INTEGER(mpi) :: lun
    
    lun=ithr
    !print *, " closing binary ", kfile, ithr
    IF(kfile <= nfilf) THEN ! Fortran file
        lun=kfile+10 
        CLOSE(lun)
#ifdef READ_C_FILES
    ELSE ! C file
        CALL closec(lun)
#endif
    END IF
    
END SUBROUTINE bincls
    
!> Rewind binary file.
!!
!! \param[in]  kfile     file number
!!
SUBROUTINE binrwd(kfile)
    USE mpmod 
    
    IMPLICIT NONE
    INTEGER(mpi), INTENT(IN) :: kfile

    INTEGER(mpi) :: lun
           
    !print *, " rewinding binary ", kfile
    IF (kfile <= nfilf) THEN
        lun=kfile+10
        REWIND lun
#ifdef READ_C_FILES
    ELSE
        lun=kfile-nfilf
        CALL resetc(lun)
#endif
    END IF 

END SUBROUTINE binrwd
                    
                    
! ----- accurate summation ----(from mpnum) ---------------------------------

!> Accurate summation.
!!
!! \param[in]   add  summand

SUBROUTINE addsum(add)
    USE mpmod

    IMPLICIT NONE
    REAL(mpd):: add
    INTEGER(mpi) ::nadd
    !     ...
    nadd=INT(add,mpi)                ! convert to integer
    accurateNsum=accurateNsum+nadd               ! sum integer
    accurateDsum=accurateDsum+(add-REAL(nadd,mpd)) ! sum remainder
    IF(accurateDsum > 16.0_mpd) THEN       ! + - 16
        accurateDsum=accurateDsum-16.0_mpd
        accurateNsum=accurateNsum+16
    END IF
    IF(accurateNsum > nexp20) THEN      ! if > 2^20: + - 2^20
        accurateNexp=accurateNexp+1
        accurateNsum=accurateNsum-nexp20
    END IF
    RETURN
END SUBROUTINE addsum

!> Get accurate sum.
!!
!! \param[out]   asum   accurate sum

SUBROUTINE getsum(asum)
    USE mpmod

    IMPLICIT NONE
    REAL(mpd), INTENT(OUT) ::asum
    asum=(accurateDsum+REAL(accurateNsum,mpd))+REAL(accurateNexp,mpd)*REAL(nexp20,mpd)
    accurateDsum=0.0_mpd
    accurateNsum=0
    accurateNexp=0
    RETURN
END SUBROUTINE getsum
