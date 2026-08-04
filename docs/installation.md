# Installation and Release Use

## Public repository status

The full application source and executable are not yet published in this repository. This guide currently documents the verified portable Windows handoff process.

## Client use of a portable release

A prepared release bundle is intended to be used as follows:

1. Download or receive the versioned release ZIP from a trusted source.
2. Verify the ZIP checksum when a `.sha256` file is supplied.
3. Extract the complete ZIP to a local folder.
4. Keep all delivered files together.
5. Double-click `START-HERE.cmd`.
6. In the application, choose **Open Contract**.
7. Open one of the safe files in `sample_contracts/` for an initial demonstration.
8. Choose **Scan Contract** and review the resulting score, findings, and summary.

## Integrity verification

The release includes two verification methods:

- `VERIFY-CHECKSUMS.ps1` verifies files inside the extracted bundle.
- The ZIP `.sha256` file verifies the compressed archive before extraction.

Only run releases obtained from a trusted source. A matching checksum confirms file integrity but does not independently establish who produced the file.

## Windows SmartScreen

Unsigned Windows executables may trigger a SmartScreen warning. The current release tooling records whether a build is signed. Users should only bypass a warning when they trust the release source and have verified the supplied checksum.

## Local data notes

The verified quick-start configuration indicates that local scan history is stored under:

```text
Documents\Contract Review Assistant Exports\repository
```

Exported reports are saved to the location selected by the user in the Save dialog.

## Developer setup

Developer installation steps cannot be documented accurately until the sanitized dependency files and complete source tree are reviewed. Future documentation will include:

- Supported Python version
- Virtual-environment setup
- Dependency installation
- Development entry point
- Test execution
- Windows executable build process
- Release-bundle command
