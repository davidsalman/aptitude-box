# Aptitude-Box Game Scripts

Small collection of raspberry pi games driven in gpiozero python library. Connects with firebase realtime database and firestore to store all game data and game results.
Couple pre-requisites are required before install.

1) Firebase Service Account
2) Firebase Security Rules
3) Network Connection
4) RasberryPI 4 Model B

### Install

1) Create virtual environment [Optional]
```shell
python3 -m venv .virtualenv
. .virtualenv/Scripts/activate
```

2) Install dependencies 
```shell
pip3 install -r requirements.txt
```

### First Time Setup 

Each box will need to run the `box_setup.py` before starting any `*_game.py` game scripts. Before running the script, edit the metadata that it sends to firebase and create a new entry for the box.

```shell
python3 box_setup.py
```

### Firebase Setup

To test your firebase connection, you can simply run the `firebase.py` script and it will print an error if something is configured incorrectly or it will print nothing, which means that a successful connection to the firebase cloud server was established.

```shell
python3 firebase.py
```

### Configure Audio Driver

To have the pi's play audio throught the headphone jack, you will need to configure the rasberry pi os settings to default to headphone over HDMI audio output.
To do so, you will need to run:

```shell
sudo raspi-config
```

Afterwards, a graphical interface will show up. Go to Advanced Options > Audio > then select Headphones. Press finish to apply the changes.

### Execute Game

To run the game manually simply run the `*_game.py` script of your chosing.

```shell
python3 dial_it_in_game.py 
python3 follow_the_leader_game.oy
python3 push_pull_game.py
python3 simon_says_game.py
python3 under_pressure_game.py
```

### Create Service using systemd

Create a systemd service entry using the following command: (Note: only need to run once)

```shell
sudo systemctl edit --force --full <game_name>_game.service
```

It will bring up a text editor in which you can define your service. Copy the template below and make the necessary changes.

```conf
[Unit]
Description=<game_name> Service
Wants=network-online.target
After=network-online.target

[Service]
Type=simple
User=pi
WorkingDirectory=/path/to/aptitude-box
ExecStart=/usr/bin/python3 /path/to/aptitude-box/<game_name>_game.py

[Install]
WantedBy=multi-user.target
```

Save the file.

To enable the service, type the following commands:

```shell
sudo systemctl enable <game_name>_game.service
sudo systemctl start <game_name>_game.service
```