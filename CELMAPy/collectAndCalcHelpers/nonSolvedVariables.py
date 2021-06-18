#!/usr/bin/env python

"""
Contains functions which calculates non-solved variables
"""

import scipy.constants as cst
import numpy as np

#{{{calcN
def calcN(lnN, normalized, uc=None):
    #{{{docstring
    """
    Calculates n = exp(lnN)

    Parameters
    ----------
    lnN : [float|array]
       The logarithm of n
    normalized : bool
        Whether or not the output should be normalized
    uc : [None|UnitsConverter]
        The unitsconverter (only needed if normalized is False)

    Returns
    -------
    n : [float|array]
        The density
    """
    #}}}
    n = np.exp(lnN)
    if normalized:
        return n
    else:
        if uc == None:
            raise ValueError("uc must be set if normalized is False")
        return uc.physicalConversion(n , "n")
#}}}

#{{{calcUIPar
def calcUIPar(momDensPar, n):
    #{{{docstring
    r"""
    Calculates u_{i,\|} = \frac{nu_{i,\|}}{n}.

    Parameters
    ----------
    momDensPar : [float|array]
       nu_{i,\|}
    n : [float|array]
        The density

    Returns
    -------
    uIPar : [float|array]
        The parallel ion velocity
    """
    #}}}
    return momDensPar/n
#}}}

#{{{calcUEPar
def calcUEPar(uIPar, jPar, n, normalized):
    #{{{docstring
    r"""
    Calculates the parallel electron velocity

    In normalized units
    u_{e,\|} = u_{i,\|} - \frac{j_{\|}}{n}
    In physical units
    u_{e,\|} = u_{i,\|} - \frac{j_{\|}}{en}

    Parameters
    ----------
    uIPar : [float|array]
       The parallel ion velocity
    jPar : [float|array]
       The paralell current
    n : [float|array]
       The density
    normalized : bool
        Whether or not the input is normalized

    Returns
    -------
    uEPar : [float|array]
        The parallel electron velocity
    """
    #}}}
    if normalized:
        return uIPar - jPar/n
    else:
        return uIPar - jPar/(cst.e*n)
#}}}
