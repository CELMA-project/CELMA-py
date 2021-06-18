#!/usr/bin/env python

"""
Contains super classes for animations plots
"""

from ..plotHelpers import (plotNumberFormatter,\
                           seqCMap,\
                           seqCMap3,\
                           divCMap)
from ..plotHelpers import PlotHelper, getMaxMinAnimation, SizeMaker
from .plotSuperClass import PlotSuperClass
from matplotlib.gridspec import GridSpec
from matplotlib.ticker import FuncFormatter
from glob import glob
import numpy as np
import matplotlib.animation as animation
import matplotlib.pyplot as plt
import os

#{{{PlotAnimSuperClass
class PlotAnimSuperClass(PlotSuperClass):
    """
    Super class for animation plots.

    Handles common plot options and saving.
    """

    #{{{constructor
    def __init__(self                     ,\
                 *args                    ,\
                 blobOrHole         = None,\
                 averagedBlobOrHole = None,\
                 **kwargs):
        #{{{docstring
        """
        Constructor for PlotAnimSuperClass.

        * Calls the parent constructor
        * Sets member data
        * Sets the animation options

        Parameters
        ----------
        *args : positional arguments
            See parent constructor for details.
        blobOrHole : [None|"blobs"|"holes"]
            Only in use when looking at blobs.
            Used  when setting the fileName.
        averagedBlobOrHole : [None|bool]
            Only in use when looking at blobs.
            Used  when setting the fileName.
        **kwargs : keyword arguments
            See parent constructor for details
        """
        #}}}

        # Call the constructor of the parent class
        super().__init__(*args, **kwargs)

        # Set member data
        self._blobOrHole         = blobOrHole
        self._averagedBlobOrHole = averagedBlobOrHole

        # Set animation and text options
        self.setAnimationOptions()

        # Magic numbers
        self._axRasterization = -10
    #}}}

    #{{{setAnimationOptions
    def setAnimationOptions(self, bitrate = -1, fps = 10, codec = "h264"):
        #{{{docstring
        """
        Reset the save destination.

        Parameters
        ----------
        bitrate : int
            Sets the quality of the animation.
            -1 gives automatic quality.
        fps : int
            Frames per second.
            Sets the speed of the plot as indicated in
            http://stackoverflow.com/questions/22010586/matplotlib-animation-duration
        codec : str
            Codec to use.
            Default is h264.
            For installation, see
            https://github.com/loeiten/usingLinux/blob/master/installationProcedures/ffmpeg.md
        """
        #}}}
        self._bitrate = bitrate
        self._fps     = fps
        self._codec   = codec
    #}}}

    #{{{plotSaveShow
    def plotSaveShow(self, fig, fileName, func, frames):
        #{{{docstring
        """
        Saves, show and closes the plot.

        NOTE: In order to make .png and .pdf snapshots of the fields, .pngs
              and .pdfs will not be overwritten, but gets an increasing
              number appended the name.

        Parameters
        ----------
        fig : Figure
            Figure to save.
        fileName : str
            Name of the file, including the path and the excluding the
            extension
        func : function
            The function to use for generating the animation.
        frames : int
            Number of frames.
            If this is less than one, a normal plot will be made.
        """
        #}}}

        if self._blobOrHole is not None:
            fileName += "-{}".format(self._blobOrHole)
            if self._averagedBlobOrHole:
                fileName += "-{}".format("avg")

        if frames > 1:
            # Animate
            anim = animation.FuncAnimation(fig            ,\
                                           func           ,\
                                           frames = frames,\
                                           blit   = False ,\
                                           )

            if self._savePlot:
                FFMpegWriter = animation.writers['ffmpeg']
                writer = FFMpegWriter(bitrate = self._bitrate,\
                                      fps     = self._fps    ,\
                                      codec   = self._codec)

                # Hard coded magic number
                self._extension = "mp4"

                # Get the number
                files = glob(fileName + "*")
                if self._averagedBlobOrHole is not None\
                   and not self._averagedBlobOrHole:
                    # Remove the entries containing avg
                    files = [f for f in files if "avg" not in f]
                if len(files) != 0:
                    nrs = sorted([int(curFile.split("-")[-1].split(".")[0])\
                                  for curFile in files])
                    nr  = nrs[-1] + 1
                else:
                    nr = 0

                # Save the animation
                fileName = "{}-{}.{}".format(fileName, nr, self._extension)
                anim.save(fileName, writer = writer)
                print("Saved to {}".format(fileName))
        else:
            if self._savePlot:
                if self._extension is None:
                    self._extension = "png"

                # Get the number
                files = glob(fileName + "*")
                if self._averagedBlobOrHole is not None\
                   and not self._averagedBlobOrHole:
                    # Remove the entries containing avg
                    files = [f for f in files if "avg" not in f]
                if len(files) != 0:
                    nrs = sorted([int(curFile.split("-")[-1].split(".")[0])\
                                  for curFile in files])
                    nr  = nrs[-1] + 1
                else:
                    nr = 0

                # Save the figure
                fileName = "{}-{}.{}".format(fileName, nr, self._extension)
                PlotHelper.savePlot(fig, fileName)

        if self._showPlot:
            fig.show()

        plt.close(fig)
    #}}}
