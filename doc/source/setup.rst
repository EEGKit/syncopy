Install Syncopy
===============

Syncopy can be installed using `conda <https://anaconda.org>`_:

We recommend to install SynCoPy into a new conda environment:

.. code-block:: bash

   conda create -y --name syncopy python=3.8
   conda activate syncopy
   conda install -y -c conda-forge esi-syncopy


If you're working on the ESI cluster installing Syncopy is only necessary if
you create your own Conda environment.

.. _install_acme:

Installing parallel processing engine ACME
--------------------------------------------

To harness the parallel processing capabilities of Syncopy
it is helpful to install `ACME <https://github.com/esi-neuroscience/acme>`_.

Again either via conda

.. code-block:: bash

    conda install -c conda-forge esi-acme

or pip

.. code-block:: bash

    pip install esi-acme

.. note::
   See :ref:`parallel` for details about parallel processing setup

Importing Syncopy
-----------------

To start using Syncopy you have to import it in your Python code:

.. code-block:: python

    import syncopy as spy

All :doc:`user-facing functions and classes <user/user_api>` can then be
accessed with the ``spy.`` prefix, e.g.

.. code-block:: python

    spy.load("~/testdata.spy")


To display your Syncopy version, run:

.. code-block:: python

    spy.__version__

.. _setup_env:

Setting Up Your Python Environment
----------------------------------

On the ESI cluster, ``/opt/conda/envs/syncopy`` provides a
pre-configured and tested Conda environment with the most recent Syncopy
version. This environment can be easily started using the `ESI JupyterHub
<https://jupyterhub.esi.local>`_

Syncopy makes heavy use of temporary files, which may become large (> 100 GB).
The storage location can be set using the `environmental variable
<https://linuxhint.com/bash-environment-variables/>`_ :envvar:`SPYTMPDIR`, which
by default points to your home directory:

.. code-block:: bash

    SPYTMPDIR=~/.spy

The performance of Syncopy strongly depends on the read and write speed in
this folder. On the ESI cluster, the variable is set to use the high performance
storage:

.. code-block:: bash

    SPYTMPDIR=/cs/home/$USER/.spy
