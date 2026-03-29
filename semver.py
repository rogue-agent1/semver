#!/usr/bin/env python3
"""semver - Semantic versioning parser, comparator, and range checker."""
import sys, re

class Version:
    def __init__(self, major, minor=0, patch=0, pre=None):
        self.major, self.minor, self.patch = major, minor, patch
        self.pre = pre
    @classmethod
    def parse(cls, s):
        m = re.match(r"^v?(\d+)(?:\.(\d+))?(?:\.(\d+))?(?:-(\S+))?$", s)
        if not m: raise ValueError(f"Invalid version: {s}")
        return cls(int(m.group(1)), int(m.group(2) or 0), int(m.group(3) or 0), m.group(4))
    def _tuple(self):
        return (self.major, self.minor, self.patch, 0 if self.pre is None else -1, self.pre or "")
    def __lt__(self, o): return self._tuple() < o._tuple()
    def __le__(self, o): return self._tuple() <= o._tuple()
    def __eq__(self, o): return self._tuple() == o._tuple()
    def __gt__(self, o): return self._tuple() > o._tuple()
    def __ge__(self, o): return self._tuple() >= o._tuple()
    def __repr__(self):
        s = f"{self.major}.{self.minor}.{self.patch}"
        if self.pre: s += f"-{self.pre}"
        return s
    def bump_major(self): return Version(self.major+1, 0, 0)
    def bump_minor(self): return Version(self.major, self.minor+1, 0)
    def bump_patch(self): return Version(self.major, self.minor, self.patch+1)

def satisfies(version, constraint):
    v = Version.parse(version) if isinstance(version, str) else version
    parts = constraint.split()
    if len(parts) == 1:
        c = parts[0]
        if c.startswith(">="): return v >= Version.parse(c[2:])
        if c.startswith("<="): return v <= Version.parse(c[2:])
        if c.startswith(">"): return v > Version.parse(c[1:])
        if c.startswith("<"): return v < Version.parse(c[1:])
        if c.startswith("^"):
            base = Version.parse(c[1:])
            return v >= base and v < base.bump_major()
        if c.startswith("~"):
            base = Version.parse(c[1:])
            return v >= base and v < base.bump_minor()
        return v == Version.parse(c)
    return all(satisfies(v, p) for p in parts)

def test():
    v = Version.parse("1.2.3")
    assert v.major == 1 and v.minor == 2 and v.patch == 3
    assert Version.parse("1.2.3") < Version.parse("1.2.4")
    assert Version.parse("1.2.3") < Version.parse("1.3.0")
    assert Version.parse("2.0.0") > Version.parse("1.9.9")
    assert Version.parse("1.0.0-alpha") < Version.parse("1.0.0")
    assert satisfies("1.5.0", ">=1.0.0")
    assert not satisfies("0.9.0", ">=1.0.0")
    assert satisfies("1.2.3", "^1.0.0")
    assert not satisfies("2.0.0", "^1.0.0")
    assert satisfies("1.2.5", "~1.2.0")
    assert not satisfies("1.3.0", "~1.2.0")
    b = Version.parse("1.2.3")
    assert str(b.bump_major()) == "2.0.0"
    assert str(b.bump_minor()) == "1.3.0"
    print("semver: all tests passed")

if __name__ == "__main__":
    test() if "--test" in sys.argv else print("Usage: semver.py --test")
