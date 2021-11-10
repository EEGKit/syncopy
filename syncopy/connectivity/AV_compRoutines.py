# -*- coding: utf-8 -*-
#
# computeFunctions and -Routines to post-process
# the parallel single trial computations to be found in ST_compRoutines.py
# The standard use case involves computations on the
# trial average, meaning that the SyNCoPy input to these routines
# consists of only '1 trial` and parallelising over channels
# is non trivial and atm also not supported. Pre-processing
# like padding or detrending already happened in the single trial
# compute functions.
#

# Builtin/3rd party package imports
import numpy as np
from inspect import signature

# syncopy imports
from syncopy.specest.const_def import spectralDTypes, spectralConversions
from syncopy.shared.errors import SPYWarning
from syncopy.shared.computational_routine import ComputationalRoutine
from syncopy.shared.kwarg_decorators import unwrap_io
from syncopy.shared.errors import (
    SPYValueError,
    SPYTypeError,
    SPYWarning,
    SPYInfo)


@unwrap_io
def normalize_csd_cF(trl_dat,
                     output='abs',
                     chunkShape=None,
                     noCompute=False):
          
    """
    Given the trial averaged cross spectral densities,
    calculates the normalizations to arrive at the 
    channel x channel coherencies. If S_ij(f) is the
    averaged cross-spectrum between channel i and j, the 
    coherency [1]_ is defined as:

          C_ij = S_ij(f) / (|S_ii| |S_jj|)

    The coherence is now defined as either |C_ij|
    or |C_ij|^2, this can be controlled with the `output`
    parameter.

    Parameters
    ----------
    trl_dat : (1, nFreq, N, N) :class:`numpy.ndarray`
        Cross-spectral densities for `N` x `N` channels
        and `nFreq` frequencies.
    output : {'abs', 'pow', 'fourier'}, default: 'abs'
        Also after normalization the coherency is still complex (`'fourier'`), 
        to get the real valued coherence 0 < C_ij(f) < 1 one can either take the
        absolute (`'abs'`) or the absolute squared (`'pow'`) values of the
        coherencies. The definitions are not uniform in the literature, 
        hence multiple output types are supported.
    noCompute : bool
        Preprocessing flag. If `True`, do not perform actual calculation but
        instead return expected shape and :class:`numpy.dtype` of output
        array.

    Returns
    -------
    CS_ij : (1, nFreq, N, N) :class:`numpy.ndarray`
        Coherence for all channel combinations i,j.
        `N` corresponds to number of input channels.

    Notes
    -----

    This function also normalizes cross-covariances to cross-correlations.

    This method is intended to be used as
    :meth:`~syncopy.shared.computational_routine.ComputationalRoutine.computeFunction`
    inside a :class:`~syncopy.shared.computational_routine.ComputationalRoutine`.
    Thus, input parameters are presumed to be forwarded from a parent metafunction.
    Consequently, this function does **not** perform any error checking and operates
    under the assumption that all inputs have been externally validated and cross-checked.

    .. [1] Nolte, Guido, et al. "Identifying true brain interaction from EEG 
          data using the imaginary part of coherency." 
          Clinical neurophysiology 115.10 (2004): 2292-2307.


    See also
    --------
    cross_spectra_cF : :func:`~syncopy.connectivity.ST_compRoutines.cross_spectra_cF`
             Single trial (Multi-)tapered cross spectral densities.

    """

    # it's the same as the input shape!
    outShape = trl_dat.shape

    # For initialization of computational routine,
    # just return output shape and dtype
    # cross spectra are complex!
    if noCompute:
        return outShape, spectralDTypes[output]

    # re-shape to (nChannels x nChannels x nFreq)
    CS_ij = trl_dat.transpose(0, 2, 3, 1)[0, ...]
    
    # main diagonal has shape (nChannels x nFreq): the auto spectra
    diag = CS_ij.diagonal()
    # get the needed product pairs of the autospectra
    Ciijj = np.sqrt(diag[:, :, None] * diag[:, None, :]).T
    CS_ij = CS_ij / Ciijj

    CS_ij = spectralConversions[output](CS_ij)

    # re-shape to original form and re-attach dummy time axis
    return CS_ij[None, ...].transpose(0, 3, 1, 2)

    
class Normalize_CrossMeasure(ComputationalRoutine):

    """
    Compute class that normalizes trial averaged quantities
    of :class:`~syncopy.CrossSpectralData` objects
    like cross-spectra or cross-covariances to arrive at
    coherencies or cross-correlations respectively.

    Sub-class of :class:`~syncopy.shared.computational_routine.ComputationalRoutine`,
    see :doc:`/developer/compute_kernels` for technical details on Syncopy's compute
    classes and metafunctions.

    See also
    --------
    syncopy.connectivityanalysis : parent metafunction
    """

    # the hard wired dimord of the cF
    dimord = ['time', 'freq', 'channel_i', 'channel_j']

    computeFunction = staticmethod(normalize_csd_cF)

    method = "" # there is no backend
    # 1st argument,the data, gets omitted
    method_keys = {}
    cF_keys = list(signature(normalize_csd_cF).parameters.keys())[1:]

    def pre_check(self):
        '''
        Make sure we have a trial average, 
        so the input data only consists of `1 trial`.
        Can only be performed after initialization!
        '''
        
        if self.numTrials != 1:
            lgl = "1 trial: normalizations can only be done on averaged quantities!"
            act = f"DataSet contains {self.numTrials} trials"
            raise SPYValueError(legal=lgl, varname="data", actual=act)
    
    def process_metadata(self, data, out):

        # Some index gymnastics to get trial begin/end "samples"
        if data._selection is not None:
            chanSec = data._selection.channel
            trl = data._selection.trialdefinition
            for row in range(trl.shape[0]):
                trl[row, :2] = [row, row + 1]
        else:
            chanSec = slice(None)
            time = np.arange(len(data.trials))
            time = time.reshape((time.size, 1))
            trl = np.hstack((time, time + 1,
                             np.zeros((len(data.trials), 1)),
                             np.array(data.trialinfo)))

        # Attach constructed trialdef-array (if even necessary)
        if self.keeptrials:
            out.trialdefinition = trl
        else:
            out.trialdefinition = np.array([[0, 1, 0]])
            
        # Attach remaining meta-data
        out.samplerate = data.samplerate
        out.channel_i = np.array(data.channel_i[chanSec])
        out.channel_j = np.array(data.channel_j[chanSec])
        out.freq = data.freq
