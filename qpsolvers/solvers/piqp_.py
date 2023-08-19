#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2016-2022 Stéphane Caron and the qpsolvers contributors.
#
# This file is part of qpsolvers.
#
# qpsolvers is free software: you can redistribute it and/or modify it under
# the terms of the GNU Lesser General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option) any
# later version.
#
# qpsolvers is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with qpsolvers. If not, see <http://www.gnu.org/licenses/>.

"""Solver interface for `PIQP`_.

.. _PIQP: https://github.com/PREDICT-EPFL/piqp
"""

from typing import Optional, Union

import numpy as np
import scipy.sparse as spa
import piqp

from ..conversions import ensure_sparse_matrices
from ..exceptions import ParamError, ProblemError
from ..problem import Problem
from ..solution import Solution


def __select_backend(backend: Optional[str], use_csc: bool):
    """Select backend function for PIQP.

    Parameters
    ----------
    backend :
        PIQP backend to use in ``[None, "dense", "sparse"]``. If ``None``
        (default), the backend is selected based on the type of ``P``.
    use_csc :
        If ``True``, use sparse matrices if the backend is not specified.

    Returns
    -------
    :
        Backend solve function.

    Raises
    ------
    ParamError
        If the required backend is not a valid PIQP backend.
    """
    if backend is None:
        return piqp.SparseSolver() if use_csc else piqp.DenseSolver()
    if backend == "dense":
        return piqp.DenseSolver()
    if backend == "sparse":
        return piqp.SparseSolver()
    raise ParamError(f'Unknown PIQP backend "{backend}')


def piqp_solve_problem(
    problem: Problem,
    verbose: bool = False,
    backend: Optional[str] = None,
    **kwargs,
) -> Solution:
    """Solve a quadratic program using PIQP.

    Parameters
    ----------
    problem :
        Quadratic program to solve.
    backend :
        PIQP backend to use in ``[None, "dense", "sparse"]``. If ``None``
        (default), the backend is selected based on the type of ``P``.
    verbose :
        Set to `True` to print out extra information.

    Returns
    -------
    :
        Solution to the QP returned by the solver.

    Raises
    ------
    ParamError
        If a warm-start value is given both in `initvals` and the `x` keyword
        argument.

    Notes
    -----
    All other keyword arguments are forwarded as options to PIQP. For
    instance, you can call ``piqp_solve_qp(P, q, G, h, eps_abs=1e-6)``.
    For a quick overview, the solver accepts the following settings:

    .. list-table::
       :widths: 30 70
       :header-rows: 1

       * - Name
         - Effect
       * - ``rho_init``
         - Initial value for the primal proximal penalty parameter rho.
       * - ``delta_init``
         - Initial value for the augmented lagrangian penalty parameter delta.
       * - ``eps_abs``
         - Absolute tolerance.
       * - ``eps_rel``
         - Relative tolerance.
       * - ``check_duality_gap``
         - Check terminal criterion on duality gap.
       * - ``eps_duality_gap_abs``
         - Absolute tolerance on duality gap.
       * - ``eps_duality_gap_rel``
         - Relative tolerance on duality gap.
       * - ``reg_lower_limit``
         - Lower limit for regularization.
       * - ``reg_finetune_lower_limit``
         - Fine tune lower limit regularization.
       * - ``reg_finetune_primal_update_threshold``
         - Threshold of number of no primal updates to transition to fine tune mode.
       * - ``reg_finetune_dual_update_threshold``
         - Threshold of number of no dual updates to transition to fine tune mode.
       * - ``max_iter``
         - Maximum number of iterations.
       * - ``max_factor_retires``
         - Maximum number of factorization retires before failure.
       * - ``preconditioner_scale_cost``
         - 	Scale cost in Ruiz preconditioner.
       * - ``preconditioner_iter``
         - Maximum of preconditioner iterations.
       * - ``tau``
         - Maximum interior point step length.
       * - ``iterative_refinement_always_enabled``
         - Always run iterative refinement and not only on factorization failure.
       * - ``iterative_refinement_eps_abs``
         - Iterative refinement absolute tolerance.
       * - ``iterative_refinement_eps_rel``
         - Iterative refinement relative tolerance.
       * - ``iterative_refinement_max_iter``
         - Maximum number of iterations for iterative refinement.
       * - ``iterative_refinement_min_improvement_rate``
         - Minimum improvement rate for iterative refinement.
       * - ``iterative_refinement_static_regularization_eps``
         - Static regularization for KKT system for iterative refinement.
       * - ``iterative_refinement_static_regularization_rel``
         - Static regularization w.r.t. the maximum abs diagonal term of KKT system.
       * - ``verbose``
         - Verbose printing.
       * - ``compute_timings``
         - Measure timing information internally.

    This list is not exhaustive. Check out the `solver documentation
    <https://predict-epfl.github.io/piqp/interfaces/settings>`__ for details.
    """
    P, q, G, h, A, b, lb, ub = problem.unpack()
    n: int = q.shape[0]
    use_csc: bool = (
        not isinstance(P, np.ndarray)
        or (G is not None and not isinstance(G, np.ndarray))
        or (A is not None and not isinstance(A, np.ndarray))
    )
    if use_csc == True:
        P, G, A = ensure_sparse_matrices(P, G, A)

    solver = __select_backend(backend, use_csc)
    solver.setup(P, q, A, b, G, h, lb, ub, verbose=verbose, **kwargs)
    status = solver.solve()
    success_status = piqp.PIQP_SOLVED

    solution = Solution(problem)
    solution.extras = {"info": solver.result.info}
    solution.found = status == success_status
    solution.x = solver.result.x
    solution.y = solver.result.y
    if lb is not None or ub is not None:
        solution.z = solver.result.z[:-n]
        solution.z_box = solver.result.z[-n:]
    else:  # lb is None and ub is None
        solution.z = solver.result.z
    return solution


