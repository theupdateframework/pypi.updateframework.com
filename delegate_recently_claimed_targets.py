#!/usr/bin/env python





import delegate





def update_recently_claimed_targets():
  # For the moment, delegate no target to the "recently-claimed" targets role.
  relative_delegated_paths = []
  delegate.make_delegation(delegate.TARGETS_ROLE_NAME,
                           delegate.RECENTLY_CLAIMED_TARGETS_ROLE_NAME,
                           relative_delegated_paths=relative_delegated_paths)





if __name__ == '__main__':
  update_recently_claimed_targets()





