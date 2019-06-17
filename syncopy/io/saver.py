# -*- coding: utf-8 -*-
#
# Manager for writing various file formats
#
# Created: 2019-02-05 12:55:36
# Last modified by: Stefan Fuertinger [stefan.fuertinger@esi-frankfurt.de]
# Last modification time: <2019-05-09 13:55:11>

# Local imports
from syncopy.shared.errors import SPYTypeError
from syncopy.io import save_spy

__all__ = ["save_data"]

supportedFormats = ['.spy'] #: 

def save_data(out_name, out, filetype=None, **kwargs):
    """Save data object to disk

    Parameters
    ----------
        out_name : str
            filename path to be used for storing data object
        out : children of :class:`syncopy.datatype.base_data.BaseData`
            Syncopy data object to be store on disk
        filetype : str
            filetype for storing data on disk

    Supported file formats for storing data are

    .. autodata:: syncopy.io.saver.supportedFormats        

    """

    # Parsing of `out_name` and `out` happens in the actual writing routines,
    # only check `filetype` in here
    if filetype is not None:
        if not isinstance(filetype, str):
            raise SPYTypeError(filetype, varname="filetype", expected="str")

    # Depending on specified output file-type, call appropriate writing routine
    if filetype is None or filetype in supportedFormats:
        save_spy(out_name, out, **kwargs)
    elif filetype == "matlab" or filetype in ".mat":
        raise NotImplementedError("Coming soon...")
