#!/usr/bin/env python

"""
Contains single driver and driver class for the time traces
"""

from ..superClasses import DriverPointsSuperClass
from .collectAndCalcTimeTrace import CollectAndCalcTimeTrace
from .plotTimeTrace import PlotTimeTrace
from multiprocessing import Process

#{{{driverTimeTrace
def driverTimeTrace(collectPaths     ,\
                    varName          ,\
                    convertToPhysical,\
                    mode             ,\
                    indicesArgs      ,\
                    indicesKwargs    ,\
                    plotSuperKwargs  ,\
                    ):
    #{{{docstring
    """
    Driver for plotting time traces.

    Parameters
    ----------
    collectPaths : tuple
        Paths to collect from.
        The corresponind 't_array' of the paths must be in ascending order.
    varName : str
        The variable name which will be used.
    convertToPhysical : bool
        Whether or not to convert to physical units.
    mode : ["normal"|"fluct"]
        If mode is "normal" the raw data is given as an output.
        If mode is "fluct" the fluctuations are given as an output.
    indicesArgs : tuple
        Contains xInd, yInd and zInd.
        See CollectAndCalcPointsSuperClass.setIndices for details.
    indicesKwargs : dict
        Contains tslice, nPoints, equallySpace and steadyStatePath.
        See CollectAndCalcPointsSuperClass.setIndices for details.
    plotSuperKwargs : dict
        Keyword arguments for the plot super class.
    """
    #}}}

    tt, uc = getTimeTrace(collectPaths     ,\
                          varName          ,\
                          convertToPhysical,\
                          mode             ,\
                          indicesArgs      ,\
                          indicesKwargs    ,\
                         )

    # Plot
    ptt = PlotTimeTrace(uc              ,\
                        **plotSuperKwargs)
    ptt.setData(tt, mode)
    ptt.plotSaveShowTimeTrace()
#}}}

#{{{getTimeTrace
def getTimeTrace(collectPaths     ,\
                 varName          ,\
                 convertToPhysical,\
                 mode             ,\
                 indicesArgs      ,\
                 indicesKwargs    ,\
                ):
    #{{{docstring
    """
    Obtains the time traces.

    Parameters
    ----------
    See driverTimeTrace for details.

    Returns
    -------
    tt : dict
        Dictionary where the keys are on the form "rho,theta,z".
        The value is a dict containing of
        {varName:timeTrace, "time":time}
    uc : UnitsConverter
        The units converter
    """
    #}}}
    # Create collect object
    cctt = CollectAndCalcTimeTrace(collectPaths                         ,\
                                   mode              = mode             ,\
                                   convertToPhysical = convertToPhysical,\
                                   )

    # Set the slice
    cctt.setIndices(*indicesArgs, **indicesKwargs)

    # Set name
    cctt.setVarName(varName)

    # Execute the collection
    tt = cctt.executeCollectAndCalc()
    tt = cctt.convertTo1D(tt)

    return tt, cctt.uc
#}}}

#{{{DriverTimeTrace
class DriverTimeTrace(DriverPointsSuperClass):
    """
    Class for driving of the plotting of the time traces.
    """

    #{{{Constructor
    def __init__(self                       ,\
                 dmp_folders                ,\
                 indicesArgs                ,\
                 indicesKwargs              ,\
                 plotSuperKwargs            ,\
                 varName           = "n"    ,\
                 mode              = "fluct",\
                 **kwargs):
        #{{{docstring
        """
        This constructor:
            * Calls the parent class
            * Set the member data
            * Updates the plotSuperKwargs

        Parameters
        ----------
        dmp_folders : tuple
            Tuple of the dmp_folder (output from bout_runners).
        indicesArgs : tuple
            Contains xInd, yInd and zInd.
            See CollectAndCalcPointsSuperClass.setIndices for details.
        indicesKwargs : dict
            Contains tslice, nPoints, equallySpace and steadyStatePath.
            See CollectAndCalcPointsSuperClass.setIndices for details.
        plotSuperKwargs : dict
            Keyword arguments for the plot super class.
        varName : str
            Name of variable to collect and plot
        mode : ["normal"|"fluct"]
            If mode is "normal" the raw data is given as an output.
            If mode is "fluct" the fluctuations are given as an output.
        **kwargs : keyword arguments
            See parent class for details.
        """
        #}}}

        # Call the constructor of the parent class
        super().__init__(dmp_folders, **kwargs)

        # Set the member data
        self._varName       = varName
        self._mode          = mode
        self._indicesArgs   = indicesArgs
        self._indicesKwargs = indicesKwargs

        # Update the plotSuperKwargs dict
        plotSuperKwargs.update({"dmp_folders":dmp_folders})
        plotSuperKwargs.update({"plotType"   :"timeTraces"})
        self._plotSuperKwargs = plotSuperKwargs
    #}}}

    #{{{driverTimeTrace
    def driverTimeTrace(self):
        #{{{docstring
        """
        Wrapper to driverTimeTrace
        """
        #}}}
        args =  (\
                 self._collectPaths    ,\
                 self._varName         ,\
                 self.convertToPhysical,\
                 self._mode            ,\
                 self._indicesArgs     ,\
                 self._indicesKwargs   ,\
                 self._plotSuperKwargs ,\
                )
        if self._useMultiProcess:
            processes = Process(target = driverTimeTrace, args = args)
            processes.start()
        else:
            driverTimeTrace(*args)
    #}}}
#}}}
