#!/usr/bin/env python3
"""semver - Semantic versioning toolkit.

Parse, compare, bump, and validate semver strings. Zero dependencies.
"""

import argparse
import re
import sys


SEMVER_RE = re.compile(
    r'^v?(?P<major>\d+)\.(?P<minor>\d+)\.(?P<patch>\d+)'
    r'(?:-(?P<pre>[0-9A-Za-z\-.]+))?'
    r'(?:\+(?P<build>[0-9A-Za-z\-.]+))?$'
)


def parse(s):
    m = SEMVER_RE.match(s.strip())
    if not m:
        return None
    return {
        "major": int(m.group("major")),
        "minor": int(m.group("minor")),
        "patch": int(m.group("patch")),
        "pre": m.group("pre") or "",
        "build": m.group("build") or "",
    }


def to_str(v):
    s = f"{v['major']}.{v['minor']}.{v['patch']}"
    if v.get("pre"):
        s += f"-{v['pre']}"
    if v.get("build"):
        s += f"+{v['build']}"
    return s


def cmp_key(v):
    # Pre-release has lower precedence than release
    pre_parts = []
    if v["pre"]:
        for p in v["pre"].split("."):
            pre_parts.append((0, int(p)) if p.isdigit() else (1, p))
    else:
        pre_parts = [(2,)]  # no pre = higher than any pre
    return (v["major"], v["minor"], v["patch"], pre_parts)


def cmd_parse(args):
    v = parse(args.version)
    if not v:
        print(f"Invalid semver: {args.version}")
        sys.exit(1)
    for k, val in v.items():
        print(f"  {k}: {val}")


def cmd_bump(args):
    v = parse(args.version)
    if not v:
        print(f"Invalid semver: {args.version}")
        sys.exit(1)
    v["pre"] = ""
    v["build"] = ""
    if args.part == "major":
        v["major"] += 1
        v["minor"] = 0
        v["patch"] = 0
    elif args.part == "minor":
        v["minor"] += 1
        v["patch"] = 0
    elif args.part == "patch":
        v["patch"] += 1
    if args.pre:
        v["pre"] = args.pre
    print(to_str(v))


def cmd_compare(args):
    a = parse(args.v1)
    b = parse(args.v2)
    if not a or not b:
        print("Invalid semver")
        sys.exit(1)
    ka, kb = cmp_key(a), cmp_key(b)
    if ka < kb:
        print(f"{args.v1} < {args.v2}")
    elif ka > kb:
        print(f"{args.v1} > {args.v2}")
    else:
        print(f"{args.v1} = {args.v2}")


def cmd_sort(args):
    versions = []
    for line in sys.stdin:
        v = parse(line.strip())
        if v:
            versions.append((cmp_key(v), line.strip()))
    versions.sort(reverse=args.reverse)
    for _, s in versions:
        print(s)


def cmd_validate(args):
    v = parse(args.version)
    if v:
        print(f"✓ Valid: {to_str(v)}")
    else:
        print(f"✗ Invalid: {args.version}")
        sys.exit(1)


def cmd_range(args):
    """Check if version satisfies a simple range constraint."""
    v = parse(args.version)
    if not v:
        print("Invalid version")
        sys.exit(1)
    constraint = args.constraint
    # Parse constraint: ^1.2.3, ~1.2.3, >=1.0.0, <2.0.0, 1.x, 1.2.x
    ops = {">=": lambda a, b: a >= b, "<=": lambda a, b: a <= b,
           ">": lambda a, b: a > b, "<": lambda a, b: a < b,
           "=": lambda a, b: a == b}
    for op, fn in sorted(ops.items(), key=lambda x: -len(x[0])):
        if constraint.startswith(op):
            target = parse(constraint[len(op):].strip())
            if not target:
                print(f"Invalid constraint target")
                sys.exit(1)
            kv, kt = cmp_key(v), cmp_key(target)
            if fn(kv, kt):
                print(f"✓ {to_str(v)} satisfies {constraint}")
            else:
                print(f"✗ {to_str(v)} does not satisfy {constraint}")
                sys.exit(1)
            return

    if constraint.startswith("^"):
        target = parse(constraint[1:])
        if not target:
            print("Invalid constraint")
            sys.exit(1)
        # Caret: >=target, <next major
        ok = (v["major"] == target["major"] and cmp_key(v) >= cmp_key(target))
        sym = "✓" if ok else "✗"
        print(f"{sym} {to_str(v)} {'satisfies' if ok else 'does not satisfy'} {constraint}")
        if not ok:
            sys.exit(1)
    elif constraint.startswith("~"):
        target = parse(constraint[1:])
        if not target:
            print("Invalid constraint")
            sys.exit(1)
        # Tilde: >=target, <next minor
        ok = (v["major"] == target["major"] and v["minor"] == target["minor"]
              and cmp_key(v) >= cmp_key(target))
        sym = "✓" if ok else "✗"
        print(f"{sym} {to_str(v)} {'satisfies' if ok else 'does not satisfy'} {constraint}")
        if not ok:
            sys.exit(1)
    else:
        target = parse(constraint)
        if target:
            ok = cmp_key(v) == cmp_key(target)
            sym = "✓" if ok else "✗"
            print(f"{sym} {to_str(v)} {'==' if ok else '!='} {constraint}")
            if not ok:
                sys.exit(1)


def main():
    p = argparse.ArgumentParser(description="Semantic versioning toolkit")
    sub = p.add_subparsers(dest="cmd")

    sub.add_parser("parse", help="Parse version").add_argument("version")

    bp = sub.add_parser("bump", help="Bump version")
    bp.add_argument("version")
    bp.add_argument("part", choices=["major", "minor", "patch"])
    bp.add_argument("--pre", help="Pre-release tag")

    cp = sub.add_parser("compare", help="Compare two versions")
    cp.add_argument("v1")
    cp.add_argument("v2")

    sp = sub.add_parser("sort", help="Sort versions from stdin")
    sp.add_argument("-r", "--reverse", action="store_true")

    sub.add_parser("validate", help="Validate version").add_argument("version")

    rp = sub.add_parser("range", help="Check version against constraint")
    rp.add_argument("version")
    rp.add_argument("constraint", help="^1.0.0, ~1.2.0, >=1.0.0, <2.0.0")

    args = p.parse_args()
    if not args.cmd:
        p.print_help()
        sys.exit(1)
    {"parse": cmd_parse, "bump": cmd_bump, "compare": cmd_compare,
     "sort": cmd_sort, "validate": cmd_validate, "range": cmd_range}[args.cmd](args)


if __name__ == "__main__":
    main()
