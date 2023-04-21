API for Developers
------------------

syncopy.datatype
^^^^^^^^^^^^^^^^

.. autosummary::
    :toctree: _stubs
    :template: syncopy_class.rst

    syncopy.datatype.base_data.BaseData
    syncopy.datatype.base_data.Selector
    syncopy.datatype.base_data.FauxTrial
    syncopy.shared.StructDict
    syncopy.datatype.continuous_data.ContinuousData
    syncopy.datatype.discrete_data.DiscreteData


syncopy.misc
^^^^^^^^^^^^

.. autosummary::
    :toctree: _stubs

    syncopy.tests.misc.generate_artificial_data


syncopy.shared
^^^^^^^^^^^^^^

.. autosummary::
    :toctree: _stubs

    syncopy.shared.computational_routine.ComputationalRoutine
    syncopy.shared.errors.SPYError
    syncopy.shared.errors.SPYTypeError
    syncopy.shared.errors.SPYValueError
    syncopy.shared.errors.SPYIOError
    syncopy.shared.errors.SPYWarning
    syncopy.shared.kwarg_decorators.unwrap_cfg
    syncopy.shared.kwarg_decorators.unwrap_select
    syncopy.shared.kwarg_decorators.process_io
    syncopy.shared.kwarg_decorators.detect_parallel_client
    syncopy.shared.kwarg_decorators._append_docstring
    syncopy.shared.kwarg_decorators._append_signature
    syncopy.shared.tools.best_match


syncopy.specest
^^^^^^^^^^^^^^^

.. autosummary::
    :toctree: _stubs

    syncopy.specest.mtmfft.mtmfft
    syncopy.specest.compRoutines.MultiTaperFFT
    syncopy.specest.compRoutines.mtmfft_cF
    syncopy.specest.mtmconvol.mtmconvol
    syncopy.specest.compRoutines.MultiTaperFFTConvol
    syncopy.specest.compRoutines.mtmconvol_cF
    syncopy.specest.compRoutines._make_trialdef
    syncopy.specest.wavelet.wavelet
    syncopy.specest.compRoutines.WaveletTransform
    syncopy.specest.compRoutines.wavelet_cF
    syncopy.specest.compRoutines.SuperletTransform
    syncopy.specest.compRoutines.superlet_cF
    syncopy.specest.compRoutines._make_trialdef
    syncopy.specest.superlet.superlet
    syncopy.specest.wavelet.get_optimal_wavelet_scales
    syncopy.specest.compRoutines.FooofSpy


syncopy.connectivity
^^^^^^^^^^^^^^^^^^^^

.. autosummary::
    :toctree: _stubs

    syncopy.connectivity.AV_compRoutines.GrangerCausality


syncopy.plotting
^^^^^^^^^^^^^^^^

.. autosummary::
    :toctree: _stubs

    syncopy.plotting.spy_plotting.singlepanelplot
    syncopy.plotting.spy_plotting.multipanelplot
