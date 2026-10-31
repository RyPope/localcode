---
title: Walk outwards from each peak
---
First find the peaks: scan for maximal runs of equal elevation whose neighbours are both lower.

For each peak, walk west while the points are no higher than the peak, tracking the lowest elevation seen. If the walk stops at a strictly higher point, that lowest elevation is the western key col; if it runs off the end, there is no higher ground to the west. Do the same to the east. The prominence is the peak's elevation minus the higher key col, or minus the profile's minimum if neither walk found higher ground.

Each walk can cross the whole array, so this takes $O(n^2)$ time in the worst case (for example, many small peaks on one long slope) and $O(1)$ extra space. It is too slow for the largest inputs but is a useful reference.

```python
class Solution:
    def countProminentPeaks(self, heights: List[int], k: int) -> int:
        h, n = heights, len(heights)
        lowest, count, i = min(h), 0, 0
        while i < n:
            j = i
            while j + 1 < n and h[j + 1] == h[i]:
                j += 1
            if (i == 0 or h[i - 1] < h[i]) and (j == n - 1 or h[j + 1] < h[i]):
                cols = []
                low, a = h[i], i - 1
                while a >= 0 and h[a] <= h[i]:
                    low = min(low, h[a])
                    a -= 1
                if a >= 0:
                    cols.append(low)
                low, b = h[i], j + 1
                while b < n and h[b] <= h[i]:
                    low = min(low, h[b])
                    b += 1
                if b < n:
                    cols.append(low)
                if h[i] - (max(cols) if cols else lowest) >= k:
                    count += 1
            i = j + 1
        return count
```

```java
class Solution {
    public int countProminentPeaks(int[] heights, int k) {
        int[] h = heights;
        int n = h.length, lowest = Integer.MAX_VALUE, count = 0;
        for (int x : h) lowest = Math.min(lowest, x);
        for (int i = 0; i < n; ) {
            int j = i;
            while (j + 1 < n && h[j + 1] == h[i]) j++;
            if ((i == 0 || h[i - 1] < h[i]) && (j == n - 1 || h[j + 1] < h[i])) {
                int col = -1;
                int low = h[i], a = i - 1;
                while (a >= 0 && h[a] <= h[i]) low = Math.min(low, h[a--]);
                if (a >= 0) col = Math.max(col, low);
                low = h[i];
                int b = j + 1;
                while (b < n && h[b] <= h[i]) low = Math.min(low, h[b++]);
                if (b < n) col = Math.max(col, low);
                if (h[i] - (col >= 0 ? col : lowest) >= k) count++;
            }
            i = j + 1;
        }
        return count;
    }
}
```

```cpp
class Solution {
public:
    int countProminentPeaks(vector<int>& heights, int k) {
        const vector<int>& h = heights;
        int n = h.size(), lowest = *min_element(h.begin(), h.end()), count = 0;
        for (int i = 0; i < n;) {
            int j = i;
            while (j + 1 < n && h[j + 1] == h[i]) j++;
            if ((i == 0 || h[i - 1] < h[i]) && (j == n - 1 || h[j + 1] < h[i])) {
                int col = -1;
                int low = h[i], a = i - 1;
                while (a >= 0 && h[a] <= h[i]) low = min(low, h[a--]);
                if (a >= 0) col = max(col, low);
                low = h[i];
                int b = j + 1;
                while (b < n && h[b] <= h[i]) low = min(low, h[b++]);
                if (b < n) col = max(col, low);
                if (h[i] - (col >= 0 ? col : lowest) >= k) count++;
            }
            i = j + 1;
        }
        return count;
    }
};
```

```kotlin
class Solution {
    fun countProminentPeaks(heights: IntArray, k: Int): Int {
        val h = heights
        val n = h.size
        val lowest = h.min()
        var count = 0
        var i = 0
        while (i < n) {
            var j = i
            while (j + 1 < n && h[j + 1] == h[i]) j++
            if ((i == 0 || h[i - 1] < h[i]) && (j == n - 1 || h[j + 1] < h[i])) {
                var col = -1
                var low = h[i]
                var a = i - 1
                while (a >= 0 && h[a] <= h[i]) low = minOf(low, h[a--])
                if (a >= 0) col = maxOf(col, low)
                low = h[i]
                var b = j + 1
                while (b < n && h[b] <= h[i]) low = minOf(low, h[b++])
                if (b < n) col = maxOf(col, low)
                if (h[i] - (if (col >= 0) col else lowest) >= k) count++
            }
            i = j + 1
        }
        return count
    }
}
```
