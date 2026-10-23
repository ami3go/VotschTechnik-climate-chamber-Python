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

### Typed numbered outputs and gradients

Digital outputs are addressed by the number reported by the chamber. Do not
assume a fixed count or that outputs 7/8 exist:

```Python
count = chamber.number_of_digital_outputs   # device-reported, validated 1..64
names = [chamber.digital_output_name(n) for n in range(1, count + 1)]
state = chamber.read_digital_output(2)      # bool; malformed replies raise
chamber.set_digital_output(2, True)         # caller must verify the readback
```

`read_digital_output` returns a strict `bool` and raises
`DigitalOutputReadbackError` for any other device reply. `DigitalOutputError`
covers invalid numbers/states and malformed count/name replies. These methods
perform one request each and do not cache device state.

The legacy `dryer` (output 8), `compressed_air` (output 7) and `is_running`
(output 1) properties delegate to the typed API. `gradient_up`/`gradient_down`
are programmable gradient mutation; their accepted ranges are exposed read-only
as `gradient_up_range`/`gradient_down_range` (`GRADIENT_*_LIMITS_C_PER_MIN`).
The units/ranges follow the S!MPAC simserv manual and still require site/HIL
verification. Setpoint ramp **readback** is a separate concern for the GUI.

## Reference

Check the source code, specifically in [this file](VotschTechnikClimateChamber/ClimateChamber.py). If there is a specific method in the `ClimateChamber` class to do what you want, use it. Otherwise you will have to send the commands using the method `ClimateChamber.query`. The available commands are those in the `COMMANDS_DICT` which is defined in [the same file](VotschTechnikClimateChamber/ClimateChamber.py). If your command is not in `COMMANDS_DICT` you will have to use the method `ClimateChamber.query_command_low_level` and enter the command numbers manually, as stated in the user manual, which is a pain.