#}}}

#{{{PlotAnim1DSuperClass
class PlotAnim1DSuperClass(PlotAnimSuperClass):
    """
    Super class for 1D animation plots.

    Handles common plot options and saving.
    """

    #{{{constructor
    def __init__(self,\
                 *args,\
                 **kwargs):
        #{{{docstring
        """
        Constructor for PlotAnim1DSuperClass.

        * Calls the parent constructor
        * Sets the variable legend template

        Parameters
        ----------
        *args : positional arguments
            See parent constructor for details
        **kwargs : keyword arguments
            See parent constructor for details
        """
        #}}}

        # Call the constructor of the parent class
        super().__init__(*args, **kwargs)

        # Set the colormap
        self._cmap = seqCMap3

        # Magic numbers
        self._cols     = 2
        self._marker   = "o"
        self._ddtColor = "k"

        # Set var label template
        if self.uc.convertToPhysical:
            unitsOrNormalization = " $[{units}]$"
        else:
            unitsOrNormalization = "${normalization}$"

        self._varLegendTemplate = r"${{}}${}".format(unitsOrNormalization)
    #}}}

    #{{{_createFiguresAndAxes
    def _createFiguresAndAxes(self):
        """
        Creates the figures and axes and organizes the plot.
        """

        # Calculate the number of rows
        rows = int(np.ceil(len(self._vars)/self._cols))

        # Create the figure
        figSize = SizeMaker.array(self._cols    ,\
                                  rows          ,\
                                  aSingle = 0.40,\
                                  )
        self._fig = plt.figure(figsize=figSize)

        # Create the axes
        gs = GridSpec(rows, self._cols)
        self._axes = []
        # Make first ax
        firstAx = self._fig.add_subplot(gs[0])
        firstAx.grid(True)
        self._axes.append(firstAx)
        # Make the rest of the axes
        for nr in range(1, len(self._vars)):
            ax = self._fig.add_subplot(gs[nr])
            ax.grid(True)
            self._axes.append(ax)

        # Cast to tuple
        self._axes = tuple(self._axes)

        # Set the x-labels
        totalAx = len(tuple(self._vars.keys()))
        for nr in range(totalAx-self._cols):
            self._axes[nr].tick_params(labelbottom="off")
        for nr in range(totalAx-self._cols, totalAx):
            self._axes[nr].set_xlabel(self._xlabel)

        # Adjust the subplots
        # NOTE: Measured in fractions of average axis widths
        self._fig.subplots_adjust(hspace=0.17, wspace=0.55)
    #}}}

    #{{{_initialPlot
    def _initialPlot(self):
        #{{{docstring
        """
        Initial plot.

        The initial plot:
            * Fetches the labels
            * Finds the max/min of all lines
            * Plots normal lines and makes the axes pretty
            * Plots ddt (if present)
            * Populates self._lines and self._ddtLines with the lines
        """
        #}}}

        # Placeholder for the lines
        self._lines = []

        # Plot and obtain the level
        for ax, key, color in zip(self._axes, self._plotOrder, self._colors):
            # Obtain the legend
            pltVarName = self._ph.getVarPltName(key)
            if self.uc.convertToPhysical:
                legend = self._varLegendTemplate.\
                    format(pltVarName, **self.uc.conversionDict[key])
            else:
                legend = "${}$".format(pltVarName)

            # Do the plot
            self._lines.append(\
                        ax.plot(self._X,\
                                self._vars[key][0,:],\
                                marker          = self._marker,\
                                color           = color       ,\
                                markeredgecolor = color       ,\
                                markerfacecolor = color       ,\
                                label           = legend      ,\
                                )[0]\
                              )

            vMax, vMin = getMaxMinAnimation((self._vars[key],), False, False)
            ax.set_ylim(vMin[0], vMax[0])

            # Make the ax pretty
            self._ph.makePlotPretty(ax,\
                                    yprune="both",\
                                    loc="upper right",\
                                    rotation = 45,\
                                    ybins = 6
                                    )

        # If ddt is present
        if self._ddtPresent:
            self._ddtLines = []
            for key, color in zip(self._plotOrder, self._colors):
                # Redo the plots
                self._ddtLines.append(\
                        self._axes[-1].plot(self._X                       ,\
                                            self._vars[key][0,:]          ,\
                                            marker          = self._marker,\
                                            color           = color       ,\
                                            markeredgecolor = color       ,\
                                            markerfacecolor = color       ,\
                                            )[0]\
                                  )
            pltVarName = self._ph.getVarPltName(self._ddtVar)
            if self.uc.convertToPhysical:
                legend = self._varLegendTemplate.\
                    format(pltVarName, **self.uc.conversionDict[key])
            else:
                legend = "${}$".format(pltVarName)

            # Plot the ddt
            self._ddtLines.append(\
                    self._axes[-1].plot(self._X                         ,\
                                        self._vars[self._ddtVar][0,:]   ,\
                                        marker          = self._marker  ,\
                                        color           = self._ddtColor,\
                                        markeredgecolor = self._ddtColor,\
                                        markerfacecolor = self._ddtColor,\
                                        label           = legend        ,\
                                        )[0]\
                                )

            # Make an array tuple in order to check for max/min
            arrayTuple = tuple(self._vars[key] for key in self._plotOrder)
            vMax, vMin = getMaxMinAnimation(arrayTuple, False, False)
            self._axes[-1].set_ylim(vMin[0], vMax[0])

            # Make the ax pretty
            self._ph.makePlotPretty(self._axes[-1],\
                                    yprune="both",\
                                    loc="upper right",\
                                    rotation = 45,\
                                    ybins = 6)

        # Cast to tuples
        self._lines = tuple(self._lines)
        if self._ddtPresent:
            self._ddtLines = tuple(self._ddtLines)
    #}}}

    #{{{_setColors
    def _setColors(self):
        """
        Sets the colors to be used in the plotting
        """
        colorSpace = np.arange(len(self._vars))
        self._colors = self._cmap(np.linspace(0, 1, len(colorSpace)))
        # Cast to avoid a.any() or a.all() bug, see
        # https://github.com/matplotlib/matplotlib/issues/8750
        # for details
        self._colors = tuple(tuple(c) for c in self._colors)
    #}}}
