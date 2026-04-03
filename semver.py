#!/usr/bin/env python3
"""semver - Semantic versioning parser, comparator, and bumper.

Parse, compare, sort, bump, and validate semantic versions per semver.org spec.

Usage:
    semver parse 1.2.3-beta.1+build.42    # parse into components
    semver compare 1.2.3 2.0.0            # compare two versions
    semver sort 1.0.0 2.1.0 1.5.3 0.9.0   # sort versions
    semver bump 1.2.3 --major              # → 2.0.0
    semver bump 1.2.3 --minor              # → 1.3.0
    semver bump 1.2.3 --patch              # → 1.2.4
    semver bump 1.2.3 --pre beta           # → 1.2.4-beta.1
    semver range ">=1.0.0 <2.0.0" 1.5.3   # check if version matches range
    semver validate 1.2.3                  # check if valid semver
"""
import argparse
import re
import sys
from functools import cmp_to_key

SEMVER_RE = re.compile(
    r'^v?(?P<major>0|[1-9]\d*)'
    r'\.(?P<minor>0|[1-9]\d*)'
    r'\.(?P<patch>0|[1-9]\d*)'
    r'(?:-(?P<pre>[0-9A-Za-z\-]+(?:\.[0-9A-Za-z\-]+)*))?'
    r'(?:\+(?P<build>[0-9A-Za-z\-]+(?:\.[0-9A-Za-z\-]+)*))?$'
)


class SemVer:
    __slots__ = ('major', 'minor', 'patch', 'pre', 'build')

    def __init__(self, major, minor, patch, pre=None, build=None):
        self.major = major
        self.minor = minor
        self.patch = patch
        self.pre = pre  # tuple of parts or None
        self.build = build  # string or None

    @classmethod
    def parse(cls, s: str) -> 'SemVer':
        m = SEMVER_RE.match(s.strip())
        if not m:
            raise ValueError(f"Invalid semver: {s}")
        pre = None
        if m.group('pre'):
            parts = []
            for p in m.group('pre').split('.'):
                parts.append(int(p) if p.isdigit() else p)
            pre = tuple(parts)
        return cls(
            int(m.group('major')), int(m.group('minor')), int(m.group('patch')),
            pre, m.group('build')
        )

    def __str__(self):
        s = f"{self.major}.{self.minor}.{self.patch}"
        if self.pre:
            s += f"-{'.'.join(str(p) for p in self.pre)}"
        if self.build:
            s += f"+{self.build}"
        return s

    def _cmp_tuple(self):
        # Pre-release has lower precedence than release
        # No pre = release = higher than any pre-release
        if self.pre is None:
            pre_key = (1,)  # release sorts after pre-release
        else:
            # Each part: numeric < alpha, shorter < longer
            pre_key = (0,) + tuple((0, p) if isinstance(p, int) else (1, p) for p in self.pre)
        return (self.major, self.minor, self.patch, pre_key)

    def __lt__(self, o): return self._cmp_tuple() < o._cmp_tuple()
    def __le__(self, o): return self._cmp_tuple() <= o._cmp_tuple()
    def __gt__(self, o): return self._cmp_tuple() > o._cmp_tuple()
    def __ge__(self, o): return self._cmp_tuple() >= o._cmp_tuple()
    def __eq__(self, o): return self._cmp_tuple() == o._cmp_tuple()
    def __ne__(self, o): return self._cmp_tuple() != o._cmp_tuple()


def cmd_parse(args):
    v = SemVer.parse(args.version)
    print(f"  Version:    {v}")
    print(f"  Major:      {v.major}")
    print(f"  Minor:      {v.minor}")
    print(f"  Patch:      {v.patch}")
    print(f"  Pre-release:{' ' + '.'.join(str(p) for p in v.pre) if v.pre else ' (none)'}")
    print(f"  Build:      {v.build or '(none)'}")
    print(f"  Stable:     {'yes' if v.major > 0 and v.pre is None else 'no'}")


def cmd_compare(args):
    a = SemVer.parse(args.v1)
    b = SemVer.parse(args.v2)
    if a < b:
        print(f"  {a} < {b}")
    elif a > b:
        print(f"  {a} > {b}")
    else:
        print(f"  {a} == {b}")


def cmd_sort(args):
    versions = [SemVer.parse(v) for v in args.versions]
    versions.sort(reverse=args.desc)
    for v in versions:
        print(f"  {v}")


def cmd_bump(args):
    v = SemVer.parse(args.version)
    if args.major:
        v = SemVer(v.major + 1, 0, 0)
    elif args.minor:
        v = SemVer(v.major, v.minor + 1, 0)
    elif args.pre:
        label = args.pre
        if v.pre and len(v.pre) >= 2 and v.pre[0] == label and isinstance(v.pre[1], int):
            v = SemVer(v.major, v.minor, v.patch, (label, v.pre[1] + 1))
        else:
            v = SemVer(v.major, v.minor, v.patch + 1, (label, 1))
    else:  # patch (default)
        v = SemVer(v.major, v.minor, v.patch + 1)
    print(v)


def cmd_range(args):
    """Check if version satisfies a range expression."""
    v = SemVer.parse(args.version)
    expr = args.range_expr

    # Simple range parser: supports >=, <=, >, <, =, space-separated (AND)
    ops = {">=": '__ge__', "<=": '__le__', ">": '__gt__', "<": '__lt__', "=": '__eq__'}
    parts = re.findall(r'([><=]+)\s*([\w.\-+]+)', expr)

    if not parts:
        print(f"Error: Cannot parse range: {expr}", file=sys.stderr)
        sys.exit(1)

    for op_str, ver_str in parts:
        target = SemVer.parse(ver_str)
        op = ops.get(op_str)
        if not op:
            print(f"Error: Unknown operator: {op_str}", file=sys.stderr)
            sys.exit(1)
        if not getattr(v, op)(target):
            print(f"  ❌ {v} does NOT satisfy {expr}")
            sys.exit(1)

    print(f"  ✅ {v} satisfies {expr}")


def cmd_validate(args):
    try:
        v = SemVer.parse(args.version)
        print(f"  ✅ Valid semver: {v}")
    except ValueError:
        print(f"  ❌ Invalid semver: {args.version}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Semantic versioning tool")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("parse", help="Parse version")
    p.add_argument("version")

    p = sub.add_parser("compare", help="Compare two versions")
    p.add_argument("v1")
    p.add_argument("v2")

    p = sub.add_parser("sort", help="Sort versions")
    p.add_argument("versions", nargs="+")
    p.add_argument("--desc", action="store_true")

    p = sub.add_parser("bump", help="Bump version")
    p.add_argument("version")
    g = p.add_mutually_exclusive_group()
    g.add_argument("--major", action="store_true")
    g.add_argument("--minor", action="store_true")
    g.add_argument("--patch", action="store_true", default=True)
    g.add_argument("--pre", metavar="LABEL")

    p = sub.add_parser("range", help="Check version against range")
    p.add_argument("range_expr")
    p.add_argument("version")

    p = sub.add_parser("validate", help="Validate semver string")
    p.add_argument("version")

    args = parser.parse_args()
    {"parse": cmd_parse, "compare": cmd_compare, "sort": cmd_sort,
     "bump": cmd_bump, "range": cmd_range, "validate": cmd_validate}[args.command](args)


if __name__ == "__main__":
    main()
