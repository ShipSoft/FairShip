!> \file
!! Bit field counters.
!!
!! \author Volker Blobel, University Hamburg, 2005-2009 (initial Fortran77 version)
!! \author Claus Kleinwort, DESY (maintenance and developement)
!!
!! \copyright
!! Copyright (c) 2009 - 2015 Deutsches Elektronen-Synchroton,
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
!! Count pairs of global parameters for sparse storage of global matrix,
!! apply pair entries cut and build (compressed) sparsity structure (row offsets, column lists).
!!
!! In sparse storage mode for each row the list of column indices with non zero elements
!! (and those elements) are stored. With compression this list is represented by the
!! first column and their number for continous regions (encoded in single INTEGER(mpi) words).
!! Rare elements may be stored in single precision.
!!
!! An additional bit map is used to monitor the parameter pairs for measurements (or 'equations').
!!

!> Bit field data.
MODULE mpbits
    USE mpdef
    IMPLICIT NONE

    INTEGER(mpl) :: ndimb  !< dimension for bit (field) array
    INTEGER(mpl) :: ndimb2 !< dimension for bit map
    INTEGER(mpi) :: n      !< matrix size (counters)
    INTEGER(mpi) :: n2     !< matrix size (map)
    INTEGER(mpi) :: ibfw   !< bit field width
    INTEGER(mpi) :: ireqpe !< min number of pair entries
    INTEGER(mpi) :: isngpe !< upper bound for pair entry single precision storage
    INTEGER(mpi) :: icmprs !< compression flag for sparsity (column indices)
    INTEGER(mpi) :: iextnd !< flag for extended storage (both 'halves' of sym. mat. for improved access patterns)
    INTEGER(mpi) :: nspc   !< number of precision for sparse global matrix (1=D, 2=D+f)
    INTEGER(mpi) :: mxcnt  !< max value for bit field counters
    INTEGER(mpi) :: nencdm !< max value for column counter
    INTEGER(mpi) :: nencdb !< number of bits for encoding column counter
    INTEGER(mpi) :: nthrd  !< number of threads
    INTEGER(mpi), DIMENSION(:), ALLOCATABLE :: bitFieldCounters !< fit field counters for global parameters pairs (tracks)
    INTEGER(mpi), DIMENSION(:), ALLOCATABLE :: bitMap !< fit field map for global parameters pairs (measurements)
    INTEGER(mpi), PARAMETER :: bs = BIT_SIZE(1_mpi)  !< number of bits in INTEGER(mpi)

END MODULE mpbits

!> Fill bit fields (counters).
!!
!! \param [in]    im     first index
!! \param [in]    jm     second index
!! \param [in]    inc    increment (usually 1)
!!
SUBROUTINE inbits(im,jm,inc)        ! include element (I,J)
    USE mpbits

    INTEGER(mpi), INTENT(IN) :: im
    INTEGER(mpi), INTENT(IN) :: jm
    INTEGER(mpi), INTENT(IN) :: inc

    INTEGER(mpl) :: l
    INTEGER(mpl) :: ll
    INTEGER(mpi) :: i
    INTEGER(mpi) :: j
    INTEGER(mpi) :: noffj
    INTEGER(mpi) :: m
    INTEGER(mpi) :: mm
    INTEGER(mpi) :: icount
    INTEGER(mpi) :: ib
    INTEGER(mpi) :: jcount
    INTEGER(mpl) :: noffi
    LOGICAL :: btest

    IF(im == jm) RETURN  ! diagonal
    j=MIN(im,jm)
    i=MAX(im,jm)
    IF(j <= 0) RETURN    ! out low
    IF(i > n) RETURN    ! out high
    noffi=INT(i-1,mpl)*INT(i-2,mpl)*INT(ibfw,mpl)/2 ! for J=1
    noffj=(j-1)*ibfw
    l=noffi/bs+i+noffj/bs ! row offset + column offset
    !     add I instead of 1 to keep bit maps of different rows in different words (openMP !)
    m=MOD(noffj,bs)
    IF (ibfw <= 1) THEN
        bitFieldCounters(l)=ibset(bitFieldCounters(l),m)
    ELSE
        !        get counter from bit field
        ll=l
        mm=m
        icount=0
        DO ib=0,ibfw-1
            IF (btest(bitFieldCounters(ll),mm)) icount=ibset(icount,ib)
            mm=mm+1
            IF (mm >= bs) THEN
                ll=ll+1
                mm=mm-bs
            END IF
        END DO
        !        increment
        jcount=icount
        icount=MIN(icount+inc,mxcnt)
        !        store counter into bit field
        IF (icount /= jcount) THEN
            ll=l
            mm=m
            DO ib=0,ibfw-1
                IF (btest(icount,ib)) THEN
                    bitFieldCounters(ll)=ibset(bitFieldCounters(ll),mm)
                ELSE
                    bitFieldCounters(ll)=ibclr(bitFieldCounters(ll),mm)
                END IF
                mm=mm+1
                IF (mm >= bs) THEN
                    ll=ll+1
                    mm=mm-bs
                END IF
            END DO
        END IF
    END IF
    RETURN

