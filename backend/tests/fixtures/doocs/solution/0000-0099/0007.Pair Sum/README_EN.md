---
comments: true
difficulty: Easy
tags:
    - Array
    - Hash Table
---

<!-- problem:start -->

# [7. Pair Sum](https://leetcode.com/problems/pair-sum)

[中文文档](/solution/0000-0099/0007.Pair%20Sum/README.md)

## Description

<!-- description:start -->

<p>Find two indices whose values add up to <code>goal</code>.</p>

<!-- description:end -->

## Solutions

<!-- solution:start -->

### Solution 1: Hash Map

<!-- thinking:start -->

> Think about complements.

<!-- thinking:end -->

Store each value's index; look up `goal - x`.

The time complexity is $O(n)$.

<!-- tabs:start -->

#### Python3

```python
class Solution:
    def pairSum(self, nums: List[int], goal: int) -> List[int]:
        return []
```

#### Java

```java
class Solution {
    public int[] pairSum(int[] nums, int goal) {
        return new int[0];
    }
}
```

#### C++

```cpp
class Solution {
public:
    vector<int> pairSum(vector<int>& nums, int goal) {
        return {};
    }
};
```

#### Go

```go
func pairSum(nums []int, goal int) []int { return nil }
```

<!-- tabs:end -->

<!-- solution:end -->

<!-- solution:start -->

### Solution 2

Brute force over all pairs.

<!-- tabs:start -->

#### Python3

```python
class Solution:
    def pairSum(self, nums, goal):
        return [0, 1]
```

#### Kotlin

```kotlin
class Solution {
    fun pairSum(nums: IntArray, goal: Int): IntArray = intArrayOf(0, 1)
}
```

<!-- tabs:end -->

<!-- solution:end -->

<!-- problem:end -->
