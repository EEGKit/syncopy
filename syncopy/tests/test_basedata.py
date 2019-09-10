# -*- coding: utf-8 -*-
# 
# Test proper functionality of SyNCoPy BaseData class + helper
# 
# Created: 2019-03-19 10:43:22
# Last modified by: Stefan Fuertinger [stefan.fuertinger@esi-frankfurt.de]
# Last modification time: <2019-09-10 13:57:08>

import os
import tempfile
import h5py
import time
import pytest
import numpy as np
from numpy.lib.format import open_memmap
from memory_profiler import memory_usage
from syncopy.datatype import AnalogData
import syncopy.datatype as spd
from syncopy.datatype.base_data import VirtualData, Selector
from syncopy.shared.errors import SPYValueError, SPYTypeError
from syncopy.tests.misc import is_win_vm, is_slurm_node

# Construct decorators for skipping certain tests
skip_in_vm = pytest.mark.skipif(is_win_vm(), reason="running in Win VM")
skip_in_slurm = pytest.mark.skipif(is_slurm_node(), reason="running on cluster node")


class TestVirtualData():

    # Allocate test-dataset
    nChannels = 5
    nSamples = 30
    data = np.arange(1, nChannels * nSamples + 1).reshape(nSamples, nChannels)

    def test_alloc(self):
        with tempfile.TemporaryDirectory() as tdir:
            fname = os.path.join(tdir, "vdat")
            np.save(fname, self.data)
            dmap = open_memmap(fname + ".npy")

            # illegal type
            with pytest.raises(SPYTypeError):
                VirtualData({})

            # 2darray expected
            d3 = np.ones((2, 3, 4))
            np.save(fname + "3", d3)
            d3map = open_memmap(fname + "3.npy")
            with pytest.raises(SPYValueError):
                VirtualData([d3map])

            # rows/cols don't match up
            with pytest.raises(SPYValueError):
                VirtualData([dmap, dmap.T])

            # check consistency of VirtualData object
            for vk in range(2, 6):
                vdata = VirtualData([dmap] * vk)
                assert vdata.dtype == dmap.dtype
                assert vdata.M == dmap.shape[0]
                assert vdata.N == vk * dmap.shape[1]

            # Delete all open references to file objects b4 closing tmp dir
            del dmap, vdata, d3map

    def test_retrieval(self):
        with tempfile.TemporaryDirectory() as tdir:
            fname = os.path.join(tdir, "vdat.npy")
            fname2 = os.path.join(tdir, "vdat2.npy")
            np.save(fname, self.data)
            np.save(fname2, self.data * 2)
            dmap = open_memmap(fname)
            dmap2 = open_memmap(fname2)

            # ensure stacking is performed correctly
            vdata = VirtualData([dmap, dmap2])
            assert np.array_equal(vdata[:, :self.nChannels], self.data)
            assert np.array_equal(vdata[:, self.nChannels:], 2 * self.data)
            assert np.array_equal(vdata[:, 0].flatten(), self.data[:, 0].flatten())
            assert np.array_equal(vdata[:, self.nChannels].flatten(), 2 * self.data[:, 0].flatten())
            assert np.array_equal(vdata[0, :].flatten(),
                                  np.hstack([self.data[0, :], 2 * self.data[0, :]]))
            vdata = VirtualData([dmap, dmap2, dmap])
            assert np.array_equal(vdata[:, :self.nChannels], self.data)
            assert np.array_equal(vdata[:, self.nChannels:2 * self.nChannels], 2 * self.data)
            assert np.array_equal(vdata[:, 2 * self.nChannels:], self.data)
            assert np.array_equal(vdata[:, 0].flatten(), self.data[:, 0].flatten())
            assert np.array_equal(vdata[:, self.nChannels].flatten(),
                                  2 * self.data[:, 0].flatten())
            assert np.array_equal(vdata[0, :].flatten(),
                                  np.hstack([self.data[0, :], 2 * self.data[0, :], self.data[0, :]]))

            # illegal indexing type
            with pytest.raises(SPYTypeError):
                vdata[{}, :]

            # queried indices out of bounds
            with pytest.raises(SPYValueError):
                vdata[:, self.nChannels * 3]
            with pytest.raises(SPYValueError):
                vdata[self.nSamples * 2, 0]

            # Delete all open references to file objects b4 closing tmp dir
            del dmap, dmap2, vdata

    @skip_in_vm
    @skip_in_slurm
    def test_memory(self):
        with tempfile.TemporaryDirectory() as tdir:
            fname = os.path.join(tdir, "vdat.npy")
            data = np.ones((1000, 5000))  # ca. 38.2 MB
            np.save(fname, data)
            del data
            dmap = open_memmap(fname)

            # allocation of VirtualData object must not consume memory
            mem = memory_usage()[0]
            vdata = VirtualData([dmap, dmap, dmap])
            assert np.abs(mem - memory_usage()[0]) < 1

            # test consistency and efficacy of clear method
            vd = vdata[:, :]
            vdata.clear()
            assert np.array_equal(vd, vdata[:, :])
            mem = memory_usage()[0]
            vdata.clear()
            assert (mem - memory_usage()[0]) > 100

            # Delete all open references to file objects b4 closing tmp dir
            del dmap, vdata


