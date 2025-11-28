from VotschTechnikClimateChamber.ClimateChamber import ClimateChamber
from colorama import Fore, Back, Style
import datetime
import numpy as np

import Logging_class as logclass

folder = r"C:\Temp"
file_name = "cccm_temperature_log.txt"
logger = logclass.txt_logger()
logger.set_folder(folder)
logger.set_file_name(file_name)
logger.init("chamber_")


ip_1 = '192.168.0.31'
ip_2 = '192.168.0.11'
tcam = ClimateChamber(
        ip=ip_1,  # Use the IP address shown in the display of the climate chamber.
        temperature_min=-45,  # Minimum limit, will rise an error if try to set temperature lower than this.
        temperature_max=120,  # Maximum limit, will rise an error if try to set temperature higher than this.
    )


test_temp = [85, 75, 65, 55, 45, 35, 25, 15, 5, -5, -15, -25, -35, -40]
# test_temp = [25]
wait_after = 10  # dwell time in minutes (before test at given T starts)

for temp in test_temp:
    current_t = tcam.temperature_measured
    logger.print_and_log(f"temp: {current_t}")
    tcam.set_and_wait(temp, wait_after)
    logger.print_and_log(f"temp: {current_t}")
tcam.set_and_wait(25,0)
tcam.stop()
logger.stop_logging()