// localcode C++ harness prelude: LeetCode node types and JSON <-> C++ conversions.
#pragma once
#include <bits/stdc++.h>
#include <cxxabi.h>
#include <nlohmann/json.hpp>
using namespace std;
using json = nlohmann::json;

struct ListNode {
    int val;
    ListNode *next;
    ListNode() : val(0), next(nullptr) {}
    ListNode(int x) : val(x), next(nullptr) {}
    ListNode(int x, ListNode *next) : val(x), next(next) {}
};

struct TreeNode {
    int val;
    TreeNode *left;
    TreeNode *right;
    TreeNode() : val(0), left(nullptr), right(nullptr) {}
    TreeNode(int x) : val(x), left(nullptr), right(nullptr) {}
    TreeNode(int x, TreeNode *left, TreeNode *right) : val(x), left(left), right(right) {}
};

namespace lc {
constexpr size_t MAX_NODES = 200000;

template <class T> struct conv {
    static T from(const json& j) { return j.get<T>(); }
    static json to(const T& v) { return json(v); }
};
template <> struct conv<char> {
    static char from(const json& j) { return j.get<string>()[0]; }
    static json to(char c) { return json(string(1, c)); }
};
template <class T> struct conv<vector<T>> {
    static vector<T> from(const json& j) {
        vector<T> v;
        for (auto& x : j) v.push_back(conv<T>::from(x));
        return v;
    }
    static json to(const vector<T>& v) {
        json a = json::array();
        for (const auto& x : v) a.push_back(conv<T>::to(x));
        return a;
    }
};
template <> struct conv<ListNode*> {
    static ListNode* from(const json& j) {
        ListNode dummy, *cur = &dummy;
        for (auto& x : j) cur = cur->next = new ListNode(x.get<int>());
        return dummy.next;
    }
    static json to(ListNode* n) {
        json a = json::array();
        for (size_t k = 0; n && k < MAX_NODES; n = n->next, ++k) a.push_back(n->val);
        return a;
    }
};
template <> struct conv<TreeNode*> {
    static TreeNode* from(const json& j) {
        if (j.empty() || j[0].is_null()) return nullptr;
        TreeNode* root = new TreeNode(j[0].get<int>());
        deque<TreeNode*> q{root};
        size_t i = 1;
        while (!q.empty() && i < j.size()) {
            TreeNode* n = q.front();
            q.pop_front();
            if (i < j.size() && !j[i].is_null()) q.push_back(n->left = new TreeNode(j[i].get<int>()));
            ++i;
            if (i < j.size() && !j[i].is_null()) q.push_back(n->right = new TreeNode(j[i].get<int>()));
            ++i;
        }
        return root;
    }
    static json to(TreeNode* root) {
        json a = json::array();
        vector<TreeNode*> q{root};
        for (size_t i = 0; i < q.size() && a.size() <= MAX_NODES; ++i) {
            if (!q[i]) { a.push_back(nullptr); continue; }
            a.push_back(q[i]->val);
            q.push_back(q[i]->left);
            q.push_back(q[i]->right);
        }
        while (!a.empty() && a.back().is_null()) a.erase(a.size() - 1);
        return a;
    }
};

// Defined in lc_io.cpp, compiled once into lc_io.o so each submission skips these instantiations.
json read_spec(const char* path);
string dump_line(const json& line);

inline string demangle(const char* name) {
    int status = 0;
    char* d = abi::__cxa_demangle(name, nullptr, nullptr, &status);
    string s = status == 0 ? d : name;
    free(d);
    return s;
}
}  // namespace lc
