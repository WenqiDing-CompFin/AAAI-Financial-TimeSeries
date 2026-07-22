# Experiment Protocol

## Question

Can a linear model using only lagged price and volume features improve held-out
next-month return error relative to a persistence baseline in a deterministic
pipeline fixture?

This question validates the experimental harness. It is not a market-efficiency
or investment hypothesis because the default panel is synthetic.

## Frozen Inputs

- Features: one-month return, lagged three-month return, lagged six-month
  volatility, and one-month volume change.
- Target: next-month close-to-close return, computed within ticker.
- Partitions: first 60% of dates for training, next 20% for validation, and last
  20% for final testing.
- Selection metric: validation mean squared error.
- Candidate Ridge alphas: 0.01, 0.1, 1.0, and 10.0.
- Comparators: latest-return persistence and Ridge regression.

## Leakage Controls

1. Dates, not rows, define every partition, so the same month cannot enter two
   partitions through different assets.
2. Ticker-level group operations prevent price lags and targets from crossing
   security boundaries.
3. Standardization statistics are fitted on the training partition during model
   selection.
4. Alpha is chosen on validation data without consulting test metrics.
5. After selection, the model is refitted on train plus validation and evaluated
   once on the final chronological test partition.

## Success and Failure

A successful software run means tests pass, outputs are deterministic for a fixed
seed, every test row has a prediction, and all metrics are finite. Ridge beating
persistence is reported if it occurs but is not required for pipeline validity.

The experiment must be considered failed or inconclusive if any target leaks into
features, a partition date overlaps, output changes under the same environment and
seed, or an implementation error removes difficult observations.

## Real-Data Gate

No historical-market conclusion is allowed until the dataset documents source and
redistribution rights, total-return adjustment, inactive securities, universe
membership, execution timing, and a test period that was frozen before results
were inspected.
