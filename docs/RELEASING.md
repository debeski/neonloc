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

1. Update `pyproject.toml`, `VERSION`, and `src/neonloc/__init__.py` to the same new version.
2. Update `CHANGELOG.md` under `## vX.Y.Z`.
3. Commit and push the version changes.
4. Create and push the matching tag:

```bash
git tag -a vX.Y.Z -m "vX.Y.Z"
git push origin main
git push origin vX.Y.Z
```

The workflow verifies the tag matches package metadata, builds the sdist and wheel, publishes to PyPI through the `pypi` environment, and creates a GitHub Release with the matching changelog section.
