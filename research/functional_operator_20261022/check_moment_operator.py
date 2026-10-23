"""Exact designed checks; no biological assay input or statistical fits."""
from fractions import Fraction as F
import json
from pathlib import Path


def moment(atoms, order):
    return sum((weight * z**order for z, weight in atoms), F(0))


def bounds(m1, m2):
    assert 0 <= m1 <= 1 and m1*m1 <= m2 <= m1
    if m1 in (0, 1):
        return m1, m1
    b = m2 / m1
    a = (m1-m2) / (1-m1)
    lower = m2**3 / m1**2
    upper = ((1+2*a+3*a*a)*m2 - 2*a*(1+a)**2*m1
             + a*a*(1+2*a))
    return lower, upper


def text_pair(pair):
    return [str(value) for value in pair]


def one_anchor_certificate(relative1, relative2, pool_survival1, i, j):
    """Conservative exact bound on m_i(4)-m_j(4), with unknown shared c2."""
    m1s = [value*pool_survival1 for value in relative1]
    c2_interval = (max(m1*m1/r2 for m1, r2 in zip(m1s, relative2)),
                   min(m1/r2 for m1, r2 in zip(m1s, relative2)))
    assert c2_interval[0] <= c2_interval[1]
    lower_i = bounds(m1s[i], relative2[i]*c2_interval[0])[0]
    upper_j = bounds(m1s[j], relative2[j]*c2_interval[1])[1]
    return c2_interval, lower_i-upper_j


def main():
    checks = []
    # Same first two absolute moments, opposite fourth-moment ranks on swap.
    left = [(F(0), F(1, 3)), (F(3, 4), F(2, 3))]
    right = [(F(1, 4), F(2, 3)), (F(1), F(1, 3))]
    assert [moment(left, j) for j in (1, 2)] == [F(1, 2), F(3, 8)]
    assert [moment(right, j) for j in (1, 2)] == [F(1, 2), F(3, 8)]
    assert moment(left, 4) == F(27, 128)
    assert moment(right, 4) == F(43, 128)
    checks.append("same early moments permit a terminal rank reversal")
    assert bounds(F(1, 2), F(3, 8)) == (F(27, 128), F(43, 128))
    checks.append("sharp lower and upper moment witnesses attained")

    # Verify the two dual polynomial identities on exact rational grid points.
    for numerator in range(17):
        z = F(numerator, 16)
        b = F(3, 4)
        assert z**4-3*b*b*z*z+2*b**3*z == z*(z-b)**2*(z+2*b)
        a = F(1, 4)
        upper_poly = ((1+2*a+3*a*a)*z*z - 2*a*(1+a)**2*z
                      + a*a*(1+2*a))
        assert upper_poly-z**4 == (1-z)*(z-a)**2*(z+1+2*a)
        assert z*(z-b)**2*(z+2*b) >= 0
        assert (1-z)*(z-a)**2*(z+1+2*a) >= 0
    checks.append("34 polynomial identities and 34 nonnegative evaluations")

    # Exact rank certificate from anchored moments, not fitted latent mechanism.
    homogeneous = [(F(3, 5), F(1))]
    assert bounds(moment(homogeneous, 1), moment(homogeneous, 2)) == (F(81, 625), F(81, 625))
    assert bounds(F(1, 2), F(3, 8))[0] > F(81, 625)
    assert F(1, 2)**4 < F(3, 5)**4
    checks.append("two-moment rank certificate correct where first-moment homogeneous extrapolation reverses")

    # Unknown shared pooled normalizers do not become absolute moments.
    rows = [left, homogeneous]
    pooled = {}
    for e in (1, 2, 4):
        raw = [moment(row, e) for row in rows]
        normalizer = sum(raw, F(0))/len(raw)
        pooled[e] = [value/normalizer for value in raw]
        # Add a common instantly killed component: unchanged pooled evidence.
        thinned = [[(z, w*F(1, 3)) for z, w in row] + [(F(0), F(2, 3))] for row in rows]
        new_raw = [moment(row, e) for row in thinned]
        new_normalizer = sum(new_raw, F(0))/len(new_raw)
        assert pooled[e] == [value/new_normalizer for value in new_raw]
        assert new_raw == [value/3 for value in raw]
    checks.append("three pooled panels invariant under shared susceptibility dilution; absolute survival changes")

    # One total-pool survival anchor at exposure1 fixes every m1. The observed
    # relative exposure2 panel then leaves only ONE shared normalization scalar.
    # Near-unit survival in one gene constrains that scalar for all other genes.
    m1s = [F(1, 2), F(3, 5), F(99, 100)]
    m2s = [F(3, 8), F(9, 25), F(9801, 10000)]
    c1 = sum(m1s)/3
    c2 = sum(m2s)/3
    r1s = [value/c1 for value in m1s]
    r2s = [value/c2 for value in m2s]
    recovered_m1s = [value*c1 for value in r1s]
    assert recovered_m1s == m1s
    gauge = (max(m1*m1/r2 for m1, r2 in zip(m1s, r2s)),
             min(m1/r2 for m1, r2 in zip(m1s, r2s)))
    assert gauge == (F(5717, 10000), F(5717, 9900))
    a_lower = bounds(m1s[0], r2s[0]*gauge[0])[0]
    b_upper = bounds(m1s[1], r2s[1]*gauge[1])[1]
    assert a_lower == F(27, 128) and b_upper == F(753, 5324)
    assert a_lower > b_upper
    assert one_anchor_certificate(r1s, r2s, c1, 0, 1) == (gauge, a_lower-b_upper)
    checks.append("one pooled exposure1 anchor plus relative exposure2 certifies another-gene terminal rank")

    # The identical unanchored relative observations allow the opposite rank.
    # Choose a different shared gauge at each observed exposure, then select
    # valid sharp extremizers at exposure4. These are probability measures.
    other_m1s = [value/10 for value in m1s]
    other_m2s = [value/50 for value in m2s]
    assert [value/(c1/10) for value in other_m1s] == r1s
    assert [value/(c2/50) for value in other_m2s] == r2s
    for m1, m2 in zip(other_m1s, other_m2s):
        assert m1*m1 <= m2 <= m1
    other_a = bounds(other_m1s[0], other_m2s[0])[0]
    other_b = bounds(other_m1s[1], other_m2s[1])[1]
    assert other_a < other_b
    checks.append("same two relative panels without global anchor admit reverse terminal ranking")

    # Full-information conventional generalized moment optimization has exactly
    # the same sharp bounds: the two dual polynomials plus attaining distributions
    # certify the optimum without trusting a numerical solver.
    conventional = (moment(left, 4), moment(right, 4))
    proposed = bounds(F(1, 2), F(3, 8))
    assert conventional == proposed
    checks.append("nearest sharp ordinary generalized-moment counterpart matches exactly")
    result = {
        "status": "PASS", "checks": checks,
        "anchored_interval": text_pair(proposed),
        "homogeneous_reference_m4": str(F(81, 625)),
        "one_anchor_c2_interval": text_pair(gauge),
        "one_anchor_rank_separation": text_pair((a_lower, b_upper)),
        "unanchored_opposite_rank": text_pair((other_a, other_b)),
        "unanchored_absolute_identification": False,
        "biological_scalars_decoded": 0, "predictive_fits": 0,
        "claim": "Designed exact witnesses only; no empirical functional or novelty gain.",
    }
    out = Path("log/20261022/operator_renewal/functional/synthetic_result.json")
    out.write_text(json.dumps(result, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
