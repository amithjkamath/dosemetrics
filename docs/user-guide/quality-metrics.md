# Metric Framework

DoseMetrics separates metrics by the quantity they measure and by whether they
need one dose distribution or a reference/evaluated pair.

- A **reference-free** function begins with `compute_*` and characterizes one
  dose distribution, one structure, or one gamma map.
- A **reference-based** function begins with `compare_*` and accepts a
  reference followed by an evaluated result.

Named plan comparisons are imported directly from `dosemetrics.metrics`:

```python
from dosemetrics.metrics import compare_ptv_dose

distance_gy = compare_ptv_dose(reference, evaluated, ptv)
```

## Metric classes

The clinical metric documentation is divided into three detailed classes:

- [DVH metrics](dvh-analysis.md) describe dose-volume behaviour, point
  statistics, biological summaries, and agreement between DVHs.
- [Conformity metrics](conformity-metrics.md) describe target coverage,
  prescription-isodose overlap, and dose spillage.
- [Homogeneity metrics](homogeneity-metrics.md) describe dose uniformity inside
  a target and dose falloff outside it.

Global voxel agreement, gamma analysis, geometric overlap, and constraint
agreement are summarized below and documented by their exact signatures in the
[Metrics API](../api/metrics.md).

## Classification table

The table includes both single-plan quantities and their between-plan
counterparts. The **Reference use** column is determined by the actual function
signature, not by the clinical class.

| Class | Metric | API | Reference use | Unit | Better |
|---|---|---|---|---|---|
| DVH | Cumulative DVH | `dvh.compute_dvh` | Reference-free | % versus Gy | Context-dependent |
| DVH | Dose at volume, $D_x$ | `dvh.compute_dose_at_volume` | Reference-free | Gy | Context-dependent |
| DVH | Volume at dose, $V_x$ | `dvh.compute_volume_at_dose` | Reference-free | % | Context-dependent |
| DVH | Dose statistics | `dvh.compute_dose_statistics` | Reference-free | Gy | Context-dependent |
| DVH | Equivalent uniform dose | `dvh.compute_equivalent_uniform_dose` | Reference-free | Gy | Context-dependent |
| DVH | DVH area under curve | `dvh.compute_dvh_auc` | Reference-free | Normalized or Gy | Context-dependent |
| DVH | PTV mean-dose distance | `compare_ptv_dose` | Reference-based | Gy | Lower |
| DVH | OAR DVH AUC distance | `compare_oar_dvh_auc` | Reference-based | Gy | Lower |
| DVH | OpenKBP DVH Score | `compare_dvh_score` | Reference-based | Gy | Lower |
| Conformity | Coverage | `conformity.compute_coverage` | Reference-free | Fraction | Higher |
| Conformity | Spillage | `conformity.compute_spillage` | Reference-free | Fraction | Lower |
| Conformity | Conformity index | `conformity.compute_conformity_index` | Reference-free | Dimensionless | Higher |
| Conformity | Conformation number | `conformity.compute_conformity_number` | Reference-free | Dimensionless | Higher |
| Conformity | Paddick conformity index | `conformity.compute_paddick_conformity_index` | Reference-free | Dimensionless | Higher |
| Conformity | RTOG conformity index | `conformity.compute_rtog_conformity_index` | Reference-free | Dimensionless | Near 1 |
| Conformity | Prescription-dose MAE | `conformity.compute_prescription_mae` | Reference-free | Gy | Lower |
| Conformity | Paddick CI distance | `compare_paddick_conformity_index` | Reference-based | Dimensionless | Lower |
| Homogeneity | Homogeneity index | `homogeneity.compute_homogeneity_index` | Reference-free | Dimensionless | Lower |
| Homogeneity | Gradient index | `homogeneity.compute_gradient_index` | Reference-free | Dimensionless | Lower |
| Homogeneity | Dose coefficient of variation | `homogeneity.compute_dose_homogeneity` | Reference-free | Dimensionless | Lower |
| Homogeneity | Uniformity index | `homogeneity.compute_uniformity_index` | Reference-free | Dimensionless | Higher |
| Homogeneity | Homogeneity index distance | `compare_homogeneity_index` | Reference-based | Dimensionless | Lower |
| Homogeneity | Paddick gradient index distance | `compare_paddick_gradient_index` | Reference-based | Dimensionless | Lower |
| Global voxel agreement | Body-mask RMSE | `compare_body_rmse` | Reference-based | Gy | Lower |
| Global voxel agreement | Gamma passing rate | `compare_gamma` | Reference-based | % | Higher |
| Constraint agreement | OAR constraint disagreement | `compare_oar_constraints` | Reference-based | Fraction | Lower |
| Error tail | Maximum absolute error | `dose_comparison.compare_max_error` | Reference-based | Gy | Lower |
| Error tail | Absolute-error percentile | `dose_comparison.compare_error_percentile` | Reference-based | Gy | Lower |
| Error tail | Tail mean absolute error (CVaR) | `dose_comparison.compare_tail_error` | Reference-based | Gy | Lower |
| Error tail | Isolated extrema count | `dose_comparison.compute_isolated_extrema` | Reference-free | Voxels | Lower |

## Pairing single-plan and comparison metrics

These pairs make the distinction explicit:

