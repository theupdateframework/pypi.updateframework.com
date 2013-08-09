#!/usr/bin/env python





import datetime

import delegate





def update_claimed_targets():
  # For the moment, sign no target with the "claimed" targets role.
  claimed_relative_target_paths = []
  delegate.update_targets_metadata(delegate.CLAIMED_TARGETS_ROLE_NAME,
                                   claimed_relative_target_paths,
                                   datetime.timedelta(days=365))

  # For the moment, delegate no target to the "claimed" targets role.
  relative_delegated_paths = []
  delegate.make_delegation(delegate.TARGETS_ROLE_NAME,
                           delegate.CLAIMED_TARGETS_ROLE_NAME,
                           relative_delegated_paths=relative_delegated_paths)





if __name__ == '__main__':
  update_claimed_targets()





