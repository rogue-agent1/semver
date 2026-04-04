# semver

Semantic versioning toolkit — parse, bump, compare, sort, validate, range check.

## Usage

```bash
python3 semver.py parse "v2.1.3-beta.1+build.42"
python3 semver.py bump 1.2.3 minor
python3 semver.py bump 1.2.3 major --pre rc.1
python3 semver.py compare 1.2.3 2.0.0
python3 semver.py validate "1.0.0-alpha"
python3 semver.py range 1.5.0 "^1.0.0"
python3 semver.py range 1.2.5 "~1.2.0"
echo -e "2.0.0\n1.0.0\n0.9.0" | python3 semver.py sort
```

## Features

- Parse with pre-release and build metadata
- Bump major/minor/patch with optional pre-release
- Compare with correct pre-release precedence
- Sort versions from stdin
- Range constraints: ^, ~, >=, <=, >, <, =
- Zero dependencies
