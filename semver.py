#!/usr/bin/env python3
"""Semantic versioning parser, comparator, and range checker."""
import sys, re

class SemVer:
    def __init__(self, version_str):
        m = re.match(r"^v?(\d+)\.(\d+)\.(\d+)(?:-([a-zA-Z0-9.]+))?(?:\+([a-zA-Z0-9.]+))?$", version_str)
        if not m: raise ValueError(f"Invalid semver: {version_str}")
        self.major, self.minor, self.patch = int(m.group(1)), int(m.group(2)), int(m.group(3))
        self.prerelease = m.group(4)
        self.build = m.group(5)
    def __str__(self):
        s = f"{self.major}.{self.minor}.{self.patch}"
        if self.prerelease: s += f"-{self.prerelease}"
        if self.build: s += f"+{self.build}"
        return s
    def _tuple(self):
        pre = (0, self.prerelease or "") if self.prerelease else (1, "")
        return (self.major, self.minor, self.patch, pre[0], pre[1])
    def __eq__(self, o): return self._tuple() == o._tuple()
    def __lt__(self, o): return self._tuple() < o._tuple()
    def __le__(self, o): return self._tuple() <= o._tuple()
    def __gt__(self, o): return self._tuple() > o._tuple()
    def __ge__(self, o): return self._tuple() >= o._tuple()
    def bump_major(self): return SemVer(f"{self.major+1}.0.0")
    def bump_minor(self): return SemVer(f"{self.major}.{self.minor+1}.0")
    def bump_patch(self): return SemVer(f"{self.major}.{self.minor}.{self.patch+1}")

def satisfies(version, constraint):
    v = SemVer(version) if isinstance(version, str) else version
    c = constraint.strip()
    if c.startswith("^"):
        base = SemVer(c[1:])
        upper = base.bump_major()
        return v >= base and v < upper
    elif c.startswith("~"):
        base = SemVer(c[1:])
        upper = base.bump_minor()
        return v >= base and v < upper
    elif c.startswith(">="):
        return v >= SemVer(c[2:].strip())
    elif c.startswith("<="):
        return v <= SemVer(c[2:].strip())
    elif c.startswith(">"):
        return v > SemVer(c[1:].strip())
    elif c.startswith("<"):
        return v < SemVer(c[1:].strip())
    elif c.startswith("="):
        return v == SemVer(c[1:].strip())
    else:
        return v == SemVer(c)

def test():
    v1 = SemVer("1.2.3")
    assert str(v1) == "1.2.3"
    assert v1.major == 1 and v1.minor == 2 and v1.patch == 3
    v2 = SemVer("1.2.4")
    assert v1 < v2
    pre = SemVer("1.0.0-alpha")
    rel = SemVer("1.0.0")
    assert pre < rel
    assert str(v1.bump_minor()) == "1.3.0"
    assert satisfies("1.5.0", "^1.2.0")
    assert not satisfies("2.0.0", "^1.2.0")
    assert satisfies("1.2.5", "~1.2.0")
    assert not satisfies("1.3.0", "~1.2.0")
    assert satisfies("2.0.0", ">=1.0.0")
    print("  semver: ALL TESTS PASSED")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "test": test()
    else: print(f"Parse: {SemVer(sys.argv[2] if len(sys.argv) > 2 else '1.0.0')}")
