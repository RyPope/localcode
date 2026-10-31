---
title: Single pass
---
Walk the string once, keeping the length of the current vowel run and the longest seen so far. A consonant resets the current run to zero.

Time complexity $O(n)$, space complexity $O(1)$.

```python
class Solution:
    def longestVowelRun(self, s: str) -> int:
        best = cur = 0
        for c in s:
            cur = cur + 1 if c in "aeiou" else 0
            best = max(best, cur)
        return best
```

```java
class Solution {
    public int longestVowelRun(String s) {
        int best = 0, cur = 0;
        for (char c : s.toCharArray()) {
            cur = "aeiou".indexOf(c) >= 0 ? cur + 1 : 0;
            best = Math.max(best, cur);
        }
        return best;
    }
}
```

```cpp
class Solution {
public:
    int longestVowelRun(string s) {
        int best = 0, cur = 0;
        for (char c : s) {
            cur = string("aeiou").find(c) != string::npos ? cur + 1 : 0;
            best = max(best, cur);
        }
        return best;
    }
};
```

```kotlin
class Solution {
    fun longestVowelRun(s: String): Int {
        var best = 0
        var cur = 0
        for (c in s) {
            cur = if (c in "aeiou") cur + 1 else 0
            best = maxOf(best, cur)
        }
        return best
    }
}
```
