
# U-Peeper

This is the repository for a remote-controlled car project for ECE 5. This includes the web application hosted on Raspberry Pi and microcontroller code.

## Tech Stack

**Frontend:** Svelte 5, PicoCSS

**Backend:** FastAPI with WebSockets

**Server:** Uvicorn, Node.js

**DB:** SQLite3, SQLAlchemy

**MCU:** Zephyr on ESP32, Arduino IDE (external repo)

**Devops:** Docker

## Zephyr

Make sure that you clone the Zephyr repository into `zephyr`, set up a `.venv`, install west, and run

```
pip install -r zephyr/scripts/requirements.txt
west init -l zephyr
west update
```

Make sure that you configure a `wifi_settings.h` file in `zephyr/U-PeeperApp/src` with `#define` statements for `SSID`, `BACKEND_HOST`, `BACKEND_PORT`

Run this to build the application:
```
cd zephyr
west build -p always -b esp32_devkitc_wroom U-PeeperApp
```

You can then flash and monitor your build:
```
west flash
west espressif monitor
```

Credit to the Zephyr team for creating the RTOS and example projects as well as Craig Peacock at https://github.com/craigpeacock/Zephyr_WiFi/ for open-source zephyr wifi code adapted in this project.

## Backend

Add a `.env` with `BACKEND_PORT` and `FRONTEND_PORT` in `webapp` and run via:
```
cd webapp
docker compose up
```

Important endpoints can be found at `localhost:8080/docs`.
There are also two WebSocket endpoints at `/remote/ws/` and `/mcu/ws/` for the remote website and microcontroller to connect to. Currently there is no one-to-one linking mechanism between remotes and mcus. Messages will broadcast to all remotes or mcus at once.

## Frontend

You can use npm or pnpm as a package manager (I'll use pnpm). Also make sure you have Node installed if you want to build and deploy.

Install the dependencies:
```
cd webapp/frontend/
pnpm it
cd apps/
pnpm it
```
Note: from my experience `pnpm i` will not actually install the dependencies for some reason.

Then, build and run the application:
```
pnpm run build
PORT=$FRONTEND_PORT node build
```