END SUBROUTINE inbits

!> Calculate bit (field) array size, encoding.
!!
!! \param [in]    in        matrix size
!! \param [in]    jreqpe    min number of pair entries
!! \param [in]    jhispe    mupper bound for pair entry histogrammimg
!! \param [in]    jsngpe    upper bound for pair entry single precision storage
!! \param [in]    jcmprs    compression flag for sparsity (column indices)
!! \param [in]    jextnd    flag for extended storage
!! \param [out]   idimb     dimension for bit (field) array
!! \param [out]   iencdb    number of bits for encoding column counter
!! \param [out]   ispc      number of precision for sparse global matrix
!!
SUBROUTINE clbits(in,jreqpe,jhispe,jsngpe,jcmprs,jextnd,idimb,iencdb,ispc)
    USE mpbits
    USE mpdalc

    INTEGER(mpi), INTENT(IN) :: in
    INTEGER(mpi), INTENT(IN) :: jreqpe
    INTEGER(mpi), INTENT(IN) :: jhispe
    INTEGER(mpi), INTENT(IN) :: jsngpe
    INTEGER(mpi), INTENT(IN) :: jcmprs
    INTEGER(mpi), INTENT(IN) :: jextnd
    INTEGER(mpl), INTENT(OUT) :: idimb
    INTEGER(mpi), INTENT(OUT) :: iencdb
    INTEGER(mpi), INTENT(OUT) :: ispc

    INTEGER(mpl) :: noffd
    INTEGER(mpi) :: i
    INTEGER(mpi) :: icount
    INTEGER(mpi) :: mb
    INTEGER(mpi) :: nbcol
    !$    INTEGER(mpi) :: OMP_GET_MAX_THREADS
    ! save input parameter 
    n=in
    ireqpe=jreqpe
    isngpe=jsngpe
    icmprs=jcmprs+jextnd ! enforce compression for extended storage
    iextnd=jextnd
    ! number of precision types (D, F)
    ispc=1
    if (jsngpe>0) ispc=2
    nspc = ispc
    ! bit field size
    icount=MAX(jsngpe+1,jhispe)
    icount=MAX(jreqpe,icount)
    ibfw=1 ! number of bits needed to count up to ICOUNT
    mxcnt=1
    DO i=1,30
        IF (icount > mxcnt) THEN
            ibfw=ibfw+1
            mxcnt=mxcnt*2+1
        END IF
    END DO
    ! bit field array size
    noffd=INT(n,mpl)*INT(n-1,mpl)*INT(ibfw,mpl)/2
    ndimb=noffd/bs+n
    idimb=ndimb
    mb=INT(4.0E-6*REAL(ndimb,mps),mpi)
    WRITE(*,*) ' '
    WRITE(*,*) 'CLBITS: symmetric matrix of dimension',n
    WRITE(*,*) 'CLBITS: off-diagonal elements',noffd
    IF (mb > 0) THEN
        WRITE(*,*) 'CLBITS: dimension of bit-array',ndimb , '(',mb,'MB)'
    ELSE
        WRITE(*,*) 'CLBITS: dimension of bit-array',ndimb , '(< 1 MB)'
    END IF
    CALL mpalloc(bitFieldCounters,ndimb,'INBITS: bit storage')
    bitFieldCounters=0
    !     encoding for compression
    nbcol=bs/2    ! one half of the bits for column number, other for column counter
    DO i=bs/2,bs-2
        IF (btest(n,i)) nbcol=i+1 ! more bits for column number
    END DO
    nencdb=bs-nbcol
    iencdb=nencdb
    nencdm=ishft(1,nencdb)-1
    nthrd=1
    !$ NTHRD=OMP_GET_MAX_THREADS()
    RETURN
END SUBROUTINE clbits

!> Analyze bit fields.
!!
!! \param [out]     ndims   (1): (reduced) size of bit array; (2): size of column lists;
!!                          (3/4): number of (double/single precision) off diagonal elements;
!! \param[out]     ncmprs  compression info (per row)
!! \param[out]     nsparr  row offsets
!! \param[in]      ihst    >0: histogram number
!!
SUBROUTINE ndbits(ndims,ncmprs,nsparr,ihst)
    USE mpbits

    INTEGER(mpl), DIMENSION(4), INTENT(OUT) :: ndims
    INTEGER(mpi), DIMENSION(:), INTENT(OUT) :: ncmprs
    INTEGER(mpl), DIMENSION(:,:), INTENT(OUT) :: nsparr
    INTEGER(mpi), INTENT(IN) :: ihst

    INTEGER(mpi) :: nwcp(0:1)
    INTEGER(mpi) :: irgn(2)
    INTEGER(mpi) :: inr(2)
    INTEGER(mpi) :: ichunk
    INTEGER(mpi) :: i
    INTEGER(mpi) :: j
    INTEGER(mpi) :: m
    INTEGER(mpi) :: last
    INTEGER(mpi) :: lrgn
    INTEGER(mpi) :: next
    INTEGER(mpi) :: icp
    INTEGER(mpi) :: mm
    INTEGER(mpi) :: jp
    INTEGER(mpi) :: nj
    INTEGER(mpi) :: ib
    INTEGER(mpi) :: ir
    INTEGER(mpi) :: icount
    INTEGER(mpi) :: iproc
    INTEGER(mpi) :: iword
    INTEGER(mpi) :: k
    INTEGER(mpi) :: mb
    INTEGER(mpi) :: n1
    INTEGER(mpl) :: ll
    INTEGER(mpl) :: lb
    INTEGER(mpl) :: nin
    INTEGER(mpl) :: ntot
    INTEGER(mpl) :: noffi
    REAL(mps) :: cpr
    REAL(mps) :: fracu
    REAL(mps) :: fracz
    LOGICAL :: btest
    !$    INTEGER(mpi) :: OMP_GET_THREAD_NUM

    ndims(1)=ndimb
    ndims(2)=0
    ndims(3)=0
    ndims(4)=0
    ntot=0
    ll=0
    lb=0
    ichunk=MIN((n+nthrd-1)/nthrd/32+1,256)
    IF (ibfw > 1.OR.icmprs > 0) THEN
        ! reduce bit field counters to (precision type) bits, analyze precision type bit fields ('1st half' (j<i))

        ! parallelize row loop
        ! private copy of NTOT for each thread, combined at end, init with 0.
        !$OMP  PARALLEL DO &
        !$OMP  PRIVATE(I,NOFFI,LL,MM,LB,MB,IWORD,IPROC,J,ICOUNT,IB,INR,IRGN,LAST,LRGN,NEXT,JP,IR) &
        !$OMP  REDUCTION(+:NTOT) &
        !$OMP  SCHEDULE(DYNAMIC,ICHUNK)
        DO i=1,n
            noffi=INT(i-1,mpl)*INT(i-2,mpl)*INT(ibfw,mpl)/2
            ll=noffi/bs+i
            mm=0
            lb=ll
            mb=0
            iword=0 ! temporary bit fields
            iproc=0
            !$ IPROC=OMP_GET_THREAD_NUM()         ! thread number
            inr(1)=0
            inr(2)=0
            irgn(1)=0
            irgn(2)=0
            last=0
            lrgn=0

            DO j=1,i-1
                ! get (pair) counter
                icount=0
                next=0
                DO ib=0,ibfw-1
                    IF (btest(bitFieldCounters(ll),mm)) icount=ibset(icount,ib)
                    mm=mm+1
                    IF (mm >= bs) THEN
                        ll=ll+1
                        mm=mm-bs
                    END IF
                END DO

                IF (icount > 0) THEN
                    ntot=ntot+1
                    IF (iproc == 0.AND.ihst > 0) CALL hmpent(ihst,REAL(icount,mps))
                END IF

                ! keep pair ?
                IF (icount >= ireqpe) THEN
                    next=1 ! double
                    IF (icount <= isngpe) next=2 ! single
                    iword=ibset(iword,mb+next-1)
                    inr(next)=inr(next)+1
                    IF (next /= last.OR.lrgn >= nencdm) THEN
                        irgn(next)=irgn(next)+1
                        lrgn=0
                    END IF
                    lrgn=lrgn+1
                END IF
                last=next

                mb=mb+nspc
                IF (mb >= bs) THEN
                    bitFieldCounters(lb)=iword ! store
                    iword=0
                    lb=lb+1
                    mb=mb-bs
                END IF
            END DO
            bitFieldCounters(lb)=iword ! store

            ! save row statistics
            ir=i+1
            DO jp=1,nspc
                nsparr(1,ir)=irgn(jp)    ! number of regions per row and precision
                nsparr(2,ir)=inr(jp)     ! number of columns per row and precision
                ir=ir+n+1
            END DO
        END DO

        ! analyze precision type bit fields for extended storage, check for row compression

        ! parallelize row loop
        ! private copy of NDIMS for each thread, combined at end, init with 0.
        !$OMP  PARALLEL DO &
        !$OMP  PRIVATE(I,NOFFI,NOFFJ,LL,MM,INR,IRGN,LAST,LRGN,J,NEXT,ICP,NWCP,JP,IR,IB) &
        !$OMP  REDUCTION(+:NDIMS) &
        !$OMP  SCHEDULE(DYNAMIC,ICHUNK)
        DO i=1,n
            ! restore row statistics
            irgn(1)=INT(nsparr(1,i+1),mpi)
            irgn(2)=INT(nsparr(1,i+n+2),mpi)
            inr(1)=INT(nsparr(2,i+1),mpi)
            inr(2)=INT(nsparr(2,i+n+2),mpi)

            ! analyze precision type bit fields for extended storage ('2nd half' (j>i) too) ?
            IF (iextnd > 0) THEN

                noffj=(i-1)*nspc
                mm=MOD(noffj,bs)

                last=0
                lrgn=0

                ! remaining columns
                DO j=i+1, n
                    ! index for pair (J,I)
                    noffi=INT(j-1,mpl)*INT(j-2,mpl)*INT(ibfw,mpl)/2 ! for I=1
                    ll=noffi/bs+j+noffj/bs ! row offset + column offset

                    ! get precision type
                    next=0
                    DO ib=0,nspc-1
                        IF (btest(bitFieldCounters(ll),mm+ib)) next=ibset(next,ib)
                    END DO

                    ! keep pair ?
                    IF (next > 0) THEN
                        inr(next)=inr(next)+1
                        IF (next /= last.OR.lrgn >= nencdm) THEN
                            irgn(next)=irgn(next)+1
                            lrgn=0
                        END IF
                        lrgn=lrgn+1
                    END IF
                    last=next
                END DO
            END IF

            ! row statistics, compression
            ir=i+1
            DO jp=1,nspc
                icp=0
                nwcp(0)=inr(jp)                        ! list of column indices (default)
                IF (inr(jp) > 0) THEN
                    nwcp(1)=irgn(jp)+(irgn(jp)+7)/8    ! list of regions of consecutive columns (and group offsets)
                    ! compress row ?
                    IF ((nwcp(1) < nwcp(0).AND.icmprs > 0).OR.iextnd > 0) THEN
                        icp=1
                        ncmprs(i+n*(jp-1))=irgn(jp)    ! number of regions per row and precision
                    END IF
                    ! total space
                    ndims(2)   =ndims(2)   +nwcp(icp)
                    ndims(jp+2)=ndims(jp+2)+nwcp(0)
                END IF
                ! per row and precision
                nsparr(1,ir)=nwcp(icp)
                nsparr(2,ir)=nwcp(0)
                ir=ir+n+1
            END DO
        END DO
        !$OMP END PARALLEL DO

        ! sum up, fill row offsets
        lb=1
        n1=0
        ll=n+1
        DO jp=1,nspc
            DO i=1,n
                n1=n1+1
                nsparr(1,n1)=lb
                nsparr(2,n1)=ll
                lb=lb+nsparr(1,n1+1)
                ll=ll+nsparr(2,n1+1)
            END DO
            n1=n1+1
            nsparr(1,n1)=lb
            nsparr(2,n1)=ll
            ll=1
        END DO

    ELSE

        nin=0
        nsparr(1,1)=1
        nsparr(2,1)=n+1
        n1=1
        DO i=1,n
            noffi=INT(i-1,mpl)*INT(i-2,mpl)/2
            ll=noffi/bs+i
            nj=(i-1)/bs
            DO k=0,nj
                DO m=0,bs-1
                    IF(btest(bitFieldCounters(ll+k),m)) nin=nin+1
                END DO
            END DO
            n1=n1+1
            nsparr(1,n1)=nsparr(1,1)+nin
            nsparr(2,n1)=nsparr(2,1)+nin
        END DO
        ndims(2)=nin
        ndims(3)=nin
        ntot=nin

    END IF

    nin=ndims(3)+ndims(4)
    fracz=200.0*REAL(ntot,mps)/REAL(n,mps)/REAL(n-1,mps)
    fracu=200.0*REAL(nin,mps)/REAL(n,mps)/REAL(n-1,mps)
    WRITE(*,*) ' '
    WRITE(*,*) 'NDBITS: number of diagonal elements',n
    WRITE(*,*) 'NDBITS: number of used off-diagonal elements',nin
    WRITE(*,1000) 'fraction of non-zero off-diagonal elements', fracz
    WRITE(*,1000) 'fraction of used off-diagonal elements', fracu
    IF (icmprs /= 0) THEN
        cpr=100.0*REAL(mpi*ndims(2)+mpd*ndims(3)+mps*ndims(4),mps)/REAL((mpd+mpi)*nin,mps)
        WRITE(*,1000) 'compression ratio for off-diagonal elements', cpr
    END IF