| Reference-free quantity | Reference-based distance or agreement |
|---|---|
| `dvh.compute_mean_dose(dose, ptv)` | `compare_ptv_dose(reference, evaluated, ptv)` |
| `dvh.compute_dvh_auc(dose, oar)` | `compare_oar_dvh_auc(reference, evaluated, oar)` |
| `conformity.compute_paddick_conformity_index(dose, ptv, rx)` | `compare_paddick_conformity_index(reference, evaluated, ptv, rx)` |
| `homogeneity.compute_homogeneity_index(dose, ptv)` | `compare_homogeneity_index(reference, evaluated, ptv)` |
| `homogeneity.compute_gradient_index(dose, ptv, rx)` | `compare_paddick_gradient_index(reference, evaluated, rx)` |

## Global voxel agreement

### Body-mask RMSE

**Reference-based** · `compare_body_rmse` · Gy · lower is better.

![Body-mask RMSE](../images/rmse-error.png)
*The voxel errors are squared, averaged over the body mask, and square-rooted.*

$$
\mathrm{RMSE}
=\sqrt{\frac{1}{N}\sum_{i=1}^{N}
\left(D_{\mathrm{evaluated},i}-D_{\mathrm{reference},i}\right)^2}.
$$

```python
from dosemetrics.metrics import compare_body_rmse

rmse_gy = compare_body_rmse(reference, evaluated, body)
```

### Gamma passing rate

**Reference-based** · `compare_gamma` · percent · higher is better.

![Gamma passing rate](../images/gamma-index.png)
*Gamma combines physical distance and dose difference for each reference voxel.*

$$
\gamma(v)=\min_{v'}
\sqrt{\frac{r^2(v,v')}{\Delta d^2}
+\frac{\delta^2(v,v')}{\Delta D^2}}.
$$

The default criteria are $\Delta d=3\ \mathrm{mm}$ and
$\Delta D=3\%$. The returned value is the percentage of evaluated reference
voxels satisfying $\gamma(v)\leq 1$.

```python
from dosemetrics.metrics import compare_gamma

passing_rate_percent = compare_gamma(reference, evaluated, body=body)
```

### Error tail and localized artifacts

**Reference-based** · `compare_max_error`, `compare_error_percentile`,
`compare_tail_error` · Gy · lower is better.
**Reference-free** · `compute_isolated_extrema` · voxel counts · lower is better.

A mean over millions of voxels cannot see a small number of badly wrong ones. A
single voxel that is 60 Gy wrong in a $128^3$ volume moves the mean absolute
error by less than $0.01\ \mathrm{Gy}$, so a model can improve every mean-based
score while leaving — or introducing — errors that are obvious on a dose
display. These metrics describe that tail.

The tail mean at level $1-f$ is the conditional value at risk (CVaR, or
superquantile) of the absolute-error distribution, averaging the worst fraction
$f$ of voxels:

$$
\mathrm{CVaR}_{f}
=\frac{1}{\lceil fN\rceil}\sum_{i\in\mathcal{T}_{f}}
\left|D_{\mathrm{evaluated},i}-D_{\mathrm{reference},i}\right|,
$$

where $\mathcal{T}_{f}$ indexes the $\lceil fN\rceil$ largest absolute errors.
It interpolates between the two extremes: $f=1$ recovers the mean absolute
error exactly, and $f\to 0$ approaches the maximum. Averaging over a tail rather
than reporting a single order statistic keeps the quantity stable, which the
maximum is not.

```python
from dosemetrics.metrics.dose_comparison import (
    compare_error_percentile,
    compare_max_error,
    compare_tail_error,
    compute_isolated_extrema,
)

worst_voxel_gy = compare_max_error(reference, evaluated)
p999_gy = compare_error_percentile(reference, evaluated, percentile=99.9)
worst_decile_gy = compare_tail_error(reference, evaluated, fraction=0.1)
```

`compute_isolated_extrema` asks a different question, and takes no reference:
**is this dose distribution locally self-consistent?** Dose is physically smooth
at the voxel scale, so a voxel differing sharply from its own neighbourhood is
an artifact rather than anatomy. The function compares each voxel with the
median of its neighbourhood and counts those falling below (`n_dropout`) or
rising above (`n_hotspot`) by more than `deviation`, restricted to voxels whose
neighbourhood is at or above `relative_threshold` of the peak.

Both the search region and the dose scale come from the median-filtered volume,
never from raw voxel values — a dropout voxel is by definition far below its
surroundings, so thresholding on its own value would exclude it from the region
it corrupts.

```python
counts = compute_isolated_extrema(predicted_dose, relative_threshold=0.5,
                                  deviation=5.0)
counts["n_dropout"], counts["fraction_isolated"]
```

Counts are comparable across dose distributions only when they share a voxel
grid and the same `deviation`, since neighbourhood and threshold are both
absolute.

## Constraint agreement

### OAR constraint disagreement

**Reference-based** · `compare_oar_constraints` · fraction · lower is better.

![OAR constraint disagreement](../images/oar_constraint_disagreement.png)
*Each constraint contributes one binary agreement or disagreement state.*

For reference satisfaction $s_c\in\{0,1\}$ and evaluated satisfaction
$\hat{s}_c\in\{0,1\}$,

$$
\mathrm{Disagreement}
=\frac{1}{N}\sum_{c=1}^{N}
\mathbb{I}\!\left[\hat{s}_c\ne s_c\right].
$$

```python
from dosemetrics.metrics import compare_oar_constraints

disagreement = compare_oar_constraints(
    reference_satisfaction,
    evaluated_satisfaction,
)
```

## Geometry metrics

Functions in `dosemetrics.metrics.geometric` compare two structures or
structure sets. They do not require a dose reference. Dice, Jaccard,
sensitivity, specificity, volume difference, Hausdorff distance, and mean
surface distance are documented in the [Metrics API](../api/metrics.md).