def piqp_solve_qp(
    P: Union[np.ndarray, spa.csc_matrix],
    q: Union[np.ndarray, spa.csc_matrix],
    G: Optional[Union[np.ndarray, spa.csc_matrix]] = None,
    h: Optional[Union[np.ndarray, spa.csc_matrix]] = None,
    A: Optional[Union[np.ndarray, spa.csc_matrix]] = None,
    b: Optional[Union[np.ndarray, spa.csc_matrix]] = None,
    lb: Optional[Union[np.ndarray, spa.csc_matrix]] = None,
    ub: Optional[Union[np.ndarray, spa.csc_matrix]] = None,
    initvals: Optional[np.ndarray] = None,
    verbose: bool = False,
    backend: Optional[str] = None,
    **kwargs,
) -> Optional[np.ndarray]:
    r"""Solve a quadratic program using PIQP.

    The quadratic program is defined as:

    .. math::

        \begin{split}\begin{array}{ll}
        \underset{\mbox{minimize}}{x} &
            \frac{1}{2} x^T P x + q^T x \\
        \mbox{subject to}
            & G x \leq h                \\
            & A x = b                   \\
            & lb \leq x \leq ub
        \end{array}\end{split}

    It is solved using `PIQP
    <https://github.com/PREDICT-EPFL/piqp>`__.

    Parameters
    ----------
    P :
        Positive semidefinite cost matrix.
    q :
        Cost vector.
    G :
        Linear inequality constraint matrix.
    h :
        Linear inequality constraint vector.
    A :
        Linear equality constraint matrix.
    b :
        Linear equality constraint vector.
    lb :
        Lower bound constraint vector.
    ub :
        Upper bound constraint vector.
    initvals :
        Warm-start guess vector.
    backend :
        PIQP backend to use in ``[None, "dense", "sparse"]``. If ``None``
        (default), the backend is selected based on the type of ``P``.
    verbose :
        Set to `True` to print out extra information.

    Returns
    -------
    :
        Primal solution to the QP, if found, otherwise ``None``.
    """
    problem = Problem(P, q, G, h, A, b, lb, ub)
    solution = piqp_solve_problem(
        problem, initvals, verbose, backend, **kwargs
    )
    return solution.x if solution.found else None
