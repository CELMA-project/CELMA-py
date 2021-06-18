#!/usr/bin/env python

""" Contains the PlotHelper class """

from .plotNumberFormatter import plotNumberFormatter
from matplotlib.ticker import MaxNLocator, FuncFormatter
from sympy import Rational
import numpy as np
import pickle
import os

#{{{PlotHelper
class PlotHelper(object):
    """Contains common routines used when making plots"""

    #{{{Static members
    _varPltName = {\
        # Main fields
        "lnN"       : r"\ln(n)"          ,\
        "n"         : r"n"               ,\
        "jPar"      : r"j_{\parallel}"   ,\
        "phi"       : r"\phi"            ,\
        "vort"      : r"\Omega"          ,\
        "vortD"     : r"\Omega^D"        ,\
        "momDensPar": r"nu_{i,\parallel}",\
        "uIPar"     : r"u_{i,\parallel}" ,\
        "uEPar"     : r"u_{e,\parallel}" ,\
        "S"         : r"S"               ,\
        # ddt fields
        "ddt(lnN)"       : r"\partial_t \ln(n)"            ,\
        "ddt(jPar)"      : r"\partial_t j_{\parallel}"     ,\
        "ddt(vortD)"     : r"\partial_t \Omega^D"          ,\
        "ddt(vort)"      : r"\partial_t \Omega"            ,\
        "ddt(momDensPar)": r"\partial_t (nu_{i,\parallel})",\
        # lnN fields
        "lnNAdv"        :  r"-\frac{1}{JB}\{\phi,\ln(n)\}"                   ,\
        "lnNRes"        : (r"\frac{\nu_{ei}}{\mu}\left(\nabla^2_\perp\ln(n)"  \
                           r" + \left[\nabla_\perp\ln(n)\right]^2\right)")   ,\
        "gradUEPar"     :  r"-\partial_{\parallel}u_{e,\parallel}"           ,\
        "lnNUeAdv"      :  r"-u_{e,\parallel}\partial_\parallel\ln(n)"       ,\
        "srcN"          :  r"\frac{S}{n}"                                    ,\
        "lnNPerpArtVisc":  r"D_{n,\perp} \partial^2_{\perp}\ln(n)"           ,\
        "lnNParArtVisc" :  r"D_{n,\parallel} \partial^2_{\parallel}\ln(n)"   ,\
        # jPar fields
        "jParAdv"        :  r"-\frac{1}{JB}\{\phi,j_{\parallel}\}"   ,\
        "uEParAdv"       : (r"nu_{e,\parallel}\partial_\parallel"     \
                            r" u_{e,\parallel}")                     ,\
        "uIParAdv"       : (r"-nu_{i,\parallel}\partial_\parallel"    \
                            r" u_{i,\parallel}")                     ,\
        "jParParAdv"     : (r"-\frac{j_\parallel}{n}"                 \
                            r"\partial_\parallel(nu_{e,\parallel})") ,\
        "gradPhiLnN"     : (r"\mu n\partial_{\parallel}"              \
                            r"\left(T_e \ln(n) - \phi \right)")      ,\
        "jParRes"        :  r"-0.51\nu_{ei}j_\parallel"              ,\
        "neutralERes"    :  r"n\nu_{en}u_{e,\parallel}"              ,\
        "neutralIRes"    :  r"-n\nu_{in}u_{i,\parallel}"             ,\
        "jParVisc"       : (r"-\frac{4}{3}\mu\eta_{e,0}"              \
                            r"\partial^2_{\parallel}u_{e,\parallel}"),\
        "jParPerpArtVisc": (r"D_{j_{\parallel}, \perp}\nabla^2_\perp" \
                            r" j_{\parallel}")                       ,\
        "jParParArtVisc" : (r"D_{j_{\parallel}, \parallel}"           \
                            r"\partial^2_{\parallel}j_{\parallel}")  ,\
        "jParHyperVisc"  : (r"D^H_{j_{\parallel}, \parallel}"         \
                            r"\partial^4_{\parallel}j_{\parallel}")  ,\
        # momDensPar fields
        "momDensAdv"        :  r"-\frac{1}{JB}\{\phi, nu_{i,\parallel}\}",\
        "uIFluxAdv"         : (r"-u_{i,\parallel}\partial_\parallel"      \
                               r"(nu_{e,\parallel})")                    ,\
        "elPressure"        :  r"-T_e\partial_{\parallel}n"              ,\
        "densDiffusion"     : (r"\frac{\nu_{ei}}{\mu}u_{i,\parallel}"     \
                               r"\nabla_\perp^2n")                       ,\
        "neutralEResMu"     :  r"-n\frac{1}{\mu}\nu_{en}u_{e,\parallel}" ,\
        "momDensVisc"       : (r"\frac{4}{3}\left("                       \
                               r"\eta_{i,0} \partial^2_{\parallel}"       \
                               r"u_{i,\parallel}"                         \
                               r"+\eta_{e,0} \partial^2_{\parallel}"      \
                               r"u_{e,\parallel}\right)")                ,\
        "momDensPerpArtVisc": (r"D_{nu_i,\perp}"                          \
                               r"\nabla^2_{\perp}"                        \
                               r"\left(nu_{i,\parallel}\right)")         ,\
        "momDensParArtVisc" : (r"D_{nu_i,\parallel}"                      \
                               r"\partial^2_{\parallel}nu_{i,\parallel}"),\
        # vort and vortD fields
        "vortNeutral"               :  r"-\nu_{in}n\Omega"                    ,\
        "potNeutral"                : (r"-\nu_{in}\nabla_\perp \phi \cdot"     \
                                       r" \nabla_\perp n")                    ,\
        "vortDAdv"                  :  r"-\frac{1}{JB}\{\phi, \Omega^D\}"     ,\
        "vortAdv"                   :  r"-\frac{1}{JB}\{\phi, \Omega\}"       ,\
        "kinEnAdvN"                 : (r"-\frac{1}{2J}\{\mathbf{u}_E \cdot"    \
                                       r"\mathbf{u}_E, n\}")                  ,\
        "parDerDivUIParNGradPerpPhi": (r"-\partial_\parallel \nabla\cdot"      \
                                       r"\left(u_{i,\parallel}"                \
                                       r"n \nabla_\perp\frac{\phi}{B}\right)"),\
        "divParCur"                 :  r"\partial_{\parallel}j_{\parallel}"   ,\
        "vortDParArtVisc"           : (r"D_{\Omega^D} \partial^2_{\parallel}"  \
                                       r"\Omega^D")                           ,\
        "vortDPerpArtVisc"          : (r"D_{\Omega^D, \perp} \nabla_\perp^2"   \
                                       r"\Omega^D")                           ,\
        "vortDHyperVisc"            : (r"D^H_{\Omega^D, \theta}"               \
                                       r" \partial_\theta^4\Omega^D")         ,\
        "vortParAdv"                : (r"-u_{i,\parallel}"                     \
                                       r"\partial_\parallel\Omega")           ,\
        "DDYGradPerpPhiGradPerpUI"  : (r"-\partial_\parallel"                  \
                                       r" \left( \nabla_\perp"
                                       r"\frac{\phi}{B}\right)"                \
                                       r"\cdot \nabla_\perp u_{i,\parallel}") ,\
        "divSourcePhi"              : (r"-\nabla\cdot"                         \
                                       r"\left(S\nabla_\perp\phi\right)")     ,\
        "divParCur"                 :  r"\partial_{\parallel}j_{\parallel}"   ,\
        "vortParArtVisc"            : (r"D_{\Omega} \partial^2_{\parallel}"    \
                                       r"\Omega")                             ,\
        "vortPerpArtVisc"           : (r"D_{\Omega, \perp} \nabla_\perp^2"     \
                                       r"\Omega")                             ,\
        "vortHyperVisc"             : (r"D^H_{\Omega, \theta}"                 \
                                       r"\partial_\theta^4\Omega")            ,\
        # Fluxes
        "fluxn" :r"nu_{E\times B,\rho}"  ,\
        # Miscellaneous
        "modeNr":r"$m_\theta$",\
        "B0"    :r"$B_0$"     ,\
        "Te0"   :r"$T_e$"     ,\
        "nn"    :r"$n_n$"     ,\
        "length":r"$z$"       ,\
        }
    #}}}

    #{{{__init__
    def  __init__(self                     ,\
                  convertToPhysical = False):
        #{{{docstring
        """
        The constructor for PlotHelper, which:

        * Sets the member data

        Parameters
        ----------
        convertToPhysical : bool
            Whether or not to convert to physical units.
        """
        #}}}

        # Set the member data
        self.convertToPhysical = convertToPhysical
    #}}}

    #{{{makeDimensionStringsDicts
    def makeDimensionStringsDicts(self, unitsConverter):
        #{{{docstring
        """
        Makes the dimension strings dicts.

        The tTxtDict, rhoTxtDict, thetaTxtDict and zTxtDict will be accessable
        from the PlotHelper object, and contain the following keys:
            * units         - String of the units for the variabls
            * normalization - String of the normalization for the variable
            * @Txt          - Variable with possible normalization
            * @TxtLabel     - Label of the variable
            * const@Txt     - Label when the variable is constant in a plot

        Expands the TxTDicts, so that they can easily be used when
        formatting text for labels and titles.
        """
        #}}}

        # String formatting
        self.tTxtDict     =\
            {"normalization":unitsConverter.getNormalization("t"  ),\
             "units"        :unitsConverter.getUnits        ("t"  ) }
        self.rhoTxtDict   =\
            {"normalization":unitsConverter.getNormalization("rho"),\
             "units"        :unitsConverter.getUnits        ("rho") }
        self.zTxtDict     =\
            {"normalization":unitsConverter.getNormalization("z"  ),\
             "units"        :unitsConverter.getUnits        ("z"  ) }
        self.thetaTxtDict = {}

        # Set generic string templates
        self.rhoTxtDict["rhoTxt"] =\
                r"$\rho{0[normalization]}$".format(self.rhoTxtDict)
        self.zTxtDict["zTxt"] =\
                r"$z{0[normalization]}$".format(self.zTxtDict)
        self.thetaTxtDict["constThetaTxt"] =\
                r"$\theta=${0[value]}$^{{\circ}}$"
        self.tTxtDict["tTxt"] =\
                r"$t{0[normalization]}$".format(self.tTxtDict)
        # Set label and title templates
        if self.convertToPhysical:
            self.rhoTxtDict["rhoTxtLabel"] = "{0[rhoTxt]} $[{0[units]}]$".\
                        format(self.rhoTxtDict)
            self.rhoTxtDict["constRhoTxt"] =\
                        r"{0[rhoTxt]} $=$ {0[value]} ${0[units]}$"
            self.zTxtDict["zTxtLabel"] = "{0[zTxt]} $[{0[units]}]$".\
                        format(self.zTxtDict)
            self.zTxtDict["constZTxt"] =\
                    r"{0[zTxt]} $=$ {0[value]} ${0[units]}$"
            self.tTxtDict["tTxtLabel"] = r"{0[tTxt]} $[{0[units]}]$".\
                        format(self.tTxtDict)
            self.tTxtDict["constTTxt"] =\
                        r"{0[tTxt]} $=$ {0[value]} ${0[units]}$"
        else:
            self.rhoTxtDict["rhoTxtLabel"] = "{0[rhoTxt]}".\
                                             format(self.rhoTxtDict)
            self.rhoTxtDict["constRhoTxt"] = r"{0[rhoTxt]} $=$ {0[value]}"
            self.zTxtDict  ["zTxtLabel"] = "{0[zTxt]}".\
                                           format(self.zTxtDict)
            self.zTxtDict  ["constZTxt"] = r"{0[zTxt]} $=$ {0[value]}"
            self.tTxtDict  ["tTxtLabel"] = r"{0[tTxt]}".\
                                         format(self.tTxtDict)
            self.tTxtDict  ["constTTxt"] = r"{0[tTxt]} $=$ {0[value]}"
    #}}}

    @staticmethod
    #{{{radiansOnAxis
    def radiansOnAxis(ax, axis):
        #{{{docstring
        """
        Sets radians on the given axis.

        Parameters
        ----------
        ax : Axis
            Axis to change x-axis on.
        axis : ["x"|"y"|"z"]
            Which axis to be modified
        """
        #}}}

        if axis == "x":
            getTicks  = ax.get_xticks
            setTicks  = ax.set_xticks
            setLabels = ax.set_xticklabels
            setLim    = ax.set_xlim
        elif axis == "y":
            getTicks  = ax.get_yticks
            setTicks  = ax.set_yticks
            setLabels = ax.set_yticklabels
            setLim    = ax.set_ylim
        elif axis == "z":
            getTicks  = ax.get_zticks
            setTicks  = ax.set_zticks
            setLabels = ax.set_zticklabels
            setLim    = ax.set_zlim
        else:
            message =\
                "{} is not a valid axis.\nExpected 'x','y' or 'z'".format(axis)
            raise ValueError(message)

        # Tigthen the x axis
        ax.autoscale(enable=True, axis=axis, tight=True)

        # Find max and min of the ticks
        ticks = getTicks()
        minAx = ticks[0]
        maxAx = ticks[-1]

        # Cast to radians
        # Floor to include the bottom-most tick
        minRad = int(np.floor(minAx/(np.pi/4)))
        # Ceil to include the top-most tick
        maxRad = int(np.ceil(maxAx/(np.pi/4)))

        # NOTE: Range excludes the last point
        theRange = range(minRad, maxRad+1)
        # Reset tick values
        setTicks(tuple(i*np.pi/4 for i in theRange))

        # Obtain the tick labels
        labelVals    = tuple(str(i*Rational(1, 4)) for i in theRange)
        labelStrings = []

        # NOTE: We add the sign to eaiser filter out 1pi
        for label in labelVals:
            if "/" in label:
                label =\
                    r"${:+d}\pi/{}$".\
                    format(int(label.split("/")[0]), label.split("/")[1])
            elif not("0" in label):
                label = r"${:+d}\pi$".format(int(label))
            elif "0" in label:
                label = r"$0$"

            labelStrings.append(label)

        # Remove 1pi
        labels = tuple(i.replace(r"-1\pi",r"-\pi") for i in labelStrings)
        labels = tuple(i.replace(r"+1\pi",r"\pi") for i in labels)
        labels = tuple(i.replace("+","") for i in labels)

        # Set the ticks
        setLabels(labels)
    #}}}

    @staticmethod
    #{{{getVarPltName
    def getVarPltName(var):
        #{{{docstring
        """
        Routine that returns the variable plot name.
        The return value does not include the $

        Parameters
        ----------
        var : str
            The variable to find the plot name for.

        Retruns
        -------
        varPltName : str
            The plot name
        """
        #}}}

        return PlotHelper._varPltName[var]
    #}}}

    @staticmethod
    #{{{makePlotPretty
    def makePlotPretty(ax                      ,\
                       xprune    = "lower"     ,\
                       yprune    = None        ,\
                       rotation  = "horizontal",\
                       rotationY = None        ,\
                       loc       = "best"      ,\
                       legend    = True        ,\
                       xbins     = None        ,\
                       ybins     = None        ,\
                       ):
        #{{{docstring
        """
        Routine that fixes some beauty-mistakes in matplotlib

        Parameters
        ----------
        ax : axis
            The axis to fix.
        xprune : str
            What ticks should be pruned on the x axis.
        yprune : str
            What ticks should be pruned on the y axis.
        rotation : [str | int]
            Rotation of the x axis.
        rotationY : [None | str | int]
            Rotation of the y axis.
        loc : str
            Location of the legend
        legend : bool
            Whether or not to make the legend pretty
        xbins : [None|int]
            Number of bins to use on the x-ticks
        ybins : [None|int]
            Number of bins to use on the y-ticks
        """
        #}}}

        # Avoid silly top value (only for non-log axes)
        try:
            ax.get_yaxis().get_major_formatter().set_useOffset(False)
        except:
            pass

        # Format the tick labels
        ax.set_xticklabels(ax.xaxis.get_majorticklabels(), rotation=rotation)
        ax.get_xaxis().set_major_formatter(FuncFormatter(plotNumberFormatter))
        if rotationY:
            ax.set_yticklabels(ax.yaxis.get_majorticklabels(),\
                               rotation=rotationY)
        ax.get_yaxis().set_major_formatter(FuncFormatter(plotNumberFormatter))

        # Plot the legend
        if legend:
            try:
                leg = ax.legend(loc       = loc ,\
                                fancybox  = True,\
                                numpoints = 1   ,\
                                )
                leg.get_frame().set_alpha(0.5)
            except AttributeError as ae:
                if "NoneType" in ae.args[0] and "get_frame" in ae.args[0]:
                    print("{0}{1}WARNING: Could not set legend{1}{0}".\
                          format("\n","!"*4))
                else:
                    raise ae

        # Plot the grid
        ax.grid(True)

        # Make sure no collision between the ticks
        if ax.get_xscale() != "log":
            ax.xaxis.set_major_locator(MaxNLocator(prune=xprune))

        if ax.get_yscale() != "log":
            # This destroys the ticks on log plots
            ax.yaxis.set_major_locator(MaxNLocator(prune=yprune))

        # Set number of bins
        if xbins is not None:
            if ax.get_xscale() != "log":
                ax.locator_params(axis="x", nbins=xbins)
            else:
                ax.locator_params(axis="x", numticks=xbins)
        if ybins is not None:
            if ax.get_yscale() != "log":
                ax.locator_params(axis="y", nbins=ybins)
            else:
                ax.locator_params(axis="y", numticks=ybins)
    #}}}

    @staticmethod
    #{{{savePlot
    def savePlot(fig, fileName, extraArtists=None, crop=True):
        #{{{docstring
        """
        Saves the figure

        Parameters
        ----------
        fig: figure
            The figure.
        fileName : str
            Full path of the plot.
        extraArtist : tuple
            Tuple of bbox_extra_artists to be saved
        crop : bool
            If True, whitespace will be removed.
        """
        #}}}

        if crop:
            bbox_inches        = "tight"
            bbox_extra_artists = extraArtists
            pad_inches         = 0
        else:
            bbox_inches        = None
            bbox_extra_artists = None
            pad_inches         = None


        # Create path if not exists
        directory = os.path.dirname(fileName)
        if directory != "" and directory != ".":
            if not os.path.exists(directory):
                    os.makedirs(directory)
                    print("{} created".format(directory))

        fig.savefig(fileName                               ,\
                    transparent        = True              ,\
                    bbox_inches        = bbox_inches       ,\
                    bbox_extra_artists = bbox_extra_artists,\
                    pad_inches         = pad_inches        ,\
                    )

        print("Saved to {}".format(fileName))

        # Redo fileName
        fileName = os.path.splitext(fileName)[0] + ".pickle"
        with open(fileName, "wb") as f:
            pickle.dump(fig, f, protocol=pickle.HIGHEST_PROTOCOL)

        print("Pickled to {}".format(fileName))
        print(("NOTE: Due to CEMLA.plotHelpers.plotFormatter, the "
               "unpickling must take place where 'import CELMAPy' is "
               "possible"))
    #}}}
#}}}
