#!/usr/bin/env python3
# subset_sum_basic.py
import csv
import sys
from decimal import Decimal, getcontext, InvalidOperation

getcontext().prec = 50  # buena precisión para decimales

def d(x: str) -> Decimal:
    x = x.strip()
    if x.count(",") == 1 and x.count(".") == 0:
        x = x.replace(",", ".")
    try:
        return Decimal(x)
    except InvalidOperation:
        raise ValueError(f"No puedo convertir a número: {x!r}")

def numstr(x: Decimal) -> str:
    return str(int(x)) if x == x.to_integral_value() else format(x.normalize(), "f")

def main(path: str):
    with open(path, newline="", encoding="utf-8") as f:
        for idx, row in enumerate(csv.reader(f), start=1):
            # saltar filas vacías
            if not row or all(not c.strip() for c in row):
                continue

            nums = [d(c) for c in row]
            if len(nums) < 2:
                print(f"Row {idx}: ERROR need at least 1 big and 1 small number", file=sys.stderr)
                continue
            target = nums[0]
            arr = nums[1:]

            best_sum = Decimal(0)
            best_subset = []

            n = len(arr)
            for mask in range(1 << n):
                s = Decimal(0)
                subset = []
                ok = True
                for i in range(n):
                    if mask & (1 << i):
                        s += arr[i]
                        if s > target:
                            ok = False
                            break
                        subset.append(arr[i])
                if ok and s > best_sum:
                    best_sum = s
                    best_subset = subset

            chosen = "[" + ", ".join(numstr(x) for x in best_subset) + "]"
            print(f"Row {idx}: chosen={chosen} sum={numstr(best_sum)} / target={numstr(target)}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python subset_sum_basic.py input.csv", file=sys.stderr)
        sys.exit(1)
    main(sys.argv[1])
