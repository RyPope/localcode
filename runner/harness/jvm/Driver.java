import com.google.gson.*;
import java.io.*;
import java.lang.reflect.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;

/** JVM harness for Java and Kotlin: java Driver <cases.json> <results.jsonl>. Converts JSON by reflection. */
public class Driver {
    static final int MAX_STDOUT = 64 * 1024;
    static final int MAX_NODES = 200_000;
    static final Gson GSON = new GsonBuilder().serializeNulls().serializeSpecialFloatingPointValues().disableHtmlEscaping().create();
    static Class<?> listNode, treeNode;

    public static void main(String[] args) throws Exception {
        JsonObject spec = JsonParser.parseString(Files.readString(Path.of(args[0]))).getAsJsonObject();
        PrintStream out = new PrintStream(new FileOutputStream(args[1]), true, StandardCharsets.UTF_8);
        listNode = load("ListNode");
        treeNode = load("TreeNode");
        String name = spec.get("method").getAsString();
        int arity = spec.getAsJsonArray("params").size();
        Constructor<?> ctor;
        Method method = null;
        try {
            Class<?> cls = Class.forName("Solution");
            for (Method m : cls.getDeclaredMethods()) {
                if (m.getName().equals(name) && m.getParameterCount() == arity && !m.isSynthetic()) { method = m; break; }
            }
            if (method == null) throw new NoSuchMethodException();
            method.setAccessible(true);
            ctor = cls.getDeclaredConstructor();
            ctor.setAccessible(true);
        } catch (ReflectiveOperationException e) {
            JsonObject err = new JsonObject();
            err.addProperty("compile_error", "class Solution with method " + name + " (" + arity + " parameters) not found");
            out.println(GSON.toJson(err));
            return;
        }
        Type[] types = method.getGenericParameterTypes();
        Class<?> ret = method.getReturnType();
        PrintStream realOut = System.out;
        for (JsonElement c : spec.getAsJsonArray("cases")) {
            JsonArray a = c.getAsJsonArray();
            ByteArrayOutputStream buf = new ByteArrayOutputStream();
            JsonObject line = new JsonObject();
            System.setOut(new PrintStream(buf, true, StandardCharsets.UTF_8));
            try {
                Object[] callArgs = new Object[types.length];
                for (int i = 0; i < types.length; i++) callArgs[i] = fromJson(a.get(i), types[i]);
                Object solution = ctor.newInstance();
                long t0 = System.nanoTime();
                Object result = method.invoke(solution, callArgs);
                double ms = (System.nanoTime() - t0) / 1e6;
                if (result == null && (ret == listNode || ret == treeNode)) line.add("value", new JsonArray());
                else line.add("value", toJson(result));
                line.addProperty("ok", true);
                line.addProperty("ms", Math.round(ms * 1000) / 1000.0);
            } catch (InvocationTargetException e) {
                line.addProperty("ok", false);
                line.addProperty("error", describe(e.getCause()));
                line.addProperty("ms", 0);
            } catch (Throwable e) {
                line.addProperty("ok", false);
                line.addProperty("error", describe(e));
                line.addProperty("ms", 0);
            } finally {
                System.out.flush();
                System.setOut(realOut);
            }
            String so = buf.toString(StandardCharsets.UTF_8);
            line.addProperty("stdout", so.length() > MAX_STDOUT ? so.substring(0, MAX_STDOUT) : so);
            out.println(GSON.toJson(line));
        }
    }

    static Class<?> load(String n) {
        try { return Class.forName(n); } catch (ClassNotFoundException e) { return null; }
    }

    static String describe(Throwable t) {
        String s = t.getClass().getName() + (t.getMessage() != null ? ": " + t.getMessage() : "");
        for (StackTraceElement f : t.getStackTrace()) {
            if (f.getClassName().equals("Solution") || f.getClassName().startsWith("Solution$")) {
                return s + "\n  line " + f.getLineNumber() + ", in " + f.getMethodName();
            }
        }
        return s;
    }

    static Object fromJson(JsonElement e, Type t) throws Exception {
        if (t instanceof WildcardType w) return fromJson(e, w.getUpperBounds()[0]);
        if (t instanceof ParameterizedType p) {
            Class<?> raw = (Class<?>) p.getRawType();
            Type arg = p.getActualTypeArguments()[0];
            Collection<Object> coll = Set.class.isAssignableFrom(raw) ? new HashSet<>() : new ArrayList<>();
            if (e != null && !e.isJsonNull()) for (JsonElement x : e.getAsJsonArray()) coll.add(fromJson(x, arg));
            return coll;
        }
        if (t instanceof GenericArrayType g) return array(e, g.getGenericComponentType(), raw(g.getGenericComponentType()));
        Class<?> c = (Class<?>) t;
        if (e == null || e.isJsonNull()) return c.isPrimitive() ? null : null;
        if (c == int.class || c == Integer.class) return e.getAsInt();
        if (c == long.class || c == Long.class) return e.getAsLong();
        if (c == double.class || c == Double.class) return e.getAsDouble();
        if (c == float.class || c == Float.class) return e.getAsFloat();
        if (c == boolean.class || c == Boolean.class) return e.getAsBoolean();
        if (c == char.class || c == Character.class) return e.getAsString().charAt(0);
        if (c == short.class || c == Short.class) return e.getAsShort();
        if (c == byte.class || c == Byte.class) return e.getAsByte();
        if (c == String.class) return e.getAsString();
        if (c.isArray()) return array(e, c.getComponentType(), c.getComponentType());
        if (c == listNode) return buildList(e.getAsJsonArray());
        if (c == treeNode) return buildTree(e.getAsJsonArray());
        if (List.class.isAssignableFrom(c) || c == Collection.class) return fromJson(e, new ParameterizedTypeShim(c));
        throw new IllegalArgumentException("unsupported parameter type " + c.getName());
    }