# Test BaseData methods that work identically for all regular classes
class TestBaseData():

    # Allocate test-datasets for AnalogData, SpectralData, SpikeData and EventData objects
    nChannels = 10
    nSamples = 30
    nTrials = 5
    nFreqs = 15
    nSpikes = 50
    data = {}
    trl = {}

    # Generate 2D array simulating an AnalogData array
    data["AnalogData"] = np.arange(1, nChannels * nSamples + 1).reshape(nSamples, nChannels)
    trl["AnalogData"] = np.vstack([np.arange(0, nSamples, 5),
                                   np.arange(5, nSamples + 5, 5),
                                   np.ones((int(nSamples / 5), )),
                                   np.ones((int(nSamples / 5), )) * np.pi]).T

    # Generate a 4D array simulating a SpectralData array
    data["SpectralData"] = np.arange(1, nChannels * nSamples * nTrials * nFreqs + 1).reshape(nSamples, nTrials, nFreqs, nChannels)
    trl["SpectralData"] = trl["AnalogData"]

    # Use a fixed random number generator seed to simulate a 2D SpikeData array
    seed = np.random.RandomState(13)
    data["SpikeData"] = np.vstack([seed.choice(nSamples, size=nSpikes),
                                   seed.choice(nChannels, size=nSpikes),
                                   seed.choice(int(nChannels/2), size=nSpikes)]).T
    trl["SpikeData"] = trl["AnalogData"]

    # Use a simple binary trigger pattern to simulate EventData
    data["EventData"] = np.vstack([np.arange(0, nSamples, 5),
                                   np.zeros((int(nSamples / 5), ))]).T
    data["EventData"][1::2, 1] = 1
    trl["EventData"] = trl["AnalogData"]

    # Define data classes to be used in tests below
    classes = ["AnalogData", "SpectralData", "SpikeData", "EventData"]

    # Allocation to `data` property is tested with all members of `classes`
    def test_data_alloc(self):
        with tempfile.TemporaryDirectory() as tdir:
            fname = os.path.join(tdir, "dummy.npy")
            hname = os.path.join(tdir, "dummy.h5")

            for dclass in self.classes:
                # attempt allocation with random file
                with open(fname, "w") as f:
                    f.write("dummy")
                with pytest.raises(SPYValueError):
                    getattr(spd, dclass)(fname)

                # allocation with HDF5 file
                h5f = h5py.File(hname, mode="w")
                h5f.create_dataset("dummy", data=self.data[dclass])
                h5f.close()
                dummy = getattr(spd, dclass)(filename=hname)
                assert np.array_equal(dummy.data, self.data[dclass])
                assert dummy.filename == hname
                del dummy

                # allocation using HDF5 dataset directly
                dset = h5py.File(hname, mode="r+")["dummy"]
                dummy = getattr(spd, dclass)(dset)
                assert np.array_equal(dummy.data, self.data[dclass])
                assert dummy.mode == "r+", dummy.data.file.mode
                del dummy

                # allocation with memmaped npy file
                np.save(fname, self.data[dclass])
                dummy = getattr(spd, dclass)(filename=fname)
                assert np.array_equal(dummy.data, self.data[dclass])
                assert dummy.filename == fname
                del dummy

                # allocation using memmap directly
                mm = open_memmap(fname, mode="r")
                dummy = getattr(spd, dclass)(mm)
                assert np.array_equal(dummy.data, self.data[dclass])
                assert dummy.mode == "r"

                # attempt assigning data to read-only object
                with pytest.raises(SPYValueError):
                    dummy.data = self.data[dclass]

                # allocation using array + filename
                del dummy, mm
                dummy = getattr(spd, dclass)(self.data[dclass], fname)
                assert dummy.filename == fname
                assert np.array_equal(dummy.data, self.data[dclass])
                del dummy

                # attempt allocation using HDF5 dataset of wrong shape
                h5f = h5py.File(hname, mode="r+")
                del h5f["dummy"]
                dset = h5f.create_dataset("dummy", data=np.ones((self.nChannels,)))
                with pytest.raises(SPYValueError):
                    getattr(spd, dclass)(dset)

                # attempt allocation using illegal HDF5 container
                del h5f["dummy"]
                h5f.create_dataset("dummy1", data=self.data[dclass])
                h5f.create_dataset("dummy2", data=self.data[dclass])
                h5f.close()
                with pytest.raises(SPYValueError):
                    getattr(spd, dclass)(hname)

                # allocate with valid dataset of "illegal" container
                dset = h5py.File(hname, mode="r")["dummy1"]
                dummy = getattr(spd, dclass)(dset, fname)

                # attempt data access after backing file of dataset has been closed
                dset.file.close()
                with pytest.raises(SPYValueError):
                    dummy.data[0, ...]

                # attempt allocation with HDF5 dataset of closed container
                with pytest.raises(SPYValueError):
                    getattr(spd, dclass)(dset)

                # attempt allocation using memmap of wrong shape
                np.save(fname, np.ones((self.nChannels,)))
                with pytest.raises(SPYValueError):
                    getattr(spd, dclass)(open_memmap(fname))

    # Assignment of trialdefinition array is tested with all members of `classes`
    def test_trialdef(self):
        for dclass in self.classes:
            dummy = getattr(spd, dclass)(self.data[dclass],
                                         trialdefinition=self.trl[dclass])
            assert np.array_equal(dummy.sampleinfo, self.trl[dclass][:, :2])
            assert np.array_equal(dummy.t0, self.trl[dclass][:, 2])
            assert np.array_equal(dummy.trialinfo.flatten(), self.trl[dclass][:, 3])

    # Test ``clear`` with `AnalogData` only - method is independent from concrete data object
    @skip_in_vm
    def test_clear(self):
        with tempfile.TemporaryDirectory() as tdir:
            fname = os.path.join(tdir, "dummy.npy")
            data = np.ones((5000, 1000))  # ca. 38.2 MB
            np.save(fname, data)
            del data
            dmap = open_memmap(fname)

            # test consistency and efficacy of clear method
            dummy = AnalogData(dmap)
            data = np.array(dummy.data)
            dummy.clear()
            assert np.array_equal(data, dummy.data)
            mem = memory_usage()[0]
            dummy.clear()
            time.sleep(1)
            assert np.abs(mem - memory_usage()[0]) > 30

            # Delete all open references to file objects b4 closing tmp dir
            del dmap, dummy

    # Test ``_gen_filename`` with `AnalogData` only - method is independent from concrete data object
    def test_filename(self):
        # ensure we're salting sufficiently to create at least `numf`
        # distinct pseudo-random filenames in `__storage__`
        numf = 1000
        dummy = AnalogData()
        fnames = []
        for k in range(numf):
            fnames.append(dummy._gen_filename())
        assert np.unique(fnames).size == numf

    # Object copying is tested with all members of `classes`
    def test_copy(self):

        # test shallow copy of data arrays (hashes must match up, since
        # shallow copies are views in memory)
        for dclass in self.classes:
            dummy = getattr(spd, dclass)(self.data[dclass],
                                         trialdefinition=self.trl[dclass])
            dummy2 = dummy.copy()
            assert dummy.filename == dummy2.filename
            assert hash(str(dummy.data)) == hash(str(dummy2.data))
            assert hash(str(dummy.sampleinfo)) == hash(str(dummy2.sampleinfo))
            assert hash(str(dummy.t0)) == hash(str(dummy2.t0))
            assert hash(str(dummy.trialinfo)) == hash(str(dummy2.trialinfo))

        # test shallow + deep copies of memmaps + HDF5 containers
        with tempfile.TemporaryDirectory() as tdir:
            for dclass in self.classes:
                fname = os.path.join(tdir, "dummy.npy")
                hname = os.path.join(tdir, "dummy.h5")
                np.save(fname, self.data[dclass])
                h5f = h5py.File(hname, mode="w")
                h5f.create_dataset("dummy", data=self.data[dclass])
                h5f.close()
                mm = open_memmap(fname, mode="r")

                # hash-matching of shallow-copied memmap
                dummy = getattr(spd, dclass)(mm, trialdefinition=self.trl[dclass])
                dummy2 = dummy.copy()
                assert dummy.filename == dummy2.filename
                assert hash(str(dummy.data)) == hash(str(dummy2.data))
                assert hash(str(dummy.sampleinfo)) == hash(str(dummy2.sampleinfo))
                assert hash(str(dummy.t0)) == hash(str(dummy2.t0))
                assert hash(str(dummy.trialinfo)) == hash(str(dummy2.trialinfo))

                # test integrity of deep-copy
                dummy3 = dummy.copy(deep=True)
                assert dummy3.filename != dummy.filename
                assert np.array_equal(dummy.sampleinfo, dummy3.sampleinfo)
                assert np.array_equal(dummy.t0, dummy3.t0)
                assert np.array_equal(dummy.trialinfo, dummy3.trialinfo)
                assert np.array_equal(dummy.data, dummy3.data)

                # hash-matching of shallow-copied HDF5 dataset
                dummy = getattr(spd, dclass)(filename=hname, 
                                             trialdefinition=self.trl[dclass])
                dummy2 = dummy.copy()
                assert dummy.filename == dummy2.filename
                assert hash(str(dummy.data)) == hash(str(dummy2.data))
                assert hash(str(dummy.sampleinfo)) == hash(str(dummy2.sampleinfo))
                assert hash(str(dummy.t0)) == hash(str(dummy2.t0))
                assert hash(str(dummy.trialinfo)) == hash(str(dummy2.trialinfo))

                # test integrity of deep-copy
                dummy3 = dummy.copy(deep=True)
                assert dummy3.filename != dummy.filename
                assert np.array_equal(dummy.sampleinfo, dummy3.sampleinfo)
                assert np.array_equal(dummy.t0, dummy3.t0)
                assert np.array_equal(dummy.trialinfo, dummy3.trialinfo)
                assert np.array_equal(dummy.data, dummy3.data)

                # Delete all open references to file objects b4 closing tmp dir
                del mm, dummy, dummy2, dummy3

                # remove container for next round
                os.unlink(hname)


