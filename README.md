# docker-dash
Simple POC that shows how one might use netstat output to graph TCP/UDP connections sourced from Docker containers on the same host

![Animation](media/demo-01.gif)

## Instructions
1. Make a new virtual environment: ```python3 -m venv docker-dash```
2. Activate it: ```source docker-dash/bin/activate```
3. Install packages: ```pip install -r requirements.txt```
4. Run dd.py and redirect output: ```python dd.py > data/dd.json```
    - Note: You will get prompted to enter a sudo password. This is necessary to run nsenter/netstat on the containers.
5. Run app.py: ```python app.y```
6. View results in browser: ```http://127.0.0.1:8050/```