1000 FORMAT(' NDBITS: ',a,f6.2,' %')
    RETURN
END SUBROUTINE ndbits

!> Check sparsity of matrix.
!!
!! \param [out]    ndims   (1): (reduced) size of bit array; (2): size of column lists;
!!                         (3/4): number of (double/single precision) off diagonal elements;
!!
SUBROUTINE ckbits(ndims)
    USE mpbits

    INTEGER(mpl), DIMENSION(4), INTENT(OUT) :: ndims

    INTEGER(mpi) :: nwcp(0:1)
    INTEGER(mpi) :: irgn(2)
    INTEGER(mpi) :: inr(2)
    INTEGER(mpl) :: ll
    INTEGER(mpl) :: noffi
    INTEGER(mpi) :: i
    INTEGER(mpi) :: j
    INTEGER(mpi) :: last
    INTEGER(mpi) :: lrgn
    INTEGER(mpi) :: next
    INTEGER(mpi) :: icp
    INTEGER(mpi) :: ib
    INTEGER(mpi) :: icount
    INTEGER(mpi) :: kbfw
    INTEGER(mpi) :: jp
    INTEGER(mpi) :: mm
    LOGICAL :: btest

    DO i=1,4
        ndims(i)=0
    END DO
    kbfw=1
    IF (ibfw > 1.AND.icmprs > 0) kbfw=2
    ll=0

    DO i=1,n
        noffi=INT(i-1,mpl)*INT(i-2,mpl)*INT(ibfw,mpl)/2
        ll=noffi/bs+i
        mm=0
        inr(1)=0
        inr(2)=0
        irgn(1)=0
        irgn(2)=0
        last=0
        lrgn=0
        DO j=1,i-1
            icount=0
            next=0
            DO ib=0,ibfw-1
                IF (btest(bitFieldCounters(ll),mm)) icount=ibset(icount,ib)
                mm=mm+1
                IF (mm >= bs) THEN
                    ll=ll+1
                    mm=mm-bs
                END IF
            END DO

            IF (icount > 0) ndims(1)=ndims(1)+1
            !           keep pair ?
            IF (icount >= ireqpe) THEN
                next=1 ! double
                IF (icount <= isngpe) next=2 ! single
                inr(next)=inr(next)+1
                IF (next /= last.OR.lrgn >= nencdm) THEN
                    irgn(next)=irgn(next)+1
                    lrgn=0
                END IF
                lrgn=lrgn+1
            END IF
            last=next
        END DO

        IF (icmprs > 0) THEN
            DO jp=1,kbfw
                IF (inr(jp) > 0) THEN
                    icp=0
                    nwcp(0)=inr(jp)                    ! list of column indices (default)
                    nwcp(1)=irgn(jp)+(irgn(jp)+7)/8    ! list of regions of consecutive columns
                    !                 compress row ?
                    IF (nwcp(1) < nwcp(0).OR. iextnd > 0) icp=1
                    ndims(2)   =ndims(2)   +nwcp(icp)
                    ndims(jp+2)=ndims(jp+2)+nwcp(0)
                END IF
            END DO
        ELSE
            ndims(2)=ndims(2)+inr(1)
            ndims(3)=ndims(3)+inr(1)
        END IF

    END DO

    RETURN
