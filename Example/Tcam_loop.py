from VotschTechnikClimateChamber.ClimateChamber import ClimateChamber
from colorama import Fore, Back, Style
import datetime
import numpy as np

ip_1 = '192.168.0.21'
ip_2 = '192.168.0.11'
tcam = ClimateChamber(
        ip=ip_2,  # Use the IP address shown in the display of the climate chamber.
        temperature_min=-45,  # Minimum limit, will rise an error if try to set temperature lower than this.
        temperature_max=120,  # Maximum limit, will rise an error if try to set temperature higher than this.
    )


test_temp = [-40, -20, 25, 60, 70, 85, 95]

wait_after = 30  # dwell time in minutes (before test at given T starts)

for temp in test_temp:

    tcam.set_and_wait(temp, wait_after)