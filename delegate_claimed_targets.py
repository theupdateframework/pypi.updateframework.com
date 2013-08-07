#!/usr/bin/env python





import delegate





def update_claimed_targets():
  # For the moment, delegate no target to the "claimed" targets role.
  relative_delegated_paths = []
  delegate.make_delegation(delegate.TARGETS_ROLE_NAME,
                           delegate.CLAIMED_TARGETS_ROLE_NAME,
                           relative_delegated_paths=relative_delegated_paths)





if __name__ == '__main__':
  update_claimed_targets()





