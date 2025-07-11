import time
from VotschTechnikClimateChamber.ClimateChamber import ClimateChamber
from colorama import Fore, Back, Style
import datetime
ip_1 = '192.168.0.21'
ip_2 = '192.168.0.11'
chamber = ClimateChamber(
        ip=ip_2,  # Use the IP address shown in the display of the climate chamber.
        temperature_min=-45,  # Minimum limit, will rise an error if try to set temperature lower than this.
        temperature_max=120,  # Maximum limit, will rise an error if try to set temperature higher than this.
    )

def range_check(val, min, max, val_name):
    if val > max:
        print(f"Wrong {val_name}: {val}. Max value should be less then {max}")
        val = max
    if val < min:
        print(f"Wrong {val_name}: {val}. Should be >= {min}")
        val = min
    return val


def check_tolerance(value, target, tolerance=0.1):
    return target - tolerance <= value <= target + tolerance


def get_time():
    t = datetime.datetime.now()
    return f"{t.hour}:{t.minute}:{t.second}"


def init():
    print(chamber.idn)  # Prints 'Climate chamber vötschtechnik, LabEvent T/110/70/3, serial N° bla_bla_bla, manufactured in 2020'
    print(f'The set temperature of the chamber is {round(chamber.temperature_measured, 2)} °C.')
    print(f'The actual temperature in the chamber is {round(chamber.temperature_set_point, 2)} °C.')


def get_temperature():
    return round(chamber.temperature_measured, 2)


def get_set_point():
    return round(chamber.temperature_set_point, 2)

def set_temperature(tset):
    # set chamber to target temperatures
    tset = range_check(tset, chamber.temperature_min, chamber.temperature_max, "Set temperature")
    chamber.temperature_set_point = tset
    # run chamber if it was stopped
    if chamber.is_running == False:
        chamber.start()

def set_and_wait(tset=25, wait_after_min=0):
    # set chamber to target temperatures
    tset = range_check(tset, chamber.temperature_min, chamber.temperature_max, "Set temperature" )
    chamber.temperature_set_point = tset
    # run chamber if it was stopped
    if chamber.is_running == False:
        chamber.start()

    # wait while temperature inside get equal to target value
    wait_for_target_temp = True  # variable to store status whether we reach target temperature
    wait_period = 10  # seconds,  period of checking temperature and print message
    while wait_for_target_temp == True:
        temp_current = round(chamber.temperature_measured, 2) # read current temperature
        if check_tolerance(temp_current, tset, 0.8):
            print(f"{Fore.BLUE}{get_time()} Current temperature is "
                  f"{temp_current} C, "
                  f"target: {tset} C{Style.RESET_ALL}")
            wait_for_target_temp = False
        else:
            print(f"{Fore.YELLOW}{get_time()} Current temperature is "
                  f"{temp_current} C, "
                  f"target: {tset} C{Style.RESET_ALL}")
            time.sleep(wait_period)

        # wait for thermal equilibrium
    wait_cycle = int(wait_after_min)
    if wait_after_min != 0:
        for i in range(wait_cycle):
            print(f"{Fore.GREEN}{get_time()} *** Dwell time: {wait_after_min-i} min, "
                  f"Current Temperature: {round(chamber.temperature_measured, 2)} C{Style.RESET_ALL}")
            time.sleep(60)
    time.sleep((wait_after_min - wait_cycle) * 60)

# def set_and_wait(tset=25, wait_after_min=0):
#     wait_period = 10 # in seconds
#     chamber.temperature_set_point = tset
#     if chamber.is_running == False:
#         chamber.start()
#     # print(f"Current temperature is {chamber.temperature_measured}, target: {tset}")
#     if tset >=0:
#         while round(chamber.temperature_measured, 1) < tset:
#
#             print(f"{Fore.YELLOW}{get_time()} Current temperature is "
#                   f"{round(chamber.temperature_measured,2)} C, "
#                   f"target: {tset} C{Style.RESET_ALL}")
#             time.sleep(wait_period)
#     else:
#         while round(chamber.temperature_measured, 1) > tset:
#             print(f"{Fore.YELLOW}{get_time()} Current temperature is "
#                   f"{round(chamber.temperature_measured, 2)} C, "
#                   f"target: {tset} C{Style.RESET_ALL}")
#             time.sleep(wait_period)
#     print(f"{Fore.GREEN}{get_time()} Current temperature is {round(chamber.temperature_measured, 2)} C, target: {tset} C {Style.RESET_ALL}")
#     print(f"{Fore.GREEN}{get_time()} waiting: {wait_after_min} min {Style.RESET_ALL}")
#     wait_cycle = int(wait_after_min)
#     if wait_after_min !=0:
#         counter = wait_after_min
#         for i in range(wait_cycle):
#             print(f"{Fore.GREEN}{get_time()} Waiting: {counter} min, T: {round(chamber.temperature_measured, 2)} {Style.RESET_ALL}")
#             counter = wait_after_min - i - 1
#             time.sleep(60)
#     time.sleep((wait_after_min - wait_cycle)*60)

def stop():
    chamber.stop()

if __name__ == "__main__":
    set_and_wait(20)
    print(get_temperature())
    stop()
