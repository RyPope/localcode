---
title: Count Prominent Peaks
difficulty: Hard
tags: [Array, Stack, Monotonic Stack]
---
You are walking a ridgeline and have recorded its elevation profile as an integer array `heights`, where `heights[i]` is the elevation at the `i`th point from west to east.

A **peak** is a maximal run of one or more adjacent points with equal elevation whose neighbouring points (where they exist) are all strictly lower. A single point with no neighbours is a peak.

The **prominence** of a peak measures how far you must descend from it before you can climb to anything higher:

- On each side, look for the nearest point that is **strictly higher** than the peak. If there is one, the **key col** on that side is the lowest elevation strictly between the peak and that point.
- If a higher point exists on at least one side, the peak's prominence is its elevation minus the **higher** of its key cols. (Of the routes to higher ground, take the one that loses the least height.)
- If no point on either side is strictly higher, the peak is a **summit** of the profile, and its prominence is its elevation minus the lowest elevation in `heights`. Several summits can share the highest elevation.

Peak baggers only count a summit once it stands out from its surroundings. Given an integer `k`, return the number of peaks whose prominence is **at least** `k`.

**Example 1:**

```
Input: heights = [1,5,3,6,2,4,1], k = 2
Output: 3
Explanation:
The peaks are 5, 6 and 4.
- 5: no higher point to the west; to the east, 6 is higher and the lowest point on the way is 3. Prominence 5 - 3 = 2.
- 6: nothing is higher, so it is a summit. Prominence 6 - 1 = 5.
- 4: to the west, 6 is higher and the lowest point on the way is 2. Prominence 4 - 2 = 2.
All three have prominence at least 2.
```

**Example 2:**

```
Input: heights = [2,7,7,4,8,8,3,9,1], k = 4
Output: 2
Explanation:
The peaks are the run 7,7, the run 8,8, and 9.
- 7,7: the nearest higher point is 8, to the east, with a key col of 4. Prominence 3.
- 8,8: the nearest higher point is 9, to the east, with a key col of 3. Prominence 5.
- 9: a summit. Prominence 9 - 1 = 8.
```

**Example 3:**

```
Input: heights = [5,1,5], k = 4
Output: 2
Explanation: Neither 5 is strictly higher than the other, so both are summits with prominence 5 - 1 = 4.
```

**Constraints:**

- `1 <= heights.length <= 10^5`
- `0 <= heights[i] <= 10^6`
- `1 <= k <= 10^6`
