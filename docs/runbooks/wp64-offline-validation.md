# WP6.4 offline contract validation

Use Python unittest discovery from the repository root to run all offline tests.

The validator entry point is the sentinel_forge.validate Python module. It can
read a local JSON bundle path or JSON supplied on standard input.

Exit status 0 means the supplied bundle passed the implemented logical checks.
Exit status 1 means validation rejected the bundle. Exit status 2 means the
input could not be parsed or read.

A successful validation is not transfer, release, deployment, or operational
authorization.
