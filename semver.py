#!/usr/bin/env python3
"""semver - Semantic versioning parser, comparator, and range checker."""
import sys, re

class Version:
    def __init__(self, major, minor=0, patch=0, prerelease=None, build=None):
        self.major = major
        self.minor = minor
        self.patch = patch
        self.prerelease = prerelease
        self.build = build
    @classmethod
    def parse(cls, s):
        m = re.match(r"^v?(\d+)\.(\d+)\.(\d+)(?:-([\.\w-]+))?(?:\+([\w.]+))?$", s)
        if not m:
            raise ValueError(f"Invalid semver: {s}")
        return cls(int(m.group(1)), int(m.group(2)), int(m.group(3)), m.group(4), m.group(5))
    def __str__(self):
        s = f"{self.major}.{self.minor}.{self.patch}"
        if self.prerelease:
            s += f"-{self.prerelease}"
        if self.build:
            s += f"+{self.build}"
        return s
    def _tuple(self):
        pre = (0, self.prerelease or "") if self.prerelease else (1, "")
        return (self.major, self.minor, self.patch, pre[0], pre[1])
    def __eq__(self, other): return self._tuple() == other._tuple()
    def __lt__(self, other): return self._tuple() < other._tuple()
    def __le__(self, other): return self._tuple() <= other._tuple()
    def __gt__(self, other): return self._tuple() > other._tuple()
    def __ge__(self, other): return self._tuple() >= other._tuple()
    def bump_major(self): return Version(self.major + 1)
    def bump_minor(self): return Version(self.major, self.minor + 1)
    def bump_patch(self): return Version(self.major, self.minor, self.patch + 1)

def satisfies(version, constraint):
    v = Version.parse(version) if isinstance(version, str) else version
    parts = re.split(r"\s+", constraint.strip())
    for part in parts:
        m = re.match(r"^([><=!^~]+)(.+)$", part)
        if not m:
            if Version.parse(part) != v:
                return False
            continue
        op, ver_str = m.group(1), m.group(2)
        cv = Version.parse(ver_str)
        if op == ">=": ok = v >= cv
        elif op == "<=": ok = v <= cv
        elif op == ">": ok = v > cv
        elif op == "<": ok = v < cv
        elif op == "=": ok = v == cv
        elif op == "!=": ok = v != cv
        elif op == "^":
            ok = v >= cv and v.major == cv.major
        elif op == "~":
            ok = v >= cv and v.major == cv.major and v.minor == cv.minor
        else:
            ok = False
        if not ok:
            return False
    return True

def test():
    v = Version.parse("1.2.3")
    assert str(v) == "1.2.3"
    assert v == Version.parse("1.2.3")
    assert v > Version.parse("1.2.2")
    assert v < Version.parse("1.3.0")
    # prerelease < release
    assert Version.parse("1.0.0-alpha") < Version.parse("1.0.0")
    # bump
    assert str(v.bump_major()) == "2.0.0"
    assert str(v.bump_minor()) == "1.3.0"
    assert str(v.bump_patch()) == "1.2.4"
    # satisfies
    assert satisfies("1.2.3", ">=1.0.0 <2.0.0")
    assert satisfies("1.2.3", "^1.0.0")
    assert not satisfies("2.0.0", "^1.0.0")
    assert satisfies("1.2.5", "~1.2.0")
    assert not satisfies("1.3.0", "~1.2.0")
    print("OK: semver")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        test()
    else:
        print("Usage: semver.py test")
