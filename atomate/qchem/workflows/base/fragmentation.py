# coding: utf-8

from __future__ import absolute_import, division, print_function, \
    unicode_literals

# This module defines a workflow that fragments a molecule and optimizes each fragment.
# It will most often be used in order to obtain the bond dissociation energies of a molecule.

from fireworks import Workflow
from atomate.qchem.fireworks.core import FrequencyFlatteningOptimizeFW, FragmentFW
from atomate.utils.utils import get_logger

__author__ = "Samuel Blau"
__copyright__ = "Copyright 2018, The Materials Project"
__version__ = "0.1"
__maintainer__ = "Samuel Blau"
__email__ = "samblau1@gmail.com"
__status__ = "Alpha"
__date__ = "6/22/18"
__credits__ = "Brandon Wood, Shyam Dwaraknath"

logger = get_logger(__name__)


def get_fragmentation_wf(molecule,
                         depth,
                         open_rings=True,
                         pcm_dielectric=None,
                         do_optimization=True,
                         max_cores=">>max_cores<<",
                         qchem_input_params=None,
                         name="FF then fragment",
                         qchem_cmd=">>qchem_cmd<<",
                         db_file=">>db_file<<",
                         check_db=True,
                         **kwargs):
    """

    Args:
        molecule (Molecule): input molecule to be fragmented.
        depth (int): The number of levels of iterative fragmentation to perform,
                     where each evel will include fragments obtained by breaking
                     one bond of a fragment one level up. If set to 0, instead
                     all possible fragments are generated using an alternative,
                     non-iterative scheme. 
        open_rings (bool): Whether or not to open any rings encountered during fragmentation.
                           Defaults to True. If true, any bond that fails to yield disconnected
                           graphs when broken is instead removed and the entire structure is 
                           optimized with OpenBabel in order to obtain a good initial guess for
                           an opened geometry that can then be put back into QChem to be
                           optimized without the ring just reforming.
        pcm_dielectric (float): The PCM dielectric constant.
        do_optimization (bool): Whether or not to optimize the given molecule
                                before fragmentation. Defaults to True.
        max_cores (int): Maximum number of cores to parallelize over.
                         Value obtained from the environment by default.
        qchem_input_params (dict): Specify kwargs for instantiating
                                   the input set parameters.
        qchem_cmd (str): Command to run QChem.
        db_file (str): path to file containing the database credentials.
        check_db (bool): Whether or not to check the database for equivalent
                         structures before adding new fragment fireworks.
                         Defaults to True.
        kwargs (keyword arguments): additional kwargs to be passed to Workflow

    Returns:
        Workflow with the following fireworks:

        Firework 1 : write QChem input for an FF optimization,
                     run FF_opt QCJob,
                     parse directory and insert into db,
                     pass relaxed molecule to fw_spec and on to fw2,

        Firework 2 : find all unique fragments of the optimized molecule
                     and add a frequency flattening optimize FW to the
                     workflow for each one

        Note that Firework 1 is only present if do_optimization=True.

    """

    qchem_input_params = qchem_input_params or {}
    if pcm_dielectric != None:
        qchem_input_params["pcm_dielectric"] = pcm_dielectric

    if do_optimization:
        # Optimize the original molecule
        fw1 = FrequencyFlatteningOptimizeFW(
            molecule=molecule,
            name="first FF",
            qchem_cmd=qchem_cmd,
            max_cores=max_cores,
            qchem_input_params=qchem_input_params,
            db_file=db_file)

        # Fragment the optimized molecule
        fw2 = FragmentFW(
            depth=depth,
            open_rings=open_rings,
            name="fragment and FF_opt",
            qchem_cmd=qchem_cmd,
            max_cores=max_cores,
            qchem_input_params=qchem_input_params,
            db_file=db_file,
            check_db=check_db,
            parents=fw1)
        fws = [fw1, fw2]

    else:
        # Fragment the given molecule
        fw1 = FragmentFW(
            molecule=molecule,
            depth=depth,
            open_rings=open_rings,
            name="fragment and FF_opt",
            qchem_cmd=qchem_cmd,
            max_cores=max_cores,
            qchem_input_params=qchem_input_params,
            db_file=db_file,
            check_db=check_db)
        fws = [fw1]

    wfname = "{}:{}".format(molecule.composition.reduced_formula, name)

    return Workflow(fws, name=wfname, **kwargs)
