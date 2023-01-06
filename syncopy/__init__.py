# -*- coding: utf-8 -*-
#
# Main package initializer
#

# Builtin/3rd party package imports
import os
import sys
import subprocess
import socket
import getpass
import numpy as np
from hashlib import blake2b, sha1
import logging
import warnings
from importlib.metadata import version, PackageNotFoundError
import dask.distributed as dd

# Get package version: either via meta-information from egg or via latest git commit
try:
    __version__ = version("esi-syncopy")
except PackageNotFoundError:
    proc = subprocess.Popen("git describe --tags",
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            text=True, shell=True)
    out, err = proc.communicate()
    if proc.returncode != 0:
        proc = subprocess.Popen("git rev-parse HEAD:syncopy/__init__.py",
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                text=True, shell=True)
        out, err = proc.communicate()
        if proc.returncode != 0:
            msg = "\nSyncopy <core> WARNING: Package is not installed in site-packages nor cloned via git. " +\
                "Please consider obtaining SyNCoPy sources from supported channels. "
            print(msg)
            out = "-999"
    __version__ = out.rstrip("\n")

# --- Greeting ---

msg = f"""
Syncopy {__version__}

See https://syncopy.org for the online documentation.
For bug reports etc. please send an email to syncopy@esi-frankfurt.de
"""
# do not spam via worker imports
try:
    dd.get_client()
except ValueError:
    silence_file = os.path.expanduser("~/.spy/silentstartup")
    if os.getenv("SPYSILENTSTARTUP") is None and not os.path.isfile(silence_file):
        print(msg)

# Set up sensible printing options for NumPy arrays
np.set_printoptions(suppress=True, precision=4, linewidth=80)

# Check concurrent computing  setup (if acme is installed, dask is present too)
# Import `esi_cluster_setup` and `cluster_cleanup` from acme to make the routines
# available in the `spy` package namespace
try:
    from acme import esi_cluster_setup, cluster_cleanup
    __acme__ = True
except ImportError:
    __acme__ = False
    # ACME is critical on ESI infrastructure
    if socket.gethostname().startswith('esi-sv'):
        msg = "\nSyncopy <core> WARNING: Could not import Syncopy's parallel processing engine ACME. \n" +\
            "Please consider installing it via conda: \n" +\
            "\tconda install -c conda-forge esi-acme\n" +\
            "or using pip:\n" +\
            "\tpip install esi-acme"
        # do not spam via worker imports
        try:
            dd.get_client()
        except ValueError:
            print(msg)

# (Try to) set up visualization environment
try:
    import matplotlib.pyplot as plt
    import matplotlib.style as mplstyle
    import matplotlib as mpl
    __plt__ = True
except ImportError:
    __plt__ = False

# See if NWB is available
try:
    import pynwb
    __nwb__ = True
except ImportError:
    __nwb__ = False

# Set package-wide temp directory
csHome = "/cs/home/{}".format(getpass.getuser())
if os.environ.get("SPYTMPDIR"):
    __storage__ = os.path.abspath(os.path.expanduser(os.environ["SPYTMPDIR"]))
else:
    if os.path.exists(csHome):
        __storage__ = os.path.join(csHome, ".spy", "tmp_storage")
    else:
        __storage__ = os.path.join(os.path.expanduser("~"), ".spy", "tmp_storage")

# Setup logging.
if os.environ.get("SPYLOGDIR"):
    __logdir__ = os.path.abspath(os.path.expanduser(os.environ["SPYLOGDIR"]))
else:
    if os.path.exists(csHome):
        __logdir__ = os.path.join(csHome, ".spy", "logs")
    else:
        __logdir__ = os.path.join(os.path.expanduser("~"), ".spy", "logs")

loglevel = os.getenv("SPYLOGLEVEL", "WARNING")
numeric_level = getattr(logging, loglevel.upper(), None)
if not isinstance(numeric_level, int):  # An invalid string was set as the env variable, default to WARNING.
    warnings.warn("Invalid log level set in environment variable 'SPYLOGLEVEL', ignoring and using WARNING instead. Hint: Set one of 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'.")
    loglevel = "WARNING"

spy_logger = logging.getLogger('syncopy')
spy_logger.setLevel(loglevel)

# Log to per-host files in parallel code by default.
host = socket.gethostname()
spy_parallel_logger = logging.getLogger("syncopy_" + host)

fh = logging.FileHandler(os.path.join(__logdir__, f'syncopy_{host}.log'))
spy_parallel_logger.addHandler(fh)


# Set upper bound for temp directory size (in GB)
__storagelimit__ = 10

# Establish ID and log-file for current session
__sessionid__ = blake2b(digest_size=2, salt=os.urandom(blake2b.SALT_SIZE)).hexdigest()
__sessionfile__ = os.path.join(__storage__, "session_{}.id".format(__sessionid__))

# Set max. no. of lines for traceback info shown in prompt
__tbcount__ = 5

# Set checksum algorithm to be used
__checksum_algorithm__ = sha1

# Fill up namespace
from . import (
    shared,
    io,
    datatype)

from .shared import *
from .io import *
from .datatype import *
from .specest import *
from .nwanalysis import *
from .statistics import *
from .plotting import *
from .preproc import *

# Register session
__session__ = datatype.base_data.SessionLogger()

# Override default traceback (differentiate b/w Jupyter/iPython and regular Python)
from .shared.errors import SPYExceptionHandler
try:
    ipy = get_ipython()
    import IPython
    IPython.core.interactiveshell.InteractiveShell.showtraceback = SPYExceptionHandler
    IPython.core.interactiveshell.InteractiveShell.showsyntaxerror = SPYExceptionHandler
    sys.excepthook = SPYExceptionHandler
except:
    sys.excepthook = SPYExceptionHandler

# Manage user-exposed namespace imports
__all__ = []
__all__.extend(datatype.__all__)
__all__.extend(io.__all__)
__all__.extend(shared.__all__)
__all__.extend(specest.__all__)
__all__.extend(nwanalysis.__all__)
__all__.extend(statistics.__all__)
__all__.extend(plotting.__all__)
__all__.extend(preproc.__all__)