    static Class<?> raw(Type t) {
        if (t instanceof Class<?> c) return c;
        if (t instanceof ParameterizedType p) return (Class<?>) p.getRawType();
        if (t instanceof GenericArrayType g) return java.lang.reflect.Array.newInstance(raw(g.getGenericComponentType()), 0).getClass();
        return Object.class;
    }

    static Object array(JsonElement e, Type comp, Class<?> compClass) throws Exception {
        JsonArray a = e.getAsJsonArray();
        Object arr = java.lang.reflect.Array.newInstance(compClass, a.size());
        for (int i = 0; i < a.size(); i++) java.lang.reflect.Array.set(arr, i, fromJson(a.get(i), comp));
        return arr;
    }

    static Object newNode(Class<?> c, int v) throws Exception {
        Constructor<?> k = c.getDeclaredConstructor(int.class);
        k.setAccessible(true);
        return k.newInstance(v);
    }

    static Field field(Class<?> c, String n) throws Exception {
        Field f = c.getDeclaredField(n);
        f.setAccessible(true);
        return f;
    }

    static Object buildList(JsonArray a) throws Exception {
        Object head = null, cur = null;
        Field next = field(listNode, "next");
        for (JsonElement x : a) {
            Object n = newNode(listNode, x.getAsInt());
            if (cur == null) head = n; else next.set(cur, n);
            cur = n;
        }
        return head;
    }

    static Object buildTree(JsonArray a) throws Exception {
        if (a.size() == 0 || a.get(0).isJsonNull()) return null;
        Field left = field(treeNode, "left"), right = field(treeNode, "right");
        Object root = newNode(treeNode, a.get(0).getAsInt());
        ArrayDeque<Object> q = new ArrayDeque<>(List.of(root));
        int i = 1;
        while (!q.isEmpty() && i < a.size()) {
            Object n = q.poll();
            if (i < a.size() && !a.get(i).isJsonNull()) { Object l = newNode(treeNode, a.get(i).getAsInt()); left.set(n, l); q.add(l); }
            i++;
            if (i < a.size() && !a.get(i).isJsonNull()) { Object r = newNode(treeNode, a.get(i).getAsInt()); right.set(n, r); q.add(r); }
            i++;
        }
        return root;
    }

    static JsonElement toJson(Object o) throws Exception {
        if (o == null) return JsonNull.INSTANCE;
        if (o instanceof Character ch) return new JsonPrimitive(String.valueOf(ch));
        if (o instanceof Number n) return new JsonPrimitive(n);
        if (o instanceof Boolean b) return new JsonPrimitive(b);
        if (o instanceof String s) return new JsonPrimitive(s);
        if (o instanceof CharSequence s) return new JsonPrimitive(s.toString());
        JsonArray arr = new JsonArray();
        if (o.getClass().isArray()) {
            int n = java.lang.reflect.Array.getLength(o);
            for (int i = 0; i < n; i++) arr.add(toJson(java.lang.reflect.Array.get(o, i)));
            return arr;
        }
        if (o instanceof Iterable<?> it) {
            for (Object x : it) arr.add(toJson(x));
            return arr;
        }
        if (o.getClass() == listNode) {
            Field val = field(listNode, "val"), next = field(listNode, "next");
            for (int n = 0; o != null && n < MAX_NODES; n++) { arr.add(val.getInt(o)); o = next.get(o); }
            return arr;
        }
        if (o.getClass() == treeNode) {
            Field val = field(treeNode, "val"), left = field(treeNode, "left"), right = field(treeNode, "right");
            List<Object> q = new ArrayList<>(List.of(o));
            for (int i = 0; i < q.size() && arr.size() <= MAX_NODES; i++) {
                Object n = q.get(i);
                if (n == null) { arr.add(JsonNull.INSTANCE); continue; }
                arr.add(val.getInt(n));
                q.add(left.get(n));
                q.add(right.get(n));
            }
            while (arr.size() > 0 && arr.get(arr.size() - 1).isJsonNull()) arr.remove(arr.size() - 1);
            return arr;
        }
        return new JsonPrimitive(String.valueOf(o));
    }

    /** Raw List parameter with no generic info: treat elements as Object (JSON passthrough). */
    record ParameterizedTypeShim(Class<?> raw) implements ParameterizedType {
        public Type[] getActualTypeArguments() { return new Type[]{Object.class}; }
        public Type getRawType() { return raw; }
        public Type getOwnerType() { return null; }
    }
}