END SUBROUTINE ckbits

!> Create sparsity information.
!!
!! \param[in ]    nsparr  row offsets
!! \param[out]    nsparc  column indices
!! \param[in,out] ncmprs  compression info (per row, in: number of all regions, out: number of regions in 1st half (for accessing 2nd half))
!!
SUBROUTINE spbits(nsparr,nsparc,ncmprs)               ! collect elements
    USE mpbits
    USE mpdalc

    INTEGER(mpl), DIMENSION(:,:), INTENT(IN) :: nsparr
    INTEGER(mpi), DIMENSION(:), INTENT(OUT) :: nsparc
    INTEGER(mpi), DIMENSION(:), INTENT(INOUT) :: ncmprs

    INTEGER(mpl) :: kl
    INTEGER(mpl) :: l
    INTEGER(mpl) :: ll
    INTEGER(mpl) :: l1
    INTEGER(mpl) :: k8
    INTEGER(mpl) :: n1
    INTEGER(mpl) :: noffi
    INTEGER(mpi) :: i
    INTEGER(mpi) :: j
    INTEGER(mpi) :: j1
    INTEGER(mpi) :: jb
    INTEGER(mpi) :: jn
    INTEGER(mpi) :: m
    INTEGER(mpi) :: ichunk
    INTEGER(mpi) :: next
    INTEGER(mpi) :: last
    INTEGER(mpi) :: lrgn
    INTEGER(mpi) :: nrgn
    INTEGER(mpi) :: nrgn8
    LOGICAL :: btest

    ichunk=MIN((n+nthrd-1)/nthrd/32+1,256)

    DO jb=0,nspc-1
        ! parallelize row loop
        !$OMP  PARALLEL DO &
        !$OMP  PRIVATE(I,N1,NOFFI,NOFFJ,L,M,KL,L1,NRGN,NRGN8,K8,LAST,LRGN,LL,J1,JN,J,NEXT) &
        !$OMP  SCHEDULE(DYNAMIC,ICHUNK)
        DO i=1,n
            n1=i+jb*(n+1)
            noffi=INT(i-1,mpl)*INT(i-2,mpl)*INT(ibfw,mpl)/2
            l=noffi/bs+i
            m=jb
            kl=nsparr(1,n1)-1  ! pointer to row in NSPARC
            l1=nsparr(2,n1)    ! pointer to row in sparse matrix
            nrgn=ncmprs(i+n*jb)! compression  (number of consecutive regions)
            nrgn8=(nrgn+7)/8   ! number of groups (1 offset per group)
            k8=kl
            kl=kl+nrgn8        ! reserve space of offsets
            last=0
            lrgn=0
            ll=l1-1
            j1=0
            jn=0

            DO j=1,i-1         !  loop for off-diagonal elements
                next=0
                IF(bitFieldCounters(l) /= 0) THEN
                    IF(btest(bitFieldCounters(l),m)) THEN
                        ll=ll+1
                        IF (nrgn <= 0) THEN
                            kl=kl+1
                            nsparc(kl)=j ! column index
                        ELSE
                            next=1
                            IF (last == 0.OR.jn >= nencdm) THEN
                                IF (MOD(lrgn,8) == 0) THEN
                                    k8=k8+1
                                    nsparc(k8)=INT(ll-l1,mpi)
                                END IF
                                lrgn=lrgn+1
                                kl=kl+1
                                j1=ishft(j,nencdb)
                                jn=0
                            END IF
                            jn=jn+1
                            nsparc(kl)=ior(j1,jn)
                        END IF
                    END IF
                END IF
                last=next
                m=m+nspc
                IF (m >= bs) THEN
                    m=m-bs
                    l=l+1
                END IF
            END DO

            ! extended storage ('2nd half' too) ?
            IF (iextnd > 0) THEN
                noffj=(i-1)*nspc
                m=MOD(noffj,bs)+jb
                last=0
                ncmprs(i+n*jb)=lrgn ! remember number of regions in 1st half (j<i)
                ! remaining columns
                DO j=i+1, n
                    ! index for pair (J,I)
                    noffi=INT(j-1,mpl)*INT(j-2,mpl)*INT(ibfw,mpl)/2 ! for I=1
                    l=noffi/bs+j+noffj/bs ! row offset + column offset
                    next=0
                    IF(btest(bitFieldCounters(l),m)) THEN
                        ll=ll+1
                        IF (nrgn <= 0) THEN
                            kl=kl+1
                            nsparc(kl)=j ! column index
                        ELSE
                            next=1
                            IF (last == 0.OR.jn >= nencdm) THEN
                                IF (MOD(lrgn,8) == 0) THEN
                                    k8=k8+1
                                    nsparc(k8)=INT(ll-l1,mpi)
                                END IF
                                lrgn=lrgn+1
                                kl=kl+1
                                j1=ishft(j,nencdb)
                                jn=0
                            END IF
                            jn=jn+1
                            nsparc(kl)=ior(j1,jn)
                        END IF
                    END IF
                    last=next

                END DO
            END IF

        END DO
    !$OMP END PARALLEL DO

    END DO

    n1=(n+1)*ibfw
    WRITE(*,*) ' '
    WRITE(*,*) 'SPBITS: sparse structure constructed ',nsparr(1,n1), ' words'
    WRITE(*,*) 'SPBITS: dimension parameter of matrix',nsparr(2,1)-1
    IF (ibfw <= 1) THEN
        WRITE(*,*) 'SPBITS: index of last used location',nsparr(2,n1)-1
    ELSE
        WRITE(*,*) 'SPBITS: index of last used double',nsparr(2,n1/2)-1
        WRITE(*,*) 'SPBITS: index of last used single',nsparr(2,n1)-1
    END IF
    CALL mpdealloc(bitFieldCounters)
    RETURN
