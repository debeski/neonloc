# Releasing NeonLoc

Releases are tag-driven through `.github/workflows/release.yml`.

## One-Time Setup

1. In GitHub, create an environment named `pypi`.
2. In PyPI, add a trusted publisher for:
   - PyPI project: `neonloc`
   - Owner: `debeski`
   - Repository: `neonloc`
   - Workflow: `release.yml`
   - Environment: `pypi`
3. No PyPI token secret is required when Trusted Publishing is active.

## Release Steps

1. Update `VERSION` to the new package version.
2. Update `CHANGELOG.md` under the matching `## vX.Y.Z` section.
3. Commit and push the version changes.
4. Create and push the matching tag:

```bash
version="$(cat VERSION)"
git tag -a "v${version}" -m "v${version}"
git push origin main
git push origin "v${version}"
```

`VERSION` is the single source of truth for package metadata. `pyproject.toml` reads it through setuptools dynamic versioning, and `neonloc.__version__` reads the installed package metadata generated from it.

The workflow verifies the tag matches `VERSION`, builds the sdist and wheel, verifies the built wheel metadata matches `VERSION`, publishes to PyPI through the `pypi` environment, and creates a GitHub Release with the matching changelog section.
