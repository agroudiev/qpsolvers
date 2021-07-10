#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2016-2021 Stéphane Caron <stephane.caron@normalesup.org>
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

"""Main function to solve quadratic programs."""

from typing import Optional

from numpy import eye, hstack, ones, ndarray, vstack, zeros

from .check_problem_constraints import check_problem_constraints
from .concatenate_bounds import concatenate_bounds
from .exceptions import SolverNotFound
from .solvers import dense_solvers
from .solvers import solve_function
from .typing import Matrix, Vector


def solve_qp(
    P: Matrix,
    q: Vector,
    G: Optional[Matrix] = None,
    h: Optional[Vector] = None,
    A: Optional[Matrix] = None,
    b: Optional[Vector] = None,
    lb: Optional[Vector] = None,
    ub: Optional[Vector] = None,
    solver: str = "quadprog",
    initvals: Optional[Vector] = None,
    sym_proj: bool = False,
    verbose: bool = False,
    **kwargs,
) -> Optional[ndarray]:
    """
    Solve a Quadratic Program defined as:

    .. math::

        \\begin{split}\\begin{array}{ll}
            \\mbox{minimize} &
                \\frac{1}{2} x^T P x + q^T x \\\\
            \\mbox{subject to}
                & G x \\leq h                \\\\
                & A x = b                    \\\\
                & lb \\leq x \\leq ub
        \\end{array}\\end{split}

    using one of the available QP solvers.

    Parameters
    ----------
    P : numpy.ndarray, scipy.sparse.csc_matrix or cvxopt.spmatrix
        Symmetric quadratic-cost matrix (most solvers require it to be definite
        as well).
    q : numpy.ndarray
        Quadratic-cost vector.
    G : numpy.ndarray, scipy.sparse.csc_matrix or cvxopt.spmatrix, optional
        Linear inequality matrix.
    h : numpy.ndarray, optional
        Linear inequality vector.
    A : numpy.ndarray, scipy.sparse.csc_matrix or cvxopt.spmatrix, optional
        Linear equality matrix.
    b : numpy.ndarray, optional
        Linear equality vector.
    lb: numpy.ndarray, scipy.sparse.csc_matrix or cvxopt.spmatrix, optional
        Lower bound constraint vector.
    ub: numpy.ndarray, scipy.sparse.csc_matrix or cvxopt.spmatrix, optional
        Upper bound constraint vector.
    solver : string, optional
        Name of the QP solver, to choose in ``qpsolvers.available_solvers``.
    initvals : numpy.ndarray, optional
        Vector of initial `x` values used to warm-start the solver.
    sym_proj : bool, optional
        Set to `True` when the `P` matrix provided is not symmetric.
    verbose : bool, optional
        Set to `True` to print out extra information.

    Returns
    -------
    x : array or None
        Optimal solution if found, None otherwise.

    Raises
    ------
    ValueError
        If the problem is not correctly defined.

    Note
    ----
    Extra keyword arguments given to this function are forwarded to the
    underlying solvers. For example, OSQP has a setting `eps_abs` which we can
    provide by ``solve_qp(P, q, G, h, solver='osqp', eps_abs=1e-4)``.

    Notes
    -----
    In quadratic programming, the matrix `P` should be symmetric. Many solvers
    (including CVXOPT, OSQP and quadprog) leverage this property and may return
    erroneous results when it is not the case. You can set ``sym_proj=True`` to
    project `P` on its symmetric part, at the cost of some computation time.
    """
    if sym_proj:
        P = 0.5 * (P + P.transpose())
    if isinstance(A, ndarray) and A.ndim == 1:
        A = A.reshape((1, A.shape[0]))
    if isinstance(G, ndarray) and G.ndim == 1:
        G = G.reshape((1, G.shape[0]))
    check_problem_constraints(G, h, A, b)
    G, h = concatenate_bounds(G, h, lb, ub)
    kwargs["initvals"] = initvals
    kwargs["verbose"] = verbose
    try:
        return solve_function[solver](P, q, G, h, A, b, **kwargs)
    except KeyError as e:
        raise SolverNotFound(f"solver '{solver}' is not available") from e


def solve_safer_qp(
    P: ndarray,
    q: ndarray,
    G: ndarray,
    h: ndarray,
    sw: float,
    reg: float = 1e-8,
    solver: str = "mosek",
    initvals: Optional[ndarray] = None,
    sym_proj: bool = False,
) -> Optional[ndarray]:
    """
    Solve the Quadratic Program defined as:

    .. math::

        \\begin{split}\\begin{array}{ll}
            \\mbox{minimize} &
                \\frac{1}{2} x^T P x + q^T x +
                \\frac{1}{2} \\mathit{reg} \\|s\\|^2 - \\mathit{sw} \\1^T s
                \\\\
            \\mbox{subject to}
                & G x \\leq h
        \\end{array}\\end{split}

    Slack variables `s` are increased by an additional term in the cost
    function, so that the solution of this "safer" QP is further inside the
    constraint region.

    Parameters
    ----------
    P : numpy.ndarray
        Symmetric quadratic-cost matrix.
    q : numpy.ndarray
        Quadratic-cost vector.
    G : numpy.ndarray
        Linear inequality matrix.
    h : numpy.ndarray
        Linear inequality vector.
    sw : float
        Weight of the linear cost on slack variables. Higher values bring the
        solution further inside the constraint region but override the
        minimization of the original objective.
    reg : float, optional
        Regularization term :math:`(1/2) \\epsilon` in the cost function. Set
        this parameter as small as possible (e.g. 1e-8), and increase it in
        case of numerical instability.
    solver : string, optional
        Name of the QP solver to use (default is MOSEK).
    initvals : numpy.ndarray, optional
        Vector of initial `x` values used to warm-start the solver.
    sym_proj : bool, optional
        Set to `True` when the `P` matrix provided is not symmetric.

    Returns
    -------
    x : numpy.ndarray, shape=(n,)
        Optimal solution to the relaxed QP, if found.

    Raises
    ------
    ValueError
        If the QP is not feasible.

    Note
    ----
    This is a legacy function.

    Notes
    -----
    This method can be found in the Inverse Kinematics resolution of Nozawa et
    al. (Humanoids 2016). It also appears in earlier works such as the
    "optimally safe" tension distribution algorithm of Borgstrom et al. (IEEE
    Transactions on Robotics, 2009).
    """
    assert solver in dense_solvers, "only available for dense solvers, for now"
    n, m = P.shape[0], G.shape[0]
    E, Z = eye(m), zeros((m, n))
    P2 = vstack([hstack([P, Z.T]), hstack([Z, reg * eye(m)])])
    q2 = hstack([q, -sw * ones(m)])
    G2 = hstack([Z, E])
    h2 = zeros(m)
    A2 = hstack([G, -E])
    b2 = h
    x = solve_qp(
        P2,
        q2,
        G2,
        h2,
        A2,
        b2,
        solver=solver,
        initvals=initvals,
        sym_proj=sym_proj,
    )
    if x is None:
        return None
    return x[:n]
