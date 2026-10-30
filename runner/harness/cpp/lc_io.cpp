#include "lc.hpp"

namespace lc {
json read_spec(const char* path) {
    ifstream in(path);
    return json::parse(in);
}

string dump_line(const json& line) { return line.dump(-1, ' ', false, json::error_handler_t::replace); }
}  // namespace lc
