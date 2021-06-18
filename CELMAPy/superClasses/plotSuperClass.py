#!/usr/bin/env python

"""
Contains the super class for the plotting
"""

from ..driverHelpers import scanWTagSaveFunc, onlyScan, getTime
from ..plotHelpers import PlotHelper
import os

#{{{PlotSuperClass
class PlotSuperClass(object):
    """
    The parent plotting class

    * Sets common member data.
    * Sets the save path.
    """

    #{{{Static member
    _time = ""
    #}}}

    #{{{Constructor
    def __init__(self                   ,\
                 uc                     ,\
                 showPlot        = False,\
                 savePlot        = True ,\
                 savePath        = None ,\
                 savePathFunc    = None ,\
                 extension       = None ,\
                 dmp_folders     = None ,\
                 timeStampFolder = True ,\
                 plotType        = ""   ,\
                 sliced          = False,\
                 **kwargs):
        #{{{docstring
        """
        This constructor sets the memberdata, and sets the savePath and
        creates the folders.

        Parameters
        ----------
        uc : UnitsConverter
            The units converter which makes the plot helper.
        showPlot : bool
            If the plot should be displayed.
        savePlot : bool
            If plot should be saved.
        savePath : str
            Name of the folder to save the plots in.
        savePathFunc : str
            Name of an implemented function which returns the name of
            the folder to save plots.
        extension : [None|str]
            Overrides default extension if set. Excludes the "."
        scanParameters : [None|sequence (not string)]
            Sequence of parameters changed in the scan. If this is not None,
            calls to convertToCurrentScanParameters will be triggered in
            the child classes.
        dmp_folders: [None|tuple]
            Needed if savePaths should be made automatically
        plotType : str
            Name of folder containing the plot type.
            No folder will be made if empty.
        timeStampFolder : bool
            Whether or not to timestamp the folder
        sliced : bool
            Whether or not the data is sliced
        **kwargs : keyword arguments
            Additional keyword arguments given as input to savePathFunc.
        """
        #}}}
        # Set the member data
        self._showPlot   = showPlot
        self._savePlot   = savePlot
        self._savePath   = savePath
        self._extension  = extension
        self._sliced     = sliced
        self.uc          = uc

        if dmp_folders is not None:
            # Get the firs dmp_folder (will be used to create the savepath)
            dmp_folder = dmp_folders[0]

            # Set the savePath
            if savePathFunc is not None:
                # FIXME: Check if it is possible to change the API here.
                #        Would be nice if could send in a function instead.
                if savePathFunc == "scanWTagSaveFunc":
                    savePath = scanWTagSaveFunc(dmp_folder, **kwargs)
                elif savePathFunc == "onlyScan":
                    savePath = onlyScan(dmp_folder, **kwargs)
                else:
                    message  = "{0}Warning: savePathFunc '{1}' not found, "
                    message += "falling back to standard implementation{0}"
                    print(message.format("\n"*3, savePathFunc))
                    savePath = "-".join(dmp_folder.split("/")[::-1])
            else:
                if savePath is None:
                    savePath = "-".join(dmp_folder.split("/")[::-1])

            if timeStampFolder:
                if PlotSuperClass._time == "":
                    # Get the timefolder
                    PlotSuperClass._time = getTime()

            # Create the savepath (based on the first dmp_folder string)
            visualizationType =\
                    "Physical" if uc.convertToPhysical else "Normalized"
            saveDirs = (os.path.normpath(dmp_folder).split(os.sep)[0],\
                        "visualization{}".format(visualizationType),\
                        savePath,\
                        plotType,\
                        PlotSuperClass._time)

            self._savePath = ""
            for saveDir in saveDirs:
                self._savePath = os.path.join(self._savePath, saveDir)
        else:
            if savePath is None:
                message = ("Don't know what to set self._savePath to as "
                           "both savePath and dmp_folders ar None")
                raise ValueError(message)

            self._savePath = savePath

        # Make dir if not exists
        if not os.path.exists(self._savePath):
            os.makedirs(self._savePath)

        # Make the plot helper
        self._ph = PlotHelper(uc.convertToPhysical)
        self._ph.makeDimensionStringsDicts(uc)
    #}}}

    #{{{getSavePath
    def getSavePath(self):
        #{{{docstring
        """
        Returns the save path
        """
        #}}}

        return self._savePath
    #}}}
#}}}