# Test Selector class
class TestSelector():

    # Set up "global" parameters for data objects to be tested
    nChannels = 10
    nSamples = 30
    nTrials = 5
    nFreqs = 15
    nSpikes = 50
    data = {}
    trl = {}

    # Prepare selector results for valid/invalid selections
    selectDict = {}
    selectDict["channel"] = {"valid": (["channel3", "channel1"], 
                                       [4, 2, 5], 
                                       range(0, 3), 
                                       range(5, 8), 
                                       slice(None), 
                                       slice(0, 5), 
                                       slice(7, None), 
                                       slice(2, 8),
                                       slice(0, 10, 2),
                                       slice(-2, None),
                                       [0, 1, 2, 3],  # contiguous list...
                                       [2, 3, 5]),  # non-contiguous list...
                             "result": ([2, 0],
                                        [4, 2, 5], 
                                        slice(0, 3, 1),
                                        slice(5, 8, 1), 
                                        slice(None, None, 1), 
                                        slice(0, 5, 1),
                                        slice(7, None, 1), 
                                        slice(2, 8, 1),
                                        slice(0, 10, 2),
                                        slice(-2, None, 1),
                                        slice(0, 4, 1),  # ...gets converted to slice
                                        [2, 3, 5]),  # stays as is
                             "invalid": (["channel200", "channel400"],
                                         ["invalid"],
                                         "wrongtype",
                                         range(0, 100), 
                                         slice(80, None),
                                         slice(-20, None),
                                         slice(-15, -2),
                                         slice(5, 1), 
                                         [40, 60, 80]),
                             "errors": (SPYValueError,
                                        SPYValueError,
                                        SPYTypeError,
                                        SPYValueError,
                                        SPYValueError,
                                        SPYValueError,
                                        SPYValueError,
                                        SPYValueError,
                                        SPYValueError)}
    
    selectDict["taper"] = {"valid": ([4, 2, 3], 
                                     range(0, 3), 
                                     range(2, 5), 
                                     slice(None), 
                                     slice(0, 5), 
                                     slice(3, None), 
                                     slice(2, 4),
                                     slice(0, 5, 2),
                                     slice(-2, None),
                                     [0, 1, 2, 3],  # contiguous list...
                                     [1, 3, 4]),  # non-contiguous list...
                           "result": ([4, 2, 3], 
                                      slice(0, 3, 1),
                                      slice(2, 5, 1), 
                                      slice(None, None, 1), 
                                      slice(0, 5, 1),
                                      slice(3, None, 1), 
                                      slice(2, 4, 1),
                                      slice(0, 5, 2),
                                      slice(-2, None, 1),
                                      slice(0, 4, 1),  # ...gets converted to slice
                                      [1, 3, 4]),  # stays as is
                           "invalid": (["taper_typo", "channel400"],
                                       "wrongtype",
                                       range(0, 100), 
                                       slice(80, None),
                                       slice(-20, None),
                                       slice(-15, -2),
                                       slice(5, 1), 
                                       [40, 60, 80]),
                           "errors": (SPYValueError,
                                      SPYTypeError,
                                      SPYValueError,
                                      SPYValueError,
                                      SPYValueError,
                                      SPYValueError,
                                      SPYValueError,
                                      SPYValueError)}
    
    selectDict["unit"] = {"valid": (["unit3", "unit1"],
                                    [4, 2, 3], 
                                    range(0, 3), 
                                    range(2, 5), 
                                    slice(None), 
                                    slice(0, 5), 
                                    slice(3, None), 
                                    slice(2, 4),
                                    slice(0, 5, 2),
                                    slice(-2, None),
                                    [0, 1, 2, 3],  # contiguous list...
                                    [1, 3, 4]),  # non-contiguous list...
                          "result": ([3, 1],
                                     [4, 2, 3], 
                                     slice(0, 3, 1),
                                     slice(2, 5, 1), 
                                     slice(None, None, 1), 
                                     slice(0, 5, 1),
                                     slice(3, None, 1), 
                                     slice(2, 4, 1),
                                     slice(0, 5, 2),
                                     slice(-2, None, 1),
                                     slice(0, 4, 1),  # ...gets converted to slice
                                     [1, 3, 4]),  # stays as is
                          "invalid": (["unit7", "unit77"],
                                      "wrongtype",
                                      range(0, 100), 
                                      slice(80, None),
                                      slice(-20, None),
                                      slice(-15, -2),
                                      slice(5, 1), 
                                      [40, 60, 80]),
                          "errors": (SPYValueError,
                                     SPYTypeError,
                                     SPYValueError,
                                     SPYValueError,
                                     SPYValueError,
                                     SPYValueError,
                                     SPYValueError,
                                     SPYValueError)}

    selectDict["eventid"] = {"valid": ([1, 0], 
                                       range(0, 2),
                                       range(1, 2), 
                                       slice(None), 
                                       slice(0, 2), 
                                       slice(1, None), 
                                       slice(0, 1),
                                       slice(-1, None),
                                       [0, 1]),  # contiguous list...
                             "result": ([1, 0], 
                                        slice(0, 2, 1),
                                        slice(1, 2, 1), 
                                        slice(None, None, 1), 
                                        slice(0, 2, 1),
                                        slice(1, None, 1), 
                                        slice(0, 1, 1),
                                        slice(-1, None, 1),
                                        slice(0, 2, 1)),  # ...gets converted to slice
                             "invalid": (["eventid", "eventid"],
                                         "wrongtype",
                                         range(0, 100), 
                                         slice(80, None),
                                         slice(-20, None),
                                         slice(-15, -2),
                                         slice(5, 1), 
                                         [40, 60, 80]),
                             "errors": (SPYValueError,
                                        SPYTypeError,
                                        SPYValueError,
                                        SPYValueError,
                                        SPYValueError,
                                        SPYValueError,
                                        SPYValueError,
                                        SPYValueError)}

    # in the general test routine, only check correct handling of invalid toi/toilim
    # and foi/foilim selections - valid selectors are strongly object dependent
    # and thus tested in separate methods below
    selectDict["toi"] = {"invalid": (["notnumeric", "stillnotnumeric"],
                                         "wrongtype",
                                         range(0, 100), 
                                         slice(80, None),
                                         slice(-40, None),
                                         slice(-40, -2),
                                         slice(5, 1), 
                                         [40, 60, 80]),
                             "errors": (SPYValueError,
                                        SPYTypeError,
                                        SPYValueError,
                                        SPYValueError,
                                        SPYValueError,
                                        SPYValueError,
                                        SPYValueError,
                                        SPYValueError)}
    
    # Generate 2D array simulating an AnalogData array
    data["AnalogData"] = np.arange(1, nChannels * nSamples + 1).reshape(nSamples, nChannels)
    trl["AnalogData"] = np.vstack([np.arange(0, nSamples, 5),
                                   np.arange(5, nSamples + 5, 5),
                                   np.ones((int(nSamples / 5), )),
                                   np.ones((int(nSamples / 5), )) * np.pi]).T

    # Generate a 4D array simulating a SpectralData array
    data["SpectralData"] = np.arange(1, nChannels * nSamples * nTrials * nFreqs + 1).reshape(nSamples, nTrials, nFreqs, nChannels)
    trl["SpectralData"] = trl["AnalogData"]

    # Use a fixed random number generator seed to simulate a 2D SpikeData array
    seed = np.random.RandomState(13)
    data["SpikeData"] = np.vstack([seed.choice(nSamples, size=nSpikes),
                                   seed.choice(np.arange(1, nChannels + 1), size=nSpikes), 
                                   seed.choice(int(nChannels/2), size=nSpikes)]).T
    trl["SpikeData"] = trl["AnalogData"]

    # Use a simple binary trigger pattern to simulate EventData
    data["EventData"] = np.vstack([np.arange(0, nSamples, 5),
                                   np.zeros((int(nSamples / 5), ))]).T
    data["EventData"][1::2, 1] = 1
    trl["EventData"] = trl["AnalogData"]
    
    # Define data classes to be used in tests below
    classes = ["AnalogData", "SpectralData", "SpikeData", "EventData"]
    
    
    def test_general(self):
        
        with pytest.raises(SPYTypeError):
            Selector(np.empty((3,)), {})
        with pytest.raises(SPYValueError):
            Selector(spd.AnalogData(), {})
        ang = AnalogData(data=self.data["AnalogData"], 
                         trialdefinition=self.trl["AnalogData"], 
                         samplerate=2.0)
        with pytest.raises(SPYTypeError):
            Selector(ang, ())
        with pytest.raises(SPYValueError):
            Selector(ang, {"wrongkey": [1]})
            
        for dclass in self.classes:
            dummy = getattr(spd, dclass)(data=self.data[dclass],
                                         trialdefinition=self.trl[dclass],
                                         samplerate=2.0)
            
            selection = Selector(dummy, {"trials": [3, 1]})
            assert selection.trials == [3, 1]
            with pytest.raises(SPYValueError):
                Selector(dummy, {"trials": [-1, 9]})
            
            for prop in ["channel", "taper", "unit", "eventid"]:
                if hasattr(dummy, prop):
                    expected = self.selectDict[prop]["result"]
                    for sk, sel in enumerate(self.selectDict[prop]["valid"]):
                        assert getattr(Selector(dummy, {prop + "s": sel}), prop) == expected[sk]
                    for ik, isel in enumerate(self.selectDict[prop]["invalid"]):
                        with pytest.raises(self.selectDict[prop]["errors"][ik]):
                            Selector(dummy, {prop + "s": isel})
                else:
                    with pytest.raises(SPYValueError):
                        Selector(dummy, {prop + "s": [0]})
                        
            if hasattr(dummy, "time") or hasattr(dummy, "trialtime"):
                for selection in ["toi"]:
                # for selection in ["toi", "toilim"]:
                    for ik, isel in enumerate(self.selectDict[selection]["invalid"]):
                        try:
                            with pytest.raises(self.selectDict[prop]["errors"][ik]):
                                Selector(dummy, {selection: isel})
                        except:
                            import pdb; pdb.set_trace()
            else:
                with pytest.raises(SPYValueError):
                    Selector(dummy, {"toi": [0]})
                with pytest.raises(SPYValueError):
                    Selector(dummy, {"toilim": [0]})
                
                        
    def test_continuous_toitoilim(self):
        # toi/toilim
        # 
        
    # selectDict["toi"] = {"valid": ([1.5, 1.], 
    #                                    np.arange(1, 2.5, 0.5),
    #                                    [1.5, 2., 2.5]], 
    #                                    slice(None), 
    #                                    np.array([2.5, 0.5, 1])),
    #                          "resultContinuous": ([2, 1], 
    #                                     slice(2, 4, 1),
    #                                     slice(2, 5, 1), 
    #                                     slice(None, None, 1),
    #                                     [4, 0, 2]),
    #                          "invalid": (["eventid", "eventid"],
    #                                      "wrongtype",
    #                                      range(0, 100), 
    #                                      slice(80, None),
    #                                      slice(-20, None),
    #                                      slice(-15, -2),
    #                                      slice(5, 1), 
    #                                      [40, 60, 80]),
    #                          "errors": (SPYValueError,
    #                                     SPYTypeError,
    #                                     SPYValueError,
    #                                     SPYValueError,
    #                                     SPYValueError,
    #                                     SPYValueError,
    #                                     SPYValueError,
    #                                     SPYValueError)}
        
        pass
    
    def test_spectral_foifoilim(self):
        # foi/foilim + toi (single points)
        pass

    def test_spike_toitoilim(self):
        # trlTime = list((np.arange(0, trl["SpikeData"][0, 1] - trl["SpikeData"][0, 0]) + trl["SpikeData"][0, 2])/2 )
        # toi/toilim
        
        pass

    def test_event_toitoilim(self):
        # toi/toilim
        pass
    