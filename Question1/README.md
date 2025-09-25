# Question 1 - Subset Sum Solver

## Problem
You are given a CSV file where each row contains:
- The first number: the "big number"
- The following numbers (up to 12): the "small numbers"

The task is to find the combination of small numbers whose sum is as close as possible to the big number **without exceeding it**.

---

## How to run
First, go into the `Question1` folder:
```bash
cd Question1
python subset-sum-solver.py sample.csv
```

## Approach

I used an exhaustive subset enumeration with bitmasks.
With at most 12 small numbers per row, the search space is only 2¹² = 4,096 subsets, which is very small.
This guarantees the optimal solution and is fast enough for this problem.

Advantages

Always finds the best subset.

Simple and clear code.

Works with integers and decimals.

Limitations

Does not scale to very large inputs (e.g., >20 small numbers).

For larger cases, a dynamic programming or meet-in-the-middle approach would be required.