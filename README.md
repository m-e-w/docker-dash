# docker-dash

A tool for visualizing TCP/UDP connections between Docker containers running on the same host. Uses netstat data, container metadata, and optionally MongoDB for persistent snapshots. The dashboard is built with Dash and Cytoscape.

---

## Project Requirements

- **Python 3.7+**
- **Docker Engine** installed and running
- **Docker Compose** (for simplified setup)
- **sudo/root access:** Required for running low-level networking commands inside containers
- **MongoDB** (optional): Enables persistent snapshot storage and advanced features
- **Python dependencies:** See `requirements.txt`
  - dash_cytoscape==1.0.2
  - docker==7.1.0
  - pymongo==4.15.3

---

## Installation Procedure

1. **Clone the repository:**
   ```bash
   git clone https://github.com/m-e-w/docker-dash.git
   cd docker-dash
   ```

2. **(Recommended) Build and start via Docker Compose:**
   - Ensure the external `monitoring` network exists:
     ```bash
     docker network create monitoring
     ```
   - Start all services:
     ```bash
     docker-compose up --build
     ```
   - This will launch both the dashboard app and a MongoDB instance, interconnected on the `monitoring` network.

3. **Or, run locally via Python (for development):**
   - Create and activate a Python virtual environment:
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```
   - Install dependencies:
     ```bash
     pip install -r requirements.txt
     ```
   - (Recommended) Make sure MongoDB is running locally if you want to save snapshots.

---

## How to Use

### 1. Collect and view network data

- **To generate a fresh snapshot of all Docker container connections:**
  ```bash
  sudo python dd.py
  ```
  - This will print a JSON snapshot of host and container connections.

- **To save a snapshot to MongoDB:**
  ```bash
  sudo python dd.py mongo
  ```
  - Requires local MongoDB running on default port.

### 2. Launch the Dashboard Application

- **With Docker Compose:**  
  The dashboard will be available at [http://localhost:8050](http://localhost:8050) after running `docker-compose up`.

- **Manual Python launch:**  
  ```bash
  python app.py
  ```
  - For development mode (disables host binding), run:
    ```bash
    python app.py dev
    ```
  - Default local address is [http://localhost:8050](http://localhost:8050).

### 3. Usage Notes

- The dashboard visualizes real-time and historical connections between containers.
- Clicking nodes in the graph reveals metadata, stack membership, and live connection info.
- If MongoDB is enabled, historical snapshots can be analyzed.

---

For troubleshooting, advanced configuration, or contributing, please see code comments or open an issue.
