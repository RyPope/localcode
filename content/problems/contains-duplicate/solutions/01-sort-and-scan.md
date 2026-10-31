---
title: Sort and compare neighbours
---
After sorting, equal values sit next to each other, so it's enough to compare each element with the one before it. This uses no extra memory beyond the sort, unlike the hash-set approach.

Time complexity $O(n \log n)$, space complexity $O(\log n)$ for the sort.

```python
class Solution:
    def containsDuplicate(self, nums: List[int]) -> bool:
        nums = sorted(nums)
        return any(a == b for a, b in zip(nums, nums[1:]))
```

```java
class Solution {
    public boolean containsDuplicate(int[] nums) {
        Arrays.sort(nums);
        for (int i = 1; i < nums.length; i++) if (nums[i] == nums[i - 1]) return true;
        return false;
    }
}
```

```cpp
class Solution {
public:
    bool containsDuplicate(vector<int>& nums) {
        sort(nums.begin(), nums.end());
        for (int i = 1; i < nums.size(); i++) if (nums[i] == nums[i - 1]) return true;
        return false;
    }
};
```
