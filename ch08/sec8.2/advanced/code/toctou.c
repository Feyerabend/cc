#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/stat.h>

/*
 * Vulnerable: check and open are two separate syscalls. Between access()
 * and fopen() an attacker can replace the file with a symlink to /etc/shadow.
 * access() checks the *real* UID, but fopen() runs as the *effective* UID
 * (e.g. setuid root), so the attacker gains elevated read access.
 */
void read_file_bad(const char *path) {
    if (access(path, R_OK) == 0) {   /* <-- race window starts here */
        FILE *f = fopen(path, "r");  /* <-- attacker swaps path for symlink */
        if (f) { /* ... read ... */ fclose(f); }
    }
}

/*
 * Safe: open the file first (as the effective UID), then check ownership
 * and permissions on the open file descriptor. The fd is bound to the
 * inode at the moment of open(); a later symlink swap affects only the
 * path, not the already-open descriptor.
 */
void read_file_safe(const char *path, uid_t expected_owner) {
    int fd = open(path, O_RDONLY | O_NOFOLLOW);  /* O_NOFOLLOW rejects symlinks */
    if (fd < 0) return;

    struct stat st;
    if (fstat(fd, &st) < 0 || st.st_uid != expected_owner) {
        close(fd);
        return;
    }
    FILE *f = fdopen(fd, "r");
    if (f) { /* ... read ... */ fclose(f); }
}
