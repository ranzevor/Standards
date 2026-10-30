#include <stdbool.h>
#include <stddef.h>
#include <stdio.h>
#include <string.h>
static bool copy_checked(char *target, size_t capacity, const char *source, size_t length) {
    if (length > capacity) return false;
    if (length != 0) memcpy(target, source, length);
    return true;
}
int main(void) {
    char target[3] = {0, 0, 0};
    const char source[] = "abc";
    if (!copy_checked(target, sizeof target, source, 3)) return 1;
    if (memcmp(target, source, 3) != 0) return 2;
    if (copy_checked(target, sizeof target, source, 4)) return 3;
    if (!copy_checked(target, sizeof target, source, 0)) return 4;
    puts("c-contract-ok");
    return 0;
}
