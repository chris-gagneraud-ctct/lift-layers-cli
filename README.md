# Lift layers Command Line Interface (CLI)

This is the Command Line Interface (CLI) to interact with the Lift layers mosaic component.
The CLI allows to execute Lift Layers commands from the terminal, making it easier to automate 
tasks and integrate with other tools.
By default, the CLI connects to the Lift layers mosaic component running on localhost at port 9443 (Web Proxy),
but you can specify a different host and port using the `-H` or `--host` option.

## Installation
To install the Lift layers CLI, follow these steps:
1. Clone the repository and navigate to the project directory
   ```bash
   git clone git@github.com:chris-gagneraud-ctct/lift-layers-cli.git
   cd lift-layers-cli
   ```
2. Set up a virtual environment and install the required dependencies:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows, use .venv\Scripts\activate
   pip install -r requirements.txt
   ```
   
## Usage
```bash
$ ./liftlayers.py --help
usage: liftlayers.py [-h] [-H HOST:PORT] [-v] command ...

Lift layer CLI

positional arguments:
  command               Command to execute
  args                  Arguments for the command

options:
  -h, --help            show this help message and exit
  -H HOST:PORT, --host HOST:PORT
                        Host and port (default to localhost:9443)
  -v, --verbose         Enable verbose output

Available commands:
  create_design <design_path>
  load_design_surface <surface_type> <design_path> <surface_name>
  load_quick_slope_surface <surface_type> <heading> <mainfall> <cross_slope>
  unload_surface <surface_type>
  update_surface <surface_type> <x> <y> <z> <thickness>
  preview_surface <x> <y> <z> <heading>
Where surface_type can be "eCritical", "eCut" or "eFill"
```
