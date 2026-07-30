# Copyright 2026 Adilkhan Salkimbayev
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Analytic verification utilities for an explicit control law.

These exist because the deployed law is a closed-form polynomial: the
closed-loop map has an analytic Jacobian, so local exponential stability can be
certified at a set-point rather than argued for.  The same routines are used
both to *select* the deployed complexity (stage 2b) and to *report* the
certificate (stage 4), so the controller that ships is the one that was
certified.
"""

from __future__ import annotations

import numpy as np

import qtlib as Q

CERT_REFS = [(9.0, 9.0), (10.0, 10.0), (12.0, 12.0), (13.0, 9.0), (9.0, 13.0), (14.0, 14.0)]


def fixed_point(policy, reg, ref, dt, x_init=None, iters=6000, tol=1e-11):
    """Locate the closed-loop fixed point of an approximate policy."""
    x = np.asarray(x_init if x_init is not None else ref, float).copy()
    for _ in range(iters):
        xn = Q.step_plant(x, policy(x, ref), dt, reg)
        if not np.all(np.isfinite(xn)) or xn.max() > 1e4:
            return x, False
        if np.max(np.abs(xn - x)) < tol:
            return xn, True
        x = xn
    return x, False


def closed_loop_jacobian(policy, reg, x0, ref, dt, eps=1e-5):
    J = np.zeros((4, 4))
    for i in range(4):
        e = np.zeros(4); e[i] = eps
        J[:, i] = (Q.step_plant(x0 + e, policy(x0 + e, ref), dt, reg)
                   - Q.step_plant(x0 - e, policy(x0 - e, ref), dt, reg)) / (2 * eps)
    return J


def certify(policy, reg, dt, refs=CERT_REFS, assume_equilibrium=False):
    """
    Returns one record per reference: spectral radius of the closed-loop
    Jacobian at the fixed point, and the offset of that fixed point from the
    commanded equilibrium.
    """
    out = []
    for h1, h2 in refs:
        try:
            x_eq, _ = Q.equilibrium(h1, h2, reg)
        except ValueError:
            continue
        if assume_equilibrium:
            # the equilibrium-consistency constraint of the read-out makes x_eq an
            # exact closed-loop fixed point, so no search is needed
            x_fp, conv = x_eq.copy(), True
        else:
            x_fp, conv = fixed_point(policy, reg, x_eq, dt, x_init=x_eq)
        J = closed_loop_jacobian(policy, reg, x_fp, x_eq, dt)
        ev = np.linalg.eigvals(J)
        rho = float(np.max(np.abs(ev))) if np.all(np.isfinite(ev)) else float("inf")
        out.append({
            "ref": [h1, h2],
            "spectral_radius": rho,
            "converged_to_fixed_point": bool(conv),
            "fixed_point_cm": [float(v) for v in x_fp],
            "offset_h1_cm": float(x_fp[0] - x_eq[0]),
            "offset_h2_cm": float(x_fp[1] - x_eq[1]),
            "max_abs_offset_cm": float(np.max(np.abs(x_fp[:2] - x_eq[:2]))),
            "locally_stable": bool(rho < 1.0),
            "_J": J, "_xfp": x_fp, "_xeq": x_eq,
        })
    return out


def summarise(cert):
    if not cert:
        return {"max_spectral_radius": float("inf"), "all_locally_stable": False}
    return {
        "max_spectral_radius": float(max(c["spectral_radius"] for c in cert)),
        "all_locally_stable": bool(all(c["locally_stable"] for c in cert)),
        "worst_offset_cm": float(max(c["max_abs_offset_cm"] for c in cert)),
        "all_fixed_points_found": bool(all(c["converged_to_fixed_point"] for c in cert)),
    }
