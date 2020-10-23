.. ESM Pism documentation master file, created by
   sphinx-quickstart on Fri Oct 23 12:15:42 2020.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to ESM Pism's documentation!
====================================

This guide will help you to start using the ``PISM`` ice sheet model with ``ESM-Tools``
framework.

Once everything is set up, you can start ``PISM`` runs in the same manner you
would also start ``AWI-ESM``, ``MPI-ESM``, ``OpenIFS`` and similar models::

        $ esm_runscripts <experiment_config.yaml> -e <expid>

A summary video describing how to set up your ``experiment_config.yaml`` file is given below:

..  youtube:: I2PDO1AU0KU

In addition to `installing the standard ESM-Tools <www.example.com>`_, you
additionally need to install the PISM Plugin::

        $ pip install git+https://github.com/esm-tools-plugins/esm_pism

This gives you several new plugins for your job recipes:

* :py:mod:`esm_pism.plugin.pism_set_couplers`
* :py:mod:`esm_pism.plugin.pism_set_kv_pairs`
* :py:mod:`esm_pism.plugin.pism_set_flags`
* :py:mod:`esm_pism.plugin.pism_override_file`
* :py:mod:`esm_pism.plugin.pism_assemble_command`


The next section shows you how to set up your configuration file.


Table of Contents:
==================

.. toctree::
   :maxdepth: 2

   config
   api/modules



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

