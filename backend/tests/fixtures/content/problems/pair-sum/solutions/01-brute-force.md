---
title: Brute force
---
Try every pair.

```cpp
class Solution {
public:
    vector<int> pairSum(vector<int>& nums, int goal) {
        for (int i = 0; i < nums.size(); i++)
            for (int j = i + 1; j < nums.size(); j++)
                if (nums[i] + nums[j] == goal) return {i, j};
        return {};
    }
};
```
