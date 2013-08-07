#!/usr/bin/env python





import datetime

import delegate





def update_timestamp():
  # TODO: What is a good timestamp expiration time?
  time_delta = datetime.timedelta(days=1)
  delegate.update_timestamp(time_delta)





if __name__ == '__main__':
  update_timestamp()





