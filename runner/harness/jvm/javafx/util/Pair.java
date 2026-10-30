package javafx.util;

import java.util.Objects;

/** The `javafx.util.Pair` LeetCode's Java environment provides. */
public class Pair<K, V> {
    private final K key;
    private final V value;

    public Pair(K key, V value) {
        this.key = key;
        this.value = value;
    }

    public K getKey() { return key; }

    public V getValue() { return value; }

    @Override
    public boolean equals(Object o) {
        return o instanceof Pair<?, ?> p && Objects.equals(key, p.key) && Objects.equals(value, p.value);
    }

    @Override
    public int hashCode() { return Objects.hash(key, value); }

    @Override
    public String toString() { return key + "=" + value; }
}
