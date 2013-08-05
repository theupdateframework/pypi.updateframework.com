#!/usr/bin/env python





import delegate





def make_delegation():
  # For the moment, delegate no target to the "recently-claimed" targets role.
  # TODO: This needs to happen only once.
  relative_delegated_paths = []
  delegate.make_delegation(delegate.TARGETS_ROLE_NAME,
                           delegate.RECENTLY_CLAIMED_TARGETS_ROLE_NAME,
                           relative_delegated_paths)





if __name__ == '__main__':
  make_delegation()





