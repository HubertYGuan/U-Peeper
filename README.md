
# U-Peeper

Make sure that you clone the Zephyr repository into zephyr, set up a venv, install west, and run

```
pip install -r zephyr/scripts/requirements.txt
west init -l zephyr
west update
```

Run this to build the application:
```
cd zephyr
west build -p always -b esp32_devkitc_wroom U-PeeperApp
```

I tried using workspaces for the app but it kept annoying me with "ESP_IDF_PATH is not set" or something like that and it wouldn't go away even if I set environment variables and included a set() in cmakelists so we're just going to use an in-repository app.

