Automation for creating, updating and destroying [a TUF-secured PyPI
mirror](https://github.com/dachshund/pip/wiki/PyPI-over-TUF).

## Scripts

+ setup.sh: Setup pypi.updateframework.com.
    + setup1.sh: Create top-level TUF root roles.
        - quickstart.sh: Drive quickstart.py.
    - setup2.sh: Sync with PyPI.
    + setup3.sh: Create or update delegated target roles, or their delegations.
        - delegate_claimed_targets.py: Promote projects from the
        "recently-claimed" targets role to the "claimed" targets role.
        - delegate_recently_claimed_targets.py: Promote targets as projects
        from the "unclaimed" targets role to the "recently-claimed" targets
        role.
        - delegate_unclaimed_targets.py: Delegate all targets by default to the
        "unclaimed" targets role.
    + setup4.sh: Make a new release and timestamp.
        - make_release.py: Sign a new release.
        - make_timestamp.py: Sign a new timestamp.
- check.py: A library to check metadata against data.
- delegate.py: A library to delegate and update release, targets or timestamp.
- destroy.sh: Minimally destroy pypi.updateframework.com.
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
# Caution: Delete all TUF metadata!
$ ./destroy.sh
```

## Output

By default (unless you modify the environment variables in `environment.sh`),
`setup.sh` would generate output like this:

+ `~/pypi.updateframework.com`
    - `~/pypi.updateframework.com/bandersnatch.conf`
    + `~/pypi.updateframework.com/pypi.python.org`
        - Your very own PyPI mirror.
    + `~/pypi.updateframework.com/quickstart`
        + `~/pypi.updateframework.com/quickstart/client`
            - Initial TUF metadata you would distribute with your PyPI
            installer.
        + `~/pypi.updateframework.com/quickstart/keystore`
            - All the PyPI keys, all of which you would normally certainly not
            keep in the same place; some of them should be offline, while
            others should be online.
        + `~/pypi.updateframework.com/quickstart/repository`
            - TUF metadata for PyPI that you would publicly serve.
    - `~/pypi.updateframework.com/virtualenv-XYZ`
    - `~/pypi.updateframework.com/virtualenv-XYZ.tar.gz`
    - `~/pypi.updateframework.com/virtual_python`

## Notes

- On a Debian system, you may need sudo privilege to run a command in these
  scripts.
+ In order to drive a purely automated process of securing a PyPI mirror with
  TUF metadata, we are using some otherwise weak security practices. Do **NOT**
  use these practices for production purposes!
    - Passing passwords on the command line is a security issue. Ideally, [TUF
    repository tools could read from input
    files](https://github.com/akonst/tuf/issues/52).
