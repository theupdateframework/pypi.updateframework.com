Automation for creating, updating and destroying [a TUF-secured PyPI
mirror](https://github.com/dachshund/pip/wiki/PyPI-over-TUF).

## Scripts

+ setup.sh: Setup pypi.updateframework.com.
    + setup1.sh: Create top-level TUF root roles.
        - quickstart.sh: Drive quickstart.py.
    - setup2.sh: Sync with PyPI.
    + setup3.sh: Create or update delegated target roles, or their delegations.
        - gen-rsa-key.sh: Drive signercli.py --genrsakey.
        - list-keys.sh: Drive signercli.py --listkeys.
        - make-delegation.sh: Drive signercli.py --makedelegation.
    + setup4.sh: Make a new release and timestamp.
        - make-release.sh: Drive signercli.py --makerelease.
        - make-timestamp.sh: Drive signercli.py --maketimestamp.
- destroy.sh: Destroy pypi.updateframework.com.
- environment.sh: Shared environmental variables.

## Workflow

### Create

```bash
# Create top-level/root roles for PyPI.
$ ./setup1.sh
```

### Update
```bash
# Sync with PyPI.
$ ./setup2.sh
# Update targets metadata.
$ ./setup3.sh
# Timestamp a release.
$ ./setup4.sh
```

### Delete

```bash
# Delete all TUF metadata.
$ ./destroy.sh
```

## Notes

- On a Debian system, you may need sudo to run a command in these scripts.
+ In order to drive a purely automated process of securing a PyPI mirror with
  TUF metadata, we are using some otherwise weak security practices. Do **NOT**
  use these practices for production purposes!
    - Passing passwords on the command line is a security issue. Ideally, [TUF
    repository tools could read from input
    files](https://github.com/akonst/tuf/issues/52).
