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
Stage 4b -- numerical check of the two structural properties claimed for the
policy parameterisation of policyform.py.

(P1) At a reachable set-point the commanded input equals the analytic
     steady-state input exactly, so the set-point is an exact closed-loop fixed
     point.
(P2) The closed-loop linearisation at that fixed point equals A(r) - BK, and is
     therefore independent of the learned term.

Both are claimed to hold *for any learned term whatsoever*.  The check
substitutes, in place of the trained read-out: the zero function, several draws
of random coefficients on the deployed support, and the deployed law itself.  If
the properties hold, all of them must give bit-comparable spectral radii and a
residual |u(x_eq) - u_eq| at machine precision.

Outputs results/invariance.json
"""

from __future__ import annotations

import json
import os

import numpy as np

import controllers as C
import policyform as PF
import qtlib as Q
import symbolic as SY
import verify as V

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results")
MODELS = os.path.join(HERE, "models")
DT = 0.1


def main():
    rng = np.random.default_rng(0)
    out = {}
    for regime, reg in (("MP", Q.MP), ("NMP", Q.NMP)):
        law = C.SymbolicLaw(regime)
        variants = {"zero": lambda p: np.zeros((len(p), 2))}
        for t in range(3):
            scale = 10.0 ** t
            cs = [rng.normal(0, scale, len(law.sup[j])) for j in (0, 1)]

            def f(p, cs=cs, law=law):
                return np.stack([SY.design(p, law.sup[j]) @ cs[j] for j in (0, 1)], axis=1)
            variants[f"random(sigma={scale:g})"] = f

        rows = {}
        for name, f in variants.items():
            def pol(x, ref, f=f, regime=regime):
                p = Q.features(x, ref)
                return PF.decode(f(p), x, ref, regime).ravel()
            s = V.summarise(V.certify(pol, reg, DT, assume_equilibrium=True))
            res = []
            for h1, h2 in V.CERT_REFS:
                x_eq, u_eq = Q.equilibrium(h1, h2, reg)
                res.append(float(np.max(np.abs(pol(x_eq, x_eq) - u_eq))))
            rows[name] = {"max_spectral_radius": s["max_spectral_radius"],
                          "all_locally_stable": s["all_locally_stable"],
                          "max_abs_u_minus_ueq_V": float(max(res))}

        # the deployed law itself
        s = V.summarise(V.certify(law, reg, DT, assume_equilibrium=True))
        res = []
        for h1, h2 in V.CERT_REFS:
            x_eq, u_eq = Q.equilibrium(h1, h2, reg)
            res.append(float(np.max(np.abs(law(x_eq, x_eq) - u_eq))))
        rows["deployed law"] = {"max_spectral_radius": s["max_spectral_radius"],
                                "all_locally_stable": s["all_locally_stable"],
                                "max_abs_u_minus_ueq_V": float(max(res))}

        rhos = [v["max_spectral_radius"] for v in rows.values()]
        out[regime] = {
            "variants": rows,
            "spectral_radius_spread": float(max(rhos) - min(rhos)),
            "P1_holds": bool(max(v["max_abs_u_minus_ueq_V"] for v in rows.values()) < 1e-9),
            "P2_holds": bool(max(rhos) - min(rhos) < 1e-9 and all(
                v["all_locally_stable"] for v in rows.values())),
            "lqr_gain": PF.lqr_gain(regime).tolist(),
        }
        print(f"=== {regime} ===")
        for k, v in rows.items():
            print(f"  {k:22s} rho={v['max_spectral_radius']:.6f} "
                  f"stable={v['all_locally_stable']} "
                  f"|u-u_eq|={v['max_abs_u_minus_ueq_V']:.2e}")
        print(f"  P1 {out[regime]['P1_holds']}  P2 {out[regime]['P2_holds']} "
              f"(rho spread {out[regime]['spectral_radius_spread']:.2e})")

    with open(os.path.join(RES, "invariance.json"), "w") as f:
        json.dump(out, f, indent=2)
    print("wrote", os.path.join(RES, "invariance.json"))


if __name__ == "__main__":
    main()
