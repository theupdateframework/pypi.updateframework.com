Automation for creating, updating and destroying [a TUF-secured PyPI
mirror](https://github.com/dachshund/pip/wiki/PyPI-over-TUF).

## Scripts

+ setup.sh: Setup pypi.updateframework.com.
    + setup1.sh: Create top-level TUF root roles.
        - quickstart.sh: Drive quickstart.py.
    - setup2.sh: Sync with PyPI.
    + setup3.sh: Create and update delegated target roles, or their delegations.
        - gen-rsa-key.sh: Drive signercli.py --genrsakey.
        - list-keys.sh: Drive signercli.py --listkeys.
        - make-delegation.sh: Drive signercli.py --makedelegation.
    + setup4.sh: Make a new release and timestamp.
        - make-release.sh: Drive signercli.py --makerelease.
        - make-timestamp.sh: Drive signercli.py --maketimestamp.
- destroy.sh: Destroy pypi.updateframework.com.
- environment.sh: Shared environmental variables.

## Notes

- On a Debian system, you may need sudo to run these scripts.
+ In order to drive a purely automated process of securing a PyPI mirror with
  TUF metadata, we are using some otherwise bad security practices. Do *not*
  use these practices for production purposes!
    - Passing passwords on the command line is a security flaw. Ideally,
      quickstart.py and signercli.py could read from input files. 
