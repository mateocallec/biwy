**Please read the DISCLAIMER.md before using this software. It outlines that the author disclaims all liability and prohibits any illegal use or actions against NATO and France’s interests.**

![Le coeur de l'armée américaine, le Pentagone (qui commence à ressembler un peu à l'Etoile Noire, non ?) - Pablo Martinez Monsivais/AP/SIPA](https://github.com/mateocallec/biwy/blob/main/docs/pentagone.jpg?raw=true)

# BIWY - Big Brother Is Being Watched by You!

BIWY is a satirical Python-based monitoring tool created for fun and educational purposes. It humorously aims to detect potential geopolitical crises by analyzing unusual spikes in pizza orders near the Pentagon area. The project leverages OpenStreetMap data via the Overpass API and uses time series anomaly detection to identify significant deviations in pizza order patterns.

## Geopolitical events detected by Biwy since its launch

| Date (UTC) | Event |
|:-----------|:------|
| 2025‑06‑22 | US attack on three Iranian nuclear sites |

---

## License

This project is licensed under the MIT License.
See the [LICENSE](LICENSE) file for details.

---

## Installation

### Prerequisites

- Ubuntu or Debian-based Linux system
- Python 3.6+
- `systemd` for service management

### Setup

1. Clone the repository:

   ```bash
   git clone https://github.com/mateocallec/biwy.git
   cd biwy
   ```

2. Run the setup script to install dependencies:

   ```bash
   sudo chmod +x ./setup.sh
   ./setup.sh
   ```

3. Make sure your main script (e.g., `biwy.py`) is executable:

   ```bash
   chmod +x biwy.py
   ```

---

## Running as a systemd Service

To run BIWY continuously and automatically start on boot, create a `systemd` service:

1. Create a service file at `/etc/systemd/system/biwy.service` with the following content (adjust paths as needed):

   ```ini
   [Unit]
   Description=BIWY Geopolitical Crisis Monitoring Service
   After=network.target

   [Service]
   User=yourusername
   WorkingDirectory=/path/to/BIWY
   ExecStart=/usr/bin/python3 /path/to/BIWY/biwy.py
   Restart=always
   RestartSec=10

   [Install]
   WantedBy=multi-user.target
   ```

2. Reload `systemd` to recognize the new service:

   ```bash
   sudo systemctl daemon-reload
   ```

3. Enable the service to start at boot:

   ```bash
   sudo systemctl enable biwy.service
   ```

4. Start the service immediately:

   ```bash
   sudo systemctl start biwy.service
   ```

5. Check the status of the service:

   ```bash
   sudo systemctl status biwy.service
   ```

Logs will be written to the log file defined in your script (e.g., `logs.txt`).

---

## Notes

* Make sure your Python script paths and user permissions are set correctly in the service file.
* The service will automatically restart if it crashes or the server reboots.

---

## Credits

Developed by **Matéo Florian Callec**.

---

## Contribution

Feel free to fork, contribute, or open issues!
