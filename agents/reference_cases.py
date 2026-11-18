"""Small reproducible classroom examples; keys identify snapshots in execution order."""


def _binary_search():
    values, target = [2, 5, 8, 12, 17, 21, 28], 21
    lo, hi = 0, len(values) - 1
    states = {}
    while lo <= hi:
        mid = (lo + hi) // 2
        states[f"s{len(states)}"] = {"values": values, "target": target, "lo": lo,
                                    "hi": hi, "mid": mid, "value": values[mid]}
        if values[mid] == target:
            states["found"] = {"index": mid, "value": target}
            break
        if values[mid] < target:
            lo = mid + 1
        else:
            hi = mid - 1
    return states


def _btree_right_borrow():
    # Minimum degree 2, leaf deletion followed by bottom-up underflow repair.
    left, separator, right = [25], 40, [50, 60]

    def snapshot():
        return {"left": left.copy(), "separator": separator, "right": right.copy()}

    states = {"before": snapshot()}
    left.remove(25)
    states["underflow"] = snapshot()
    left.append(separator)
    separator = right.pop(0)
    states["repaired"] = snapshot()
    return states


REFERENCE_CASES = {
    "binary_search_inclusive": _binary_search,
    "btree_t2_right_borrow": _btree_right_borrow,
}
