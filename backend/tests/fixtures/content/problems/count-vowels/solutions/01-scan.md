---
title: Single scan
---
Count characters that are in the vowel set. Time $O(n)$, space $O(1)$.

```python
class Solution:
    def countVowels(self, s: str) -> int:
        return sum(c in "aeiou" for c in s)
```

```java
class Solution {
    public int countVowels(String s) {
        int n = 0;
        for (char c : s.toCharArray()) if ("aeiou".indexOf(c) >= 0) n++;
        return n;
    }
}
```
