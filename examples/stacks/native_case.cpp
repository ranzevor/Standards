#include <array>
#include <cstddef>
#include <iostream>
#include <span>
#include <string_view>
static bool copy_checked(std::span<char> target, std::string_view source) {
    if (source.size() > target.size()) return false;
    for (std::size_t i=0; i<source.size(); ++i) target[i]=source[i];
    return true;
}
int main() {
    std::array<char,3> target{};
    if (!copy_checked(target,"abc")) return 1;
    if (copy_checked(target,"abcd")) return 2;
    if (!copy_checked(target,"")) return 3;
    if (std::string_view(target.data(),target.size())!="abc") return 4;
    std::cout << "cpp-contract-ok\n";
}
