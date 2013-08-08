#!/usr/bin/env python





import datetime

import delegate





def update_release():
  # TODO: What is a good release expiration time?
  time_delta = datetime.timedelta(days=7)
  delegate.update_release(time_delta, compress=True)





if __name__ == '__main__':
  update_release()





