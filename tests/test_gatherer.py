import sys; sys.path.insert(0, '../')
from octopus.gather import Gather
import time
import numpy as np
from datetime import datetime
IP = "10.16.5.93"
gatherer = Gather()
gatherer.main()
start = time.time()

while time.time()-start < 7.5:
    gatherer.main()

not_nans = (~np.isnan(gatherer.dataMemory[0])).sum()
print("Good points: ", not_nans)
print("-> ", not_nans/gatherer.sr, " seconds")