#}}}

#{{{PlotAnim2DSuperClass
class PlotAnim2DSuperClass(PlotAnimSuperClass):
    """
    Super class for 2D animation plots.

    Handles common plot options and saving.
    """

    #{{{constructor
    def __init__(self,\
                 *args,\
                 fluct = None,\
                 **kwargs):
        #{{{docstring
        """
        Constructor for PlotAnim2DSuperClass.

        * Calls the parent constructor

        * Stores common plotting options:
            * Text
            * Extra contourf arguments
        * Sets the var label template

        Parameters
        ----------
        *args : positional arguments
            See parent constructor for details
        fluct: bool
            Whether or not the fluctuations are being plotted.
        **kwargs : keyword arguments
            See parent constructor for details
        """
        #}}}

        # Guard
        if fluct is None:
            raise ValueError("'fluct' must be bool")

        # Call the constructor of the parent class
        super().__init__(*args, **kwargs)

        # Set memberdata
        self._fluct = fluct

        # Set extra contourf keyword arguments
        self._cfKwargs = {}
        self.setContourfArguments()

        # Update extra contourf keyword arguments with cmap and zorder
        if self._fluct:
            cmap = divCMap
        else:
            cmap = seqCMap
        self._cfKwargs.update({"cmap" : cmap, "zorder" : -20})

        # Set var label template
        if self.uc.convertToPhysical:
            unitsOrNormalization = " $[{units}]$"
        else:
            unitsOrNormalization = "${normalization}$"
        if not(self._fluct):
            self._varLabelTemplate = r"${{}}${}".format(unitsOrNormalization)
        else:
            self._varLabelTemplate = r"$\widetilde{{{{{{}}}}}}${}".\
                    format(unitsOrNormalization)
    #}}}

    #{{{setContourfArguments
    def setContourfArguments(self, vmax=None, vmin=None, levels=None):
        #{{{docstring
        """
        Set extra contourf keyword arguments.

        Parameters
        ---------
        vmax : [None|tuple]
            Max value to give a color.
            One for each frame if not None.
            If None: vmin and levels must also be None
            See getMaxMinAnimation in plot2DHelpers for a function which
            automatically does this.
        vmin : [None|tuple]
            Min value to give a color.
            One for each frame if not None.
            If None: vmax and levels must also be None
            See getMaxMinAnimation in plot2DHelpers for a function which
            automatically does this.
        levels : [None|tuple]
            The levels to  use.
            One for each frame if not None.
            If None: vmax and vmin must also be None
            See getLevelsAnimation in plot2DHelpers for a function which
            automatically does this.
        """
        #}}}

        # Guard
        success = True
        self._iterableLevels = True
        if vmax is None:
            self._iterableLevels = False
            if vmin is not None and levels is not None:
                success = False
        elif vmin is None:
            self._iterableLevels = False
            if vmax is not None and levels is not None:
                success = False
        elif levels is None:
            self._iterableLevels = False
            if vmax is not None and vmin is not None:
                success = False
        if not(success):
            message ="Either all or none of vmax, vmin and levels must be None"
            raise ValueError(message)

        if self._iterableLevels:
            self._vmax   = vmax
            self._vmin   = vmin
            self._levels = levels

            self._cfKwargs.update({"vmax"   : self._vmax[0]  ,\
                                   "vmin"   : self._vmin[0]  ,\
                                   "levels" : self._levels[0],\
                                   })
        else:
            self._cfKwargs.update({"vmax"   : None,\
                                   "vmin"   : None,\
                                   "levels" : None,\
                                  })
    #}}}

    #{{{setContourArguments
    def setContourArguments(self, vmax=None, vmin=None, levels=None):
        #{{{docstring
        """
        Set extra contour keyword arguments.
        Only used if an overplot of phi is done.

        Parameters
        ---------
        vmax : [None|tuple]
            Max value to give a color.
            One for each frame if not None.
            If None: vmin and levels must also be None
            See getMaxMinAnimation in plot2DHelpers for a function which
            automatically does this.
        vmin : [None|tuple]
            Min value to give a color.
            One for each frame if not None.
            If None: vmax and levels must also be None
            See getMaxMinAnimation in plot2DHelpers for a function which
            automatically does this.
        levels : [None|tuple]
            The levels to  use.
            One for each frame if not None.
            If None: vmax and vmin must also be None
            See getLevelsAnimation in plot2DHelpers for a function which
            automatically does this.
        """
        #}}}

        # Guard
        success = True
        self._phiIterableLevels = True
        if vmax is None:
            self._phiIterableLevels = False
            if vmin is not None and levels is not None:
                success = False
        elif vmin is None:
            self._phiIterableLevels = False
            if vmax is not None and levels is not None:
                success = False
        elif levels is None:
            self._phiIterableLevels = False
            if vmax is not None and vmin is not None:
                success = False
        if not(success):
            message ="Either all or none of vmax, vmin and levels must be None"
            raise ValueError(message)

        if self._phiIterableLevels:
            self._phiVmax   = vmax
            self._phiVmin   = vmin
            self._phiLevels = levels

            self._cKwargs = {"vmax"   : self._phiVmax[0]  ,\
                             "vmin"   : self._phiVmin[0]  ,\
                             "levels" : self._phiLevels[0],\
                             }
        else:
            self._cKwargs = {"vmax"   : None,\
                             "vmin"   : None,\
                             "levels" : None,\
                             }
    #}}}

    #{{{setPhiData
    def setPhiData(self, phi):
        #{{{docstring
        """
        Sets the phi which will be overplotted as a contour.

        Parameters
        ----------
        phi : array
            A 3d array of the phi for each point in x and y for each time.
            NOTE: Must have the dimensions as the data to be overplotted
        """
        #}}}

        self._phi         = phi
        self._overplotPhi = True
    #}}}

    #{{{setPhiParData
    def setPhiParData(self, phiPPi):
        #{{{docstring
        """
        Sets the phi par which will be overplotted as a contour in the
        parallel plot.

        Parameters
        ----------
        phi : array
            A 3d array of the phi for each point in x and y for each time.
            NOTE: Must have the dimensions as the data to be overplotted
        """
        #}}}

        self._phiPPi      = phiPPi
        self._overplotPhi = True
    #}}}

    #{{{_updateColorbar
    def _updateColorbar(self, fig, plane, cBarAx, tInd):
        #{{{docstring
        """
        Updates the colorbar.

        Parameters
        ----------
        fig : Figure
            The figure where the colorbar belongs.
        plane : contour-like
            The plane where the colorbar reads the data from.
        cBarAx : Axis
            The axis where the colorbar belongs.
        tInd : int
            The current time index.
        """
        #}}}

        # Set the colorbar
        # Clear the axis
        # http://stackoverflow.com/questions/39472017/how-to-animate-the-colorbar-in-matplotlib/39596853
        cBarAx.cla()
        if self._fluct and self._iterableLevels:
            # Create the ticks (11 with 0 in the center)
            nTicks = 11
            ticks  = np.linspace(self._vmin[tInd], self._vmax[tInd], nTicks)
            # Enforce the center one to be 0 (without round off)
            ticks[int((nTicks - 1)/2)] = 0
        else:
            ticks = None

        self._cBar = fig.colorbar(plane,\
                        cax    = cBarAx,\
                        ticks  = ticks,\
                        format = FuncFormatter(plotNumberFormatter))
    #}}}

    #{{{_setFileName
    def _setFileName(self, plotTypeName):
        #{{{docstring
        """
        Sets self._fileName

        Parameters
        ----------
        plotTypeName : str
            The plot type name
        """
        #}}}
        if self._fluct:

            fileName = "{}-{}-{}-fluct"\
                    .format(self._varName, plotTypeName, "2D")
        else:
            fileName = "{}-{}-{}".format(self._varName, plotTypeName, "2D")

        self._fileName = os.path.join(self._savePath, fileName)
    #}}}

    #{{{_setupDoubleFigs
    def _setupDoubleFigs(self):
        """
        Sets up the double figures
        """

        figSize = SizeMaker.standard(w=6.3, a=0.39)
        # NOTE: tight_layout=True gives wobbly plot as the precision of
        #       the colorbar changes during the animation
        self._fig = plt.figure(figsize = figSize)

        # Create figure and axes
        gs           = GridSpec(1, 3, width_ratios=(20, 20, 1))
        self._perpAx = self._fig.add_subplot(gs[0])
        self._cBarAx = self._fig.add_subplot(gs[2])
        self._fig.subplots_adjust(wspace=0.50)
        self._perpAx.grid(True)

        name = self.__class__.__name__
        if name == "PlotAnim2DPerpPar":
            self._parAx  = self._fig.add_subplot(gs[1])
            self._parAx.grid(True)
        elif name == "PlotAnim2DPerpPol":
            self._polAx  = self._fig.add_subplot(gs[1])
            self._polAx.grid(True)

        # Adjust the colorbar
        pos = self._cBarAx.get_position()
        pos = (pos.x0-0.075, pos.y0, pos.width, pos.height)
        self._cBarAx.set_position(pos)
    #}}}
#}}}
