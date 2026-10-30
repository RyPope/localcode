"""Generate main.cpp: user code plus a typed driver for the problem's method signature."""
import re


def _local_type(t: str) -> str:
    t = re.sub(r"\bconst\b", "", t).replace("&", "")
    return re.sub(r"\s+", " ", t).strip()


def gen_main(user_code: str, sig: dict) -> str:
    decls = "\n".join(
        f"            auto a{i} = lc::conv<{_local_type(p['type'])}>::from(c[{i}]);" for i, p in enumerate(sig["params"])
    )
    call_args = ", ".join(f"a{i}" for i in range(len(sig["params"])))
    ret = _local_type(sig["ret"])
    return f'''#include <lc.hpp>
#line 1 "solution.cpp"
{user_code}
#line 1 "driver"
int main(int argc, char** argv) {{
    json spec = lc::read_spec(argv[1]);
    ofstream out(argv[2]);
    auto* real = cout.rdbuf();
    for (auto& c : spec["cases"]) {{
        json line;
        stringstream buf;
        cout.rdbuf(buf.rdbuf());
        try {{
{decls}
            Solution sol;
            auto t0 = chrono::steady_clock::now();
            {ret} r = sol.{sig["method"]}({call_args});
            double ms = chrono::duration<double, milli>(chrono::steady_clock::now() - t0).count();
            line["value"] = lc::conv<{ret}>::to(r);
            line["ok"] = true;
            line["ms"] = round(ms * 1000) / 1000;
        }} catch (const exception& e) {{
            line["ok"] = false;
            line["error"] = lc::demangle(typeid(e).name()) + ": " + e.what();
            line["ms"] = 0;
        }} catch (...) {{
            line["ok"] = false;
            line["error"] = "unknown exception";
            line["ms"] = 0;
        }}
        cout.flush();
        cout.rdbuf(real);
        line["stdout"] = buf.str().substr(0, 65536);
        out << lc::dump_line(line) << "\\n";
        out.flush();
    }}
}}
'''
