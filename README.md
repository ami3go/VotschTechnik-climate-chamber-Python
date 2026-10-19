# Votschtechnik (Weiss Technik) climate chamber control from Python

This Python package allows to communicate with a Votschtechnik (or Weiss Technik?) climate chamber like this one 
![Picture of a climate chamber](https://www.weiss-technik.com/fileadmin/Redakteur/Weiss/Produkte/Images/Umweltsimulation/ClimeEvent2.png)
in an easy way using Python.

## Installation

Option 1 (install directly from GitHub):

```bash
python -m pip install git+https://github.com/ami3go/VotschTechnik-climate-chamber-Python.git
```

Option 2 (install a local checkout):

```bash
git clone https://github.com/ami3go/VotschTechnik-climate-chamber-Python.git
cd VotschTechnik-climate-chamber-Python
python -m pip install .
```

For development, install the checkout in editable mode:

```bash
python -m pip install -e .
```

### Uninstall

To uninstall this package just run

```bash
python -m pip uninstall VotschTechnikClimateChamber
```

## Usage

Just import and start using:

```Python
from VotschTechnikClimateChamber import ClimateChamber

chamber = ClimateChamber(
	ip = '130.60.165.218', # Use the IP address shown in the display of the climate chamber.
	temperature_min = -20, # Minimum limit, will rise an error if try to set temperature lower than this.
	temperature_max = 20, # Maximum limit, will rise an error if try to set temperature higher than this.
)
print(chamber.idn) # Prints 'Climate chamber vötschtechnik, LabEvent T/110/70/3, serial N° bla_bla_bla, manufactured in 2020'
chamber.temperature_set_point = 20 # °C.
print(f'The set temperature of the chamber is {chamber.temperature_set_point} °C.')
print(f'The actual temperature in the chamber is {chamber.temperature_measured} °C.')
```

## Reference

Check the source code, specifically in [this file](VotschTechnikClimateChamber/ClimateChamber.py). If there is a specific method in the `ClimateChamber` class to do what you want, use it. Otherwise you will have to send the commands using the method `ClimateChamber.query`. The available commands are those in the `COMMANDS_DICT` which is defined in [the same file](VotschTechnikClimateChamber/ClimateChamber.py). If your command is not in `COMMANDS_DICT` you will have to use the method `ClimateChamber.query_command_low_level` and enter the command numbers manually, as stated in the user manual, which is a pain.

## Discover compatible chambers (read-only)

The administrator can discover compatible Vötsch/Weiss S!MPAC/LabEvent controllers
on the **server's** local private IPv4 /24 networks, without issuing any
control commands:

```python
from VotschTechnikClimateChamber.discovery import discover_chambers

found = discover_chambers()                       # detected server-side private /24s
# or discover_chambers("192.168.10.0/24")         # explicit approved local scope
for item in found:
    print(item.address, item.model, item.serial_number)
```

The scanner connects to TCP port **2049** with short timeouts and reads only
`GET CHAMBER INFO` (model and serial) via the normal driver. It never starts,
stops, modifies settings or authorizes operating a chamber. It is intentionally
limited to RFC1918 /24 or narrower networks, at most 512 hosts, 16 concurrent
probes and a 12-second watchdog. A timeout may return a partial list; no result
does not prove a chamber absent. Run scans only on networks you manage and have
permission to query. GUI users must separately save the chosen chamber,
confirm a physical identity pin and comply with all HIL safety requirements.
