#!/usr/bin/env python

"""Post-processor for fields1D animation"""

import os, sys
# If we add to sys.path, then it must be an absolute path
commonDir = os.path.abspath("./../common")
# Sys path is a list of system paths
sys.path.append(commonDir)

from CELMAPy.fields1D import Driver1DFields

#{{{fields1DAnimation
def fields1DAnimation(dmp_folders, collectPaths, plotSuperKwargs,\
                      hyperIncluded=False, boussinesq=False, tSlice=None,
                      yInd = 16, useMultiProcess = True):
    #{{{docstring
    """
    Runs the standard fields1D animation

    Parameters
    ----------
    dmp_folders : tuple
        Tuple of the dmp_folders.
    collectPaths : tuple
        Tuple of the paths to collect from.
    plotSuperKwargs : dict
        Keyword arguments for the plot super class.
    hyperIncluded : bool
        If hyper viscosities are used.
    boussinesq : bool
        Whether or not the boussinesq approximation is used
    tSlice : [None|Slice]
        Temporal slice
    yInd : int
        Default is 16
    useMultiProcess : bool
        If useMultiProcess should be used
    """
    #}}}

    convertToPhysical = True

    xSlice = None
    ySlice = None
    zSlice = None
    xInd = 0
    yInd = yInd
    zInd = 0
    guardSlicesAndIndicesKwargs = {\
                                   "xguards" : False ,\
                                   "yguards" : False ,\
                                   "xSlice"  : xSlice,\
                                   "ySlice"  : ySlice,\
                                   "zSlice"  : zSlice,\
                                   "tSlice"  : tSlice,\
                                   "xInd"    : xInd  ,\
                                   "yInd"    : yInd  ,\
                                   "zInd"    : zInd  ,\
                                  }

    d1DF = Driver1DFields(\
                   # Driver1DFields
                   dmp_folders                    ,\
                   plotSuperKwargs                ,\
                   guardSlicesAndIndicesKwargs    ,\
                   boussinesq      = boussinesq   ,\
                   hyperIncluded   = hyperIncluded,\
                   # DriverPlotFieldsSuperClass
                   convertToPhysical = convertToPhysical,\
                   # DriverSuperClass
                   collectPaths  = collectPaths ,\
                   useMultiProcess = useMultiProcess,\
                  )

    d1DF.driver1DFieldsAll()
#}}}
