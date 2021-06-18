#!/usr/bin/env python

"""
Contains single driver and driver class for the probability density functions
"""

from ..driverHelpers import onlyScan
from .collectAndCalcPDF import CollectAndCalcPDF
from ..superClasses import DriverPointsSuperClass
from .plotPDF import PlotPDF
from scipy import stats
from multiprocessing import Process
import os, pickle

#{{{driverPDF
def driverPDF(collectPaths     ,\
              varName          ,\
              convertToPhysical,\
              mode             ,\
              indicesArgs      ,\
              indicesKwargs    ,\
              plotSuperKwargs  ,\
             ):
    #{{{docstring
    """
    Driver for plotting probability density functions.
    Pickles the PDFStats to the desitnation folder.

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

    PDF, uc, PDFStats = getPDF(collectPaths      ,\
                               varName           ,\
                               convertToPhysical ,\
                               mode              ,\
                               indicesArgs       ,\
                               indicesKwargs     ,\
                               returnStats = True,\
                              )

    # FIXME: The saving of the PDFStats is a ugly hack for now
    root = collectPaths[0].split("/")[0]
    if convertToPhysical:
        path = os.path.join(root, "visualizationPhysical")
    else:
        path = os.path.join(root, "visualizationNormalized")

    scanPath = onlyScan(plotSuperKwargs["dmp_folders"],\
                        plotSuperKwargs["scanParameter"])

    path = os.path.join(path, scanPath, "PDFs")

    if not(os.path.exists(path)):
        os.makedirs(path)

    fileName = os.path.join(path,"PDFStats.pickle")
    with open(fileName, "wb") as f:
        pickle.dump(PDFStats, f, pickle.HIGHEST_PROTOCOL)
        print("Pickled PDFStats to {}".format(fileName))

    # Plot
    pPDF = PlotPDF(uc ,\
                   **plotSuperKwargs)
    pPDF.setData(PDF, mode)
    pPDF.plotSaveShowPDF()
#}}}

#{{{getPDF
def getPDF(collectPaths       ,\
           varName            ,\
           convertToPhysical  ,\
           mode               ,\
           indicesArgs        ,\
           indicesKwargs      ,\
           returnStats = False,\
           ):
    #{{{docstring
    """
    Obtains the probability density functions.

    Parameters
    ----------
    returnStats : bool
        Wheter or not to return PDFStats.
    See driverPDF for details about the other parameters.

    Returns
    -------
    PDF : dict
        Dictionary where the keys are on the form "rho,theta,z".
        The value is a dict containing of
        {"pdfX":pdfX, "pdfY":"pdfY"}
    uc : UnitsConverter
        The units converter
    PDFStats : dict
        Only returned if returnStats is True
        Dictionary where the keys are on the form "rho,theta,z".
        The value is a dict containing of
        {"skew":skewness, "kurtExcess":excessKurtosis}
    """
    #}}}

    # Create collect object
    ccPDF = CollectAndCalcPDF(collectPaths       ,\
            mode              = mode             ,\
            convertToPhysical = convertToPhysical,\
            )

    # Set the slice
    ccPDF.setIndices(*indicesArgs, **indicesKwargs)

    # Set name
    ccPDF.setVarName(varName)

    # Execute the collection
    tt = ccPDF.executeCollectAndCalc()
    tt = ccPDF.convertTo1D(tt)

    # Calculate the PDF
    PDF = ccPDF.calcPDF(tt)

    if returnStats:
        # Calculate the skewness and kurtosis
        PDFStats = {}
        for key in tt.keys():
            PDFStats[key] = {"skew":stats.skew(tt[key][varName]),\
                             "kurtExcess":stats.kurtosis(tt[key][varName])}

        return PDF, ccPDF.uc, PDFStats
    else:
        return PDF, ccPDF.uc
#}}}

#{{{DriverPDF
class DriverPDF(DriverPointsSuperClass):
    """
    Class for driving of the plotting of the probability density functions.
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
        plotSuperKwargs.update({"plotType"   :"PDFs"})
        self._plotSuperKwargs = plotSuperKwargs
    #}}}

    #{{{driverPDF
    def driverPDF(self):
        #{{{docstring
        """
        Wrapper to driverPDF
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
            processes = Process(target = driverPDF, args = args)
            processes.start()
        else:
            driverPDF(*args)
    #}}}
#}}}
