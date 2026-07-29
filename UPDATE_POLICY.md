# NEO Rating — Controlled Automatic Updates

## Distribution channels

- Source code: private repository `cjacqueslf/NEORating`.
- Windows packages and update manifests: public repository
  `cjacqueslf/NEORating-Releases`.
- Scientific upstream: official MPC `digest2` package and
  `Smithsonian/mpc-public` repository.

The public release repository must never contain source code, credentials,
observations, logs, or machine-specific configuration.

## Runtime behavior

The application checks the latest stable GitHub Release in a background worker.
Network unavailability never blocks startup or scientific calculation.

An update is accepted for staging only when:

1. the release is neither a draft nor a prerelease;
2. the release contains `neo-rating-update.json`;
3. the manifest schema is supported;
4. the manifest version matches the GitHub release tag;
5. the named package exists in the same release;
6. package size matches the manifest and is within the hard limit;
7. the package SHA-256 matches after download;
8. the version is newer than the installed application.

Downloads use a temporary file inside the version-specific staging directory.
The verified file replaces the temporary file atomically. Partial or rejected
downloads are removed.

## Manifest schema 1

```json
{
  "schema_version": 1,
  "version": "0.2.0",
  "digest2_version": "2.8.2",
  "asset_name": "NEORating-0.2.0-win64.zip",
  "asset_size": 12345678,
  "asset_sha256": "64 lowercase hexadecimal characters"
}
```

## Installation boundary

Version 0.1.0 implements automatic discovery, download, verification and
staging. The Windows installer and packaged layout exist, but atomic invocation
and rollback still require the external updater helper. The GUI must not claim
that installation has completed until that helper confirms it.

Scientific updates are distributed only as a complete tested NEO Rating
release. Runtime code never downloads individual model or configuration files
directly from the MPC.