END SUBROUTINE spbits


!> Clear (additional) bit map.
!!
!! \param [in]    in        matrix size
!
SUBROUTINE clbmap(in)
    USE mpbits
    USE mpdalc

    INTEGER(mpi), INTENT(IN) :: in

    INTEGER(mpl) :: noffd
    INTEGER(mpi) :: mb

    ! save input parameter 
    n2=in    
    ! bit field array size
    noffd=INT(n2,mpl)*INT(n2-1,mpl)/2
    ndimb2=noffd/bs+n2
    mb=INT(4.0E-6*REAL(ndimb2,mps),mpi)
    WRITE(*,*) ' '
    IF (mb > 0) THEN
        WRITE(*,*) 'CLBMAP: dimension of bit-map',ndimb2 , '(',mb,'MB)'
    ELSE
        WRITE(*,*) 'CLBMAP: dimension of bit-map',ndimb2 , '(< 1 MB)'
    END IF
    CALL mpalloc(bitMap,ndimb2,'INBMAP: bit storage')
    bitMap=0
    RETURN
END SUBROUTINE clbmap    

!> Fill bit map.
!!
!! \param [in]    im     first index
!! \param [in]    jm     second index
!!
SUBROUTINE inbmap(im,jm)        ! include element (I,J)
    USE mpbits

    INTEGER(mpi), INTENT(IN) :: im
    INTEGER(mpi), INTENT(IN) :: jm

    INTEGER(mpl) :: l
    INTEGER(mpi) :: i
    INTEGER(mpi) :: j
    INTEGER(mpi) :: noffj
    INTEGER(mpl) :: noffi
    INTEGER(mpi) :: m

    IF(im == jm) RETURN  ! diagonal
    j=MIN(im,jm)
    i=MAX(im,jm)
    IF(j <= 0) RETURN    ! out low
    IF(i > n2) RETURN    ! out high
    noffi=INT(i-1,mpl)*INT(i-2,mpl)/2 ! for J=1
    noffj=(j-1)
    l=noffi/bs+i+noffj/bs ! row offset + column offset
    !     add I instead of 1 to keep bit maps of different rows in different words (openMP !)
    m=MOD(noffj,bs)
    bitMap(l)=ibset(bitMap(l),m)
    RETURN
END SUBROUTINE inbmap 

!> Get pairs (statistic) from map.
!!
!! \param [out]    npair   number of paired parameters
!!
SUBROUTINE gpbmap(npair)
    USE mpbits

    INTEGER(mpi), DIMENSION(:), INTENT(OUT) :: npair

    INTEGER(mpl) :: l
    INTEGER(mpl) :: noffi
    INTEGER(mpi) :: i
    INTEGER(mpi) :: j
    INTEGER(mpi) :: m
    LOGICAL :: btest

    npair(1:n2)=0
    l=0

    DO i=1,n2
        noffi=INT(i-1,mpl)*INT(i-2,mpl)/2
        l=noffi/bs+i
        m=0
        DO j=1,i-1
            IF (btest(bitMap(l),m)) THEN
                npair(i)=npair(i)+1
                npair(j)=npair(j)+1
            END IF
            m=m+1
            IF (m >= bs) THEN
                l=l+1
                m=m-bs
            END IF
        END DO
    END DO

    RETURN
END SUBROUTINE gpbmap
