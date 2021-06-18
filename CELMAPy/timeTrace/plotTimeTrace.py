#!/usr/bin/env python

"""Class for timeTrace plot"""

from ..superClasses import PlotSuperClass
from ..plotHelpers import plotNumberFormatter, seqCMap3
import numpy as np
import matplotlib.pyplot as plt
import os

#{{{PlotTimeTrace
class PlotTimeTrace(PlotSuperClass):
    """
    Class which contains the time trace data and the plotting configuration.
    """

    #{{{constructor
    def __init__(self, *args, pltSize = (15,10), **kwargs):
        #{{{docstring
        """
        This constructor:

        * Calls the parent constructor

        Parameters
        ----------
        pltSize : tuple
            The size of the plot
        """
        #}}}

        # Call the constructor of the parent class
        super().__init__(*args, **kwargs)

        # Set the plot size
        self._pltSize = pltSize
    #}}}

    #{{{setData
    def setData(self, timeTraces, mode, timeAx=True):
        #{{{docstring
        """
        Sets the time traces to be plotted.

        This function also sets the variable labels, colors and the save name.

        Parameters
        ----------
        timeTraces : dict
            Dictionary where the keys are on the form "rho,theta,z".
            The value is a dict containing of
            {varName:timeTrace, "time":time}
        mode : ["normal"|"fluct"]
            What mode the input is given in.
        timeAx : bool
            Whether or not the time should be on the x axis
        """
        #}}}

        self._timeAx = timeAx

        # Set the member data
        self._timeTraces = timeTraces
        self._mode = mode

        # Obtain the varname
        ind  = tuple(timeTraces.keys())[0]
        keys = timeTraces[ind].keys()
        self._varName = tuple(var for var in keys if var != "time")[0]

        # Obtain the color (pad away brigthest colors)
        pad = 3
        self._colors = seqCMap3(np.linspace(0, 1, len(timeTraces.keys())+pad))

        self._prepareLabels()

        # Set the var label
        pltVarName = self._ph.getVarPltName(self._varName)

        self._varLabel = self._varLabelTemplate.\
            format(pltVarName, **self.uc.conversionDict[self._varName])

        # Set the fileName
        self._fileName =\
            os.path.join(self._savePath,\
                "{}-{}-{}".format(self._varName, "timeTraces", self._fluctName))

        if not(timeAx):
            self._fileName += "Indices"
        if (self._sliced):
            self._fileName += "Sliced"

        if self._extension is None:
            self._extension = "png"

        self._fileName = "{}.{}".format(self._fileName, self._extension)
    #}}}

    #{{{_prepareLabels
    def _prepareLabels(self):
        """
        Prepares the labels for plotting.
        """

        # Set var label template
        if self.uc.convertToPhysical:
            unitsOrNormalization = " $[{units}]$"
        else:
            unitsOrNormalization = "${normalization}$"
        if self._mode == "normal":
            self._varLabelTemplate = r"${{}}${}".format(unitsOrNormalization)
            self._fluctName = ""
        elif self._mode == "fluct":
            self._varLabelTemplate = r"$\widetilde{{{{{{}}}}}}${}".\
                    format(unitsOrNormalization)
            self._fluctName = "fluct"
        else:
            message = "'{}'-mode not implemented.".format(self._mode)
            raise NotImplementedError(message)

        # Set the time label
        if self._timeAx:
            self._timeLabel = self._ph.tTxtDict["tTxtLabel"]
        else:
            self._timeLabel = "$\mathrm{Time}$ $\mathrm{index}$"
    #}}}

    #{{{plotSaveShowTimeTrace
    def plotSaveShowTimeTrace(self):
        """
        Performs the actual plotting.
        """

        # Create the plot
        fig = plt.figure(figsize = self._pltSize)
        ax  = fig.add_subplot(111)

        keys = sorted(self._timeTraces.keys())

        for key, color in zip(keys, self._colors):
            # Make the label
            rho, theta, z = key.split(",")

            # Set values
            self._ph.rhoTxtDict  ["value"] =\
                    plotNumberFormatter(float(rho), None)
            self._ph.zTxtDict    ["value"] =\
                    plotNumberFormatter(float(z), None)
            self._ph.thetaTxtDict["value"] =\
                    plotNumberFormatter(float(theta), None)

            # Make the const values
            label = (r"{}$,$ {}$,$ {}").\
                    format(\
                        self._ph.rhoTxtDict  ["constRhoTxt"].\
                            format(self._ph.rhoTxtDict),\
                        self._ph.thetaTxtDict["constThetaTxt"].\
                            format(self._ph.thetaTxtDict),\
                        self._ph.zTxtDict["constZTxt"].\
                            format(self._ph.zTxtDict),\
                          )

            if self._timeAx:
                ax.plot(self._timeTraces[key]["time"],\
                        self._timeTraces[key][self._varName],\
                        color=color, label=label)
            else:
                ax.plot(\
                        self._timeTraces[key][self._varName],\
                        color=color, label=label)

        # Set axis labels
        ax.set_xlabel(self._timeLabel)
        ax.set_ylabel(self._varLabel)

        # Make the plot look nice
        self._ph.makePlotPretty(ax, rotation = 45)

        if self._showPlot:
            plt.show()

        if self._savePlot:
            self._ph.savePlot(fig, self._fileName)

        plt.close(fig)
    #}}}
#}}}
