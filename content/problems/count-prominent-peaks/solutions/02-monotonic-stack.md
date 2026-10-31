---
title: Monotonic stack
---
A run of equal elevations behaves exactly like a single point, so first collapse each run to one point. A peak is then a point whose neighbours are both lower.

The western key col of point $i$ is the minimum of the elevations strictly between $i$ and the nearest strictly higher point to its west. Finding the nearest strictly higher point is the classic monotonic-stack problem. The twist is that we also need the lowest point in between, so each stack entry carries its height and `gap`: the lowest elevation between it and the entry above it, or the current position for the top entry.

Sweep from west to east. At point $i$, pop every entry that is no higher than $h_i$, folding each popped height and its `gap` into a running minimum `low` (which starts at $h_i$). Those points lie between $i$ and whatever is left on the stack. If the stack is non-empty, its top is the nearest strictly higher point, and the key col is `min(low, top.gap)`. Then fold `low` into `top.gap`, because the popped points now sit between the top and $i$, and push $i$ with an empty gap.

A sweep from east to west gives the eastern key cols the same way. A peak with neither col is a summit and is measured from the global minimum.

Every point is pushed and popped at most once per sweep, so this is $O(n)$ time and $O(n)$ space.

```python
class Solution:
    def countProminentPeaks(self, heights: List[int], k: int) -> int:
        h = [x for i, x in enumerate(heights) if i == 0 or x != heights[i - 1]]
        n = len(h)

        def key_cols(order):
            col = [None] * n
            stack = []  # [height, lowest elevation between it and the next entry up]
            for i in order:
                low = h[i]
                while stack and stack[-1][0] <= h[i]:
                    top_h, gap = stack.pop()
                    low = min(low, top_h, gap)
                if stack:
                    col[i] = min(low, stack[-1][1])
                    stack[-1][1] = min(stack[-1][1], low)
                stack.append([h[i], float("inf")])
            return col

        west, east = key_cols(range(n)), key_cols(range(n - 1, -1, -1))
        lowest, count = min(h), 0
        for i in range(n):
            if (i == 0 or h[i - 1] < h[i]) and (i == n - 1 or h[i + 1] < h[i]):
                cols = [c for c in (west[i], east[i]) if c is not None]
                if h[i] - (max(cols) if cols else lowest) >= k:
                    count += 1
        return count
```

```java
class Solution {
    public int countProminentPeaks(int[] heights, int k) {
        int[] h = collapse(heights);
        int n = h.length, lowest = Integer.MAX_VALUE, count = 0;
        for (int x : h) lowest = Math.min(lowest, x);
        int[] west = keyCols(h, true), east = keyCols(h, false);
        for (int i = 0; i < n; i++) {
            if ((i == 0 || h[i - 1] < h[i]) && (i == n - 1 || h[i + 1] < h[i])) {
                int col = Math.max(west[i], east[i]);
                if (h[i] - (col >= 0 ? col : lowest) >= k) count++;
            }
        }
        return count;
    }

    private int[] collapse(int[] a) {
        int m = 0;
        int[] out = new int[a.length];
        for (int i = 0; i < a.length; i++) if (i == 0 || a[i] != a[i - 1]) out[m++] = a[i];
        return java.util.Arrays.copyOf(out, m);
    }

    // Key col on one side of every point, or -1 when nothing on that side is higher.
    private int[] keyCols(int[] h, boolean westward) {
        int n = h.length, top = -1;
        int[] col = new int[n], stackH = new int[n], gap = new int[n];
        for (int s = 0; s < n; s++) {
            int i = westward ? s : n - 1 - s;
            int low = h[i];
            while (top >= 0 && stackH[top] <= h[i]) {
                low = Math.min(low, Math.min(stackH[top], gap[top]));
                top--;
            }
            col[i] = -1;
            if (top >= 0) {
                col[i] = Math.min(low, gap[top]);
                gap[top] = Math.min(gap[top], low);
            }
            top++;
            stackH[top] = h[i];
            gap[top] = Integer.MAX_VALUE;
        }
        return col;
    }
}
```

```cpp
class Solution {
public:
    int countProminentPeaks(vector<int>& heights, int k) {
        vector<int> h;
        for (int i = 0; i < heights.size(); i++)
            if (i == 0 || heights[i] != heights[i - 1]) h.push_back(heights[i]);
        int n = h.size(), lowest = *min_element(h.begin(), h.end()), count = 0;
        vector<int> west = keyCols(h, true), east = keyCols(h, false);
        for (int i = 0; i < n; i++) {
            if ((i == 0 || h[i - 1] < h[i]) && (i == n - 1 || h[i + 1] < h[i])) {
                int col = max(west[i], east[i]);
                if (h[i] - (col >= 0 ? col : lowest) >= k) count++;
            }
        }
        return count;
    }

private:
    // Key col on one side of every point, or -1 when nothing on that side is higher.
    vector<int> keyCols(const vector<int>& h, bool westward) {
        int n = h.size();
        vector<int> col(n, -1);
        vector<pair<int, int>> stack;  // {height, lowest elevation up to the next entry}
        for (int s = 0; s < n; s++) {
            int i = westward ? s : n - 1 - s;
            int low = h[i];
            while (!stack.empty() && stack.back().first <= h[i]) {
                low = min({low, stack.back().first, stack.back().second});
                stack.pop_back();
            }
            if (!stack.empty()) {
                col[i] = min(low, stack.back().second);
                stack.back().second = min(stack.back().second, low);
            }
            stack.push_back({h[i], INT_MAX});
        }
        return col;
    }
};
```

```kotlin
class Solution {
    fun countProminentPeaks(heights: IntArray, k: Int): Int {
        val h = heights.filterIndexed { i, x -> i == 0 || x != heights[i - 1] }.toIntArray()
        val n = h.size
        val lowest = h.min()
        val west = keyCols(h, true)
        val east = keyCols(h, false)
        var count = 0
        for (i in 0 until n) {
            if ((i == 0 || h[i - 1] < h[i]) && (i == n - 1 || h[i + 1] < h[i])) {
                val col = maxOf(west[i], east[i])
                if (h[i] - (if (col >= 0) col else lowest) >= k) count++
            }
        }
        return count
    }

    // Key col on one side of every point, or -1 when nothing on that side is higher.
    private fun keyCols(h: IntArray, westward: Boolean): IntArray {
        val n = h.size
        val col = IntArray(n) { -1 }
        val stackH = IntArray(n)
        val gap = IntArray(n)
        var top = -1
        for (s in 0 until n) {
            val i = if (westward) s else n - 1 - s
            var low = h[i]
            while (top >= 0 && stackH[top] <= h[i]) {
                low = minOf(low, stackH[top], gap[top])
                top--
            }
            if (top >= 0) {
                col[i] = minOf(low, gap[top])
                gap[top] = minOf(gap[top], low)
            }
            top++
            stackH[top] = h[i]
            gap[top] = Int.MAX_VALUE
        }
        return col
    }
}
```
