#!/usr/theBin/env python

"""
Contains the blobs calculation
"""

from ..collectAndCalcHelpers import DimensionsHelper, polAvg
from ..fields2D import CollectAndCalcFields2D
from ..radialFlux import getRadialFlux
from itertools import starmap
from multiprocessing import Pool
import numpy as np

#{{{CollectAndCalcBlobs
class CollectAndCalcBlobs(object):
    """
    Class for collecting and calcuating the blobs
    """

    #{{{constructor
    def __init__(self                ,\
                 collectPaths        ,\
                 slices              ,\
                 convertToPhysical   ,\
                 condition     = 3   ,\
                 pctPadding    = 400 ,\
                 useMultiProcess = True,\
                 ):
        #{{{docstring
        """
        This constructor will:
            * Set the member data

        Parameters
        ----------
        collectPaths : tuple
            Tuple from where to collect
        slices : tuple of tuples
            Tuple the indices to use.
            On the form (xInd, yInd, zInd, tSlice)
        convertToPhysical : bool
            Whether or not to convert to physical
        condition : float
            The condition in the conditional average will be set to
            flux.std()*condition
        pctPadding : float
            Padding around the maximum pulsewidth which satisfies the
            condition.
            Measured in percent.
        useMultiProcess : bool
            Whether or not to use sub process.
        """
        #}}}

        # Set the member data
        self._collectPaths      = collectPaths
        self._convertToPhysical = convertToPhysical
        self._condition         = condition
        self._pctPadding        = pctPadding
        self._useMultiProcess     = useMultiProcess
        self._xInd, self._yInd, self._zInd, self._tSlice = slices

        # Initialize the count
        self._blobCount = None
        self._holeCount = None

        self._notCalled = ["prepareCollectAndCalc"]
    #}}}

    #{{{prepareCollectAndCalc
    def prepareCollectAndCalc(self):
        #{{{docstring
        """
        Prepares the instance for collection.

        This function will:
            * Collect the density flux at the probe place.
            * Find the times where the fluxs meets the condition.
            * Collect the density fluctuations from the perpendicular 2D
              slice at the specified y-index (used to identify blobs and
              holes [negative perturbation propagating inwards]).
            * Set which indices are blobs and which are holes.
            * Set the window time.

        NOTE: The treshold condition is made in the flux as:
                1. One can have high perturbation as a consequence of
                   high azimuthal flux.
                2. The plasma can be alongated and spin in the azimuthal
                   direction.
        """
        #}}}

        if "prepareCollectAndCalc" in self._notCalled:
            self._notCalled.remove("prepareCollectAndCalc")
        else:
            print("The preparation has already been made")
            return

        # Collect flux
        self._radialFlux, self.uc = self._collectRadialFlux()
        self._dh = DimensionsHelper(self._collectPaths[0], self.uc)

        # Initialize
        key = list(self._radialFlux.keys())[0]
        flux = self._radialFlux[key]["nRadialFlux"]

        condition = flux.std()*self._condition
        time = self._radialFlux[key]["time"]
        self._dt = time[1] - time[0]

        # Get indices and window sizes
        self._indices = self._getIndicesMeetingCondition(flux, condition)
        windowSize = self._getWindowSize(self._indices, self._pctPadding)

        # Correct for the start of tSlice
        maxInd = len(time)-1 + self._tSlice.start
        self._tSlices =\
            self._transformContiguousIndicesToSlices(self._indices   ,\
                                                     windowSize,\
                                                     maxInd    ,\
                                                     )
        # Collect the bins
        self._perp2DBins = self._collect2DBins("n",self._tSlices,False,"perp")
        self._timeTraceBins, self._perp2DBinsFluct =\
                self._getTimeTraceBins(self._perp2DBins)

        # Sort into blobs and holes
        self._midIndex = int((self._tSlices[0].stop - self._tSlices[0].start)/2)
        self._blobsIndices, self._holesIndices =\
            self._identifyBlobsAndHoles(self._timeTraceBins, self._midIndex)

        # Make averages
        # +1 for symmetry
        self._windowTime = np.array(range(-windowSize, windowSize+1))*self._dt
    #}}}

    #{{{getCounts
    def getCounts(self):
        #{{{docstring
        """
        Returns the blob count and the holes count.

        Returns
        -------
        blobCount : int
            Number of blobs found
        holeCount : int
            Number of holes found
        """
        #}}}

        if self._blobCount is None:
            message = "prepareCollectAndCalc must be called prior to getCounts"
            raise RuntimeError(message)

        return self._blobCount, self._holeCount
    #}}}

    #{{{getRadialFlux
    def getRadialFlux(self):
        """
        Getter for the radial flux.
        """

        if "prepareCollectAndCalc" in self._notCalled:
            message = ("'prepareCollectAndCalc' must be called before"
                       "the execution")
            raise RuntimeError(message)

        return self._radialFlux
    #}}}

    #{{{getWaitingTimesAndPulseWidth
    def getWaitingTimesAndPulseWidth(self, type):
        #{{{docstring
        """
        Returns the waiting times and the pulse widths

        Parameters
        ----------
        type : ["blobs"|"holes"]
            Whether the waiting times and pulse widths for blobs or
            holes are to be returned.

        Returns
        -------
        waitingTimes : tuple
            Tuple of waiting times in time units.
        pulseWidths : tuple
            Tuple of pulse widths in time units.
        """
        #}}}

        if "prepareCollectAndCalc" in self._notCalled:
            message = ("'prepareCollectAndCalc' must be called before"
                       "the execution")
            raise RuntimeError(message)

        if type == "blobs":
            blobsIndices = []
            for i in self._blobsIndices:
                blobsIndices.append(self._indices[i])
            contiguousTimes = tuple(ind*self._dt for ind in blobsIndices)
        elif type == "holes":
            holesIndices = []
            for i in self._holesIndices:
                holesIndices.append(self._indices[i])
            contiguousTimes = tuple(ind*self._dt for ind in holesIndices)
        else:
            message =\
                "'type' expected 'blobs' or 'holes', but got '{}'".\
                format(type)
            raise ValueError(message)

        waitingTimes = []
        pulseWidths  = []
        for times in contiguousTimes:
            pulseWidths.append(times[-1]-times[0])
            mid = int(len(times)/2)
            if len(pulseWidths) == 1:
                # Initialize waiting times
                waitingStart = times[mid]
                continue

            waitingEnd = times[mid]
            waitingTimes.append(waitingEnd - waitingStart)
            waitingStart = waitingEnd.copy()

        waitingTimes = tuple(waitingTimes)
        pulseWidths  = tuple(pulseWidths)

        return waitingTimes, pulseWidths
    #}}}

    #{{{executeCollectAndCalc1D
    def executeCollectAndCalc1D(self):
        #{{{docstring
        """
        Collect and calcs the blobs and holes for the 1D time trace.

        Returns
        -------
        timeTraceBlobAvg : dict
            Dictionary of the averaged blob.
            Contains the keys "n", "time" and "pos".
        timeTraceBlobs : tuple
            Tuple containing the dictionaries used to calculate the
            averaged blob.
            Each element contains the same keys as timeTraceBlobAvg.
        timeTraceHolesAvg : dict
            Dictionary of the averaged hole.
            Contains the same keys as timeTraceBlobAvg.
        timeTraceHoles : tuple
            Tuple containing the dictionaries used to calculate the
            averaged hole.
            Each element contains the same keys as timeTraceBlobAvg.
        """
        #}}}

        if "prepareCollectAndCalc" in self._notCalled:
            message = ("'prepareCollectAndCalc' must be called before"
                       "the execution")
            raise RuntimeError(message)

        # Separate into holes and blobs
        timeTraceBlobs, timeTraceHoles =\
            self._extractBlobsAndHoles(self._timeTraceBins)

        timeTraceBlobAvg  = self._calcAverages("n", timeTraceBlobs)
        timeTraceHolesAvg = self._calcAverages("n", timeTraceHoles)

        return timeTraceBlobAvg ,\
               timeTraceBlobs   ,\
               timeTraceHolesAvg,\
               timeTraceHoles
    #}}}

    #{{{executeCollectAndCalc2D
    def executeCollectAndCalc2D(self, varName, mode, fluct, phiCont=False):
        #{{{docstring
        """
        Collect and calcs the blobs and holes for the in 2D.

        Parameters
        ----------
        varName : str
            Name of the variable to collect.
        mode : ["perp"|"par"|"pol"]
            Mode to use for 2D collection.
        fluct : bool
            Wheter or not the variables shold be fluctuating or not.
        phiCont : bool
            If True, phi will also be collected.

        Returns
        -------
        blobs2DAvg : dict
            Dictionary of the averaged blob.
            Contains the keys:
                * varName    - The 2D variable.
                * varNamePPi - The 2D variable pi away from the set zInd
                               (only when mode is "par").
                * "phi"      - The 2D variable (only when phiCont is True).
                * "phiPPi"   - The 2D variable pi away from the set zInd
                               (only when mode is "par" and phiCont is True).
                * "time"     - The corresponding time.
                * "X"        - The X-mesh.
                * "Y"        - The Y-mesh.
                * pos    - The position of the fixed index
        blobs2D : tuple
            Tuple containing the dictionaries used to calculate the
            averaged blob.
            Each element contains the same keys as blobs2DAvg.
        holes2DAvg : dict
            Dictionary of the averaged hole.
            Contains the same keys as blobs2DAvg.
        holes2D : tuple
            Tuple containing the dictionaries used to calculate the
            averaged blob.
            Each element contains the same keys as blobs2DAvg.
        """
        #}}}

        if "prepareCollectAndCalc" in self._notCalled:
            message = ("'prepareCollectAndCalc' must be called before"
                       "the execution")
            raise RuntimeError(message)

        if phiCont:
            # Collect phi
            phiBins2D = self._collect2DBins("phi", self._tSlices, fluct, mode)
            phiBlobs2D, phiHoles2D = self._extractBlobsAndHoles(phiBins2D)

        if varName == "n" and mode != "perp":
            bins2D = self._collect2DBins(varName, self._tSlices, fluct, mode)
        else:
            if fluct:
                # Cast to 3D from 4D
                self._perp2DBinsFluct = list(self._perp2DBinsFluct)
                for i in range(len(self._perp2DBinsFluct)):
                    self._perp2DBinsFluct[i]["n"] = self._perp2DBinsFluct[i]["n"][:,:,0,:]
                self._perp2DBinsFluct = tuple(self._perp2DBinsFluct)
                bins2D = self._perp2DBinsFluct
            else:
                bins2D = self._perp2DBins

        blobs2D, holes2D = self._extractBlobsAndHoles(bins2D)

        blobs2DAvg = self._calcAverages(varName, blobs2D)
        holes2DAvg = self._calcAverages(varName, holes2D)

        if phiCont:
            phiBlobs2DAvg = self._calcAverages("phi", phiBlobs2D)
            blobs2DAvg.update(phiBlobs2DAvg)
            phiHoles2DAvg = self._calcAverages("phi", phiHoles2D)
            holes2DAvg.update(phiHoles2DAvg)

        return blobs2DAvg, blobs2D, holes2DAvg, holes2D
    #}}}

    #{{{_collectRadialFlux
    def _collectRadialFlux(self):
        #{{{docstring
        """
        Collects the radial flux in the probe point

        Returns
        -------
        radialFlux : dict
            Dictionary where the keys are on the form "rho,theta,z".
            The value is a dict containing of
            {varName:radialFlux, "time":time, "timeIndices":timeIndices}
        uc : UnitsConverter
            The UnitsConverter object.
        """
        #}}}
        varName = "n"
        mode    = "fluct"

        indicesArgs   = (self._xInd, self._yInd, self._zInd)
        indicesKwargs = {"tSlice"          : self._tSlice,\
                         "nPoints"         : 1           ,\
                         }

        radialFlux, uc = getRadialFlux(self._collectPaths     ,\
                                       varName                ,\
                                       self._convertToPhysical,\
                                       mode                   ,\
                                       indicesArgs            ,\
                                       indicesKwargs          ,\
                                      )

        return radialFlux, uc
    #}}}

    #{{{_getIndicesMeetingCondition
    def _getIndicesMeetingCondition(self, var, condition):
        #{{{docstring
        """
        Returns indices where the condition is meet.

        The indices are corrected for the tSlice.start.

        Parameters
        ----------
        var : array-1d
            Array of to find where the condition is meet.
        condition : float
            The condition to check for.

        Returns
        -------
        contiguousIndices : tuple
            Tuple of arrays, where each element in the tuple is a series
            of indices, contiguous, in ascending order where the
            condition is meet.
        """
        #}}}

        # Get indices where the values are above the conditions
        indicesMeetingCond = np.where(var >= condition)[0]

        # Get contiguous indices
        contiguousIndices = []
        while len(indicesMeetingCond) !=0:
            # -1 in order not to get out of index on last point
            for i in range(len(indicesMeetingCond)-1):
                if indicesMeetingCond[i]+1 != indicesMeetingCond[i+1]:
                    break
            contiguous = indicesMeetingCond[0:i+1]
            indicesMeetingCond = indicesMeetingCond[i+1:]
            contiguousIndices.append(contiguous)

        # As i ran to len(indicesMeetingCond)-1, we make a special treatment on
        # the last index
        contiguousIndices[-2] =\
            np.append(contiguousIndices[-2], contiguousIndices[-1][0])
        contiguousIndices = contiguousIndices[:-1]

        # Correct for tSlices.start
        for i in range(len(contiguousIndices)):
            contiguousIndices[i] += self._tSlice.start

        contiguousIndices = tuple(contiguousIndices)

        return contiguousIndices
    #}}}

    #{{{_getWindowSize
    def _getWindowSize(self, contiguousIndices, pctPadding):
        #{{{docstring
        """
        Get the window size which will define the size of one theBin.

        Parameters
        ----------
        contiguousIndices : tuple
            Tuple of arrays, where each element in the tuple is a series
            of indices, contiguous, in ascending order where the
            condition is meet.
        pctPadding : float
            Padding (in percent) which will be added to the max length
            of the contiguousIndices

        Returns
        -------
        windowSize : int
            Number of indices to defining the size of one theBin.
        """
        #}}}

        maxLen = 0
        for indices in contiguousIndices:
            maxLen = len(indices) if len(indices) > maxLen else maxLen
        windowSize = int(maxLen*(1+(pctPadding/100)))

        return windowSize
    #}}}

    #{{{_transformContiguousIndicesToSlices
    def _transformContiguousIndicesToSlices(self,\
                                            contiguousIndices,\
                                            windowSize,\
                                            maxInd,\
                                            ):
        #{{{docstring
        """
        Transforms the contiguous indices to tSlices.

        Parameters
        ----------
        contiguousIndices : tuple
            Tuple of arrays, where each element in the tuple is a series
            of indices, contiguous, in ascending order where the
            condition is meet.
        windowSize : int
            Number of indices to defining the size of one theBin.
        maxInd : int
            Max index in time.

        Returns
        -------
        tSlices : tuple
            Tuple of time slices, where the individual slice is the slice
            which will be used to collect a theBin.
        """
        #}}}

        tSlices = []
        for indices in contiguousIndices:
            # Find the mid of the indices
            mid = int(len(indices)/2)
            # NOTE: boutdata.collect includes the last point, whereas
            #       the slice does not.
            #       When this slice is used for collecting in
            #       boutdata.collect, the last point will be included so
            #       that the window would be symmetric
            curSlice =\
                slice(indices[mid]-windowSize, indices[mid]+windowSize)
            # Guard for the beginning
            if curSlice.start >= 0:
                # Guard for the end
                if curSlice.stop <= maxInd:
                    tSlices.append(curSlice)

        tSlices = tuple(tSlices)

        return tSlices
    #}}}

    #{{{_collect2DBins
    def _collect2DBins(self, varName, tSlices, fluct, mode):
        #{{{docstring
        """
        Collects the bins which will be used in the average.

        Parameters
        ----------
        varName : str
            Name of the variable to collect.
        tSlices : tuple
            Tuple of time slices, where the individual slice is the slice
            which will be used to collect a theBin.
        fluct : bool
            Whether or not to collect the fluctuations only.
        mode : ["perp"|"par"|"pol"]
            Type of 2D calculation.

        Returns
        -------
        tupleOfBins2D : tuple
            A tuple of the 2D bins stored as dicts with the
            keys:
                * varName    - A 3d array (a 2d spatial array of each time)
                               of the collected variable.
                * varNamePPi - The field at pi away from the varName field
                               (only if "type" == "par")
                * "X"        - The cartesian x mesh to the field
                * "Y"        - The cartesian Y mesh to the field
                * "time"     - The time trace
                * pos        - The position of the fixed index
        """
        #}}}

        args = tuple((varName, tSlice, fluct, mode) for tSlice in tSlices)
        if self._useMultiProcess:
            # Set a max of 10 processors in order not to saturate the memory
            with Pool(10) as p:
                # Here using Pool.starmap
                tupleOfBins2D = tuple(p.starmap(self._collect2DBin, args))
        else:
            # Here using itertools.starmap
            tupleOfBins2D = tuple(starmap(self._collect2DBin, args))

        return tupleOfBins2D
    #}}}

    #{{{_collect2DBin
    def _collect2DBin(self, varName, tSlice, fluct, mode):
        #{{{docstring
        """
        Collects the bins which will be used in the average.

        Parameters
        ----------
        varName : str
            Name of the variable to collect.
        tSlices : tuple
            Tuple of time slices, where the individual slice is the slice
            which will be used to collect a theBin.
        fluct : bool
            Whether or not to collect the fluctuations only.
        mode : ["perp"|"par"|"pol"]
            Type of 2D calculation.

        Returns
        -------
        theBin : dict
            A dict with the keys:
                * varName    - A 3d array (a 2d spatial array of each time)
                               of the collected variable.
                * varNamePPi - The field at pi away from the varName field
                               (only if "type" == "par")
                * "X"        - The cartesian x mesh to the field
                * "Y"        - The cartesian Y mesh to the field
                * "time"     - The time trace
                * pos        - The position of the fixed index
        """
        #}}}

        xSlice            = None
        ySlice            = None
        zSlice            = None
        xInd              = self._xInd
        yInd              = self._yInd
        zInd              = self._zInd

        convertToPhysical = self._convertToPhysical

        # Pependicular collection
        ccf2D = CollectAndCalcFields2D(\
                    self._collectPaths        ,\
                    fluct             = fluct ,\
                    mode              = mode  ,\
                    convertToPhysical = convertToPhysical)

        if mode == "perp":
            ccf2D.setSlice(xSlice, yInd, zSlice, tSlice)
        elif mode == "par":
            ccf2D.setSlice(xSlice, ySlice, zInd, tSlice)
        elif mode == "pol":
            ccf2D.setSlice(xInd, ySlice, zSlice, tSlice)
        else:
            message =\
                "'mode' expected 'perp', 'par' or 'pol', but got '{}'".\
                format(mode)
            raise ValueError(message)

        ccf2D.setVarName(varName)
        theBin = ccf2D.executeCollectAndCalc()

        return theBin
    #}}}

    #{{{_getTimeTraceBins
    def _getTimeTraceBins(self, perp2DBins):
        #{{{docstring
        """
        Get the time trace bins from perp2DBins

        Parameters
        ----------
        perp2DBins : tuple
            A tuple of the perpendicular 2D bins stored as dicts with
            the keys:
                * "n"    - A 3d array (a 2d spatial array of each time)
                           of the collected variable.
                * "X"    - The cartesian x mesh to the field
                * "Y"    - The cartesian Y mesh to the field
                * "time" - The time trace
                * pos    - The position of the fixed index

        Returns
        -------
        timeTraceBins : tuple
            A tuple of the time traces, stored as dicts with the keys:
                * "n"    - A 3d array (a 2d spatial array of each time)
                           of the collected variable.
                * "time" - The time trace
                * "pos"  - Tuple of the (rho, theta, z) fixed positions.
        perp2DBinFluct : tuple
            A by-product of the process.
            A tuple of the 2D bins stored as dicts with the
            keys:
                * "n"    - A 3d array (a 2d spatial array of each time)
                           of the collected variable.
                * "X"    - The cartesian x mesh to the field
                * "Y"    - The cartesian Y mesh to the field
                * "time" - The time trace
                * pos    - The position of the fixed index
        """
        #}}}

        timeTraceBins = []
        perp2DBinFluct = []
        rhoPos   = self._dh.rho     [self._xInd]
        thetaPos = self._dh.thetaRad[self._yInd]
        for perp2DBin in perp2DBins:
            curDict         = {}
            # Must manually take the poloidal average
            var = np.expand_dims(perp2DBin["n"], axis=2)
            fluct = var - polAvg(var)
            # Add to perp2DBinFluct
            fluctDict = perp2DBin.copy()
            fluctDict["n"] = fluct
            perp2DBinFluct.append(fluctDict)

            # Store to dict
            curDict["n"]    = fluct[:, self._xInd, 0, self._zInd]
            curDict["time"] = perp2DBin["time"]
            curDict["pos"]  = (rhoPos, thetaPos, perp2DBin["zPos"])
            timeTraceBins.append(curDict)

        perp2DBinFluct = tuple(perp2DBinFluct)
        return timeTraceBins, perp2DBinFluct
    #}}}

    #{{{_identifyBlobsAndHoles
    def _identifyBlobsAndHoles(self, timeTraceBins, midIndex):
        #{{{docstring
        """
        Identifies whether the theBin contains a blob or a hole.

        Sets the blobCount and holeCount.

        An outward transportation of positive fluctuations is a positive
        flux.
        A negative transportation of a negative fluctuation is also a
        positive flux.

        Parameters
        ----------
        timeTraceBins : tuple
            A tuple of the time traces, stored as dicts with the keys:
                * "n"    - A 3d array (a 2d spatial array of each time)
                           of the collected variable.
                * "time" - The time trace
                * "pos"  - Tuple of the (rho, theta, z) fixed positions.
        midIndex : int
            Index of the mid of the time trace.

        Returns
        -------
        blobsIndices : tuple
            Tuple containing the indices identified as blobs
        holesIndices : tuple
            Tuple containing the indices identified as holes
        """
        #}}}

        blobsIndices  = []
        holesIndices = []
        for nr, timeTrace in enumerate(timeTraceBins):
            curDens = timeTrace["n"]
            if curDens[midIndex] >= 0:
                blobsIndices.append(nr)
            else:
                holesIndices.append(nr)

        blobsIndices = tuple(blobsIndices)
        holesIndices = tuple(holesIndices)

        # Set the counts
        self._blobCount = len(blobsIndices)
        self._holeCount = len(holesIndices)

        return blobsIndices, holesIndices
    #}}}

    #{{{_extractBlobsAndHoles
    def _extractBlobsAndHoles(self, bins):
        #{{{docstring
        """
        Extracts blobs and holes from a tuple of bins.

        Parameters
        ----------
        bins : tuple
            Bins to be separated.

        Returns
        -------
        blobs : tuple
            Tuple of the bins which are blobs.
        holes : tuple
            Tuple of the bins which are holes.
        """
        #}}}

        blobs = []
        holes = []

        for i in self._blobsIndices:
            blobs.append(bins[i])
        for i in self._holesIndices:
            holes.append(bins[i])

        return tuple(blobs), tuple(holes)
    #}}}

    #{{{_calcAverages
    def _calcAverages(self, varName, tupleOfDictsWithBins):
        #{{{docstring
        """
        Returns a tuple of dict where varname and "time" in the dicts has
        been replaced with averaged values.

        Parameters
        ----------
        varName : str
            The name of the variable.
        tupleOfDictsWithBins : tuple
            Tuple of dicts, where each dict contains the keys varName and
            "time".

        Returns
        -------
        binAverageDict : tuple
            Dict where the bins have been averaged.
        """
        #}}}

        # Guard if tupleOfDictsWithBins is empty (i.e. either no holes
        # or no blobs)
        if len(tupleOfDictsWithBins) == 0:
            return {}

        binAverageDict = tupleOfDictsWithBins[0].copy()
        sumN = np.zeros(tupleOfDictsWithBins[0][varName].shape)
        for curDict in tupleOfDictsWithBins:
            sumN += curDict[varName]

        binAverageDict[varName] = sumN/len(tupleOfDictsWithBins)
        binAverageDict["time"]  = self._windowTime

        return binAverageDict
    #}}}
#}}}
