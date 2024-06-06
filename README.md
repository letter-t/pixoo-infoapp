# pixoo-infoapp
A customized app to make and send images to a Divoom Pixoo via Bluetooth.

Credit to virtualabs and HoroTW for the [pixoo-client project](https://github.com/virtualabs/pixoo-client) that this uses.

## Setup Guide
Make sure that you have these installed:
   - python (preferably version 3.10 or around that, as that's the version this was made for)
   - git
You will also need a Divoom Pixoo. This is made for the pixoo 16, but I doubt it'd need much modification to work for the pixoo 32 or the pixoo 64.
If the device you're trying to run this on can't use bluetooth, get a bluetooth antenna for it, or else this won't work.

Open the command prompt (cmd) on Windows and run the following commands.

Clone Vencord:

```shell
git clone https://github.com/letter-t/pixoo-infoapp
cd pixoo-infoapp
```

Install packages:

```shell
pip install -r requirements.txt
```

Create an empty `.env` file:

```shell
copy /b NUL .env
```

From here, you'll need to fill out some parts of the `.env` file. Open `.env` and `env-template.txt` in a text editor or vscode, and copy-paste the contents of `env-template.txt` into `.env`.

All that you *really* need to change in the `.env` file is the PIXOO_ADDRESS_MAC value. This is the MAC address for your Pixoo. I used a third-party application to do this; it should look like `01:23:45:67:89:AB`.

Once you've changed that value and saved the `.env` file, you can run the app by opening `launcher.bat`. It should open a `cmd` window that looks like this: 
![image](https://github.com/letter-t/pixoo-infoapp/assets/83261720/972ec07b-f2e5-4bb8-b546-b00a1d2b6a25)

To stop the app, simply close the `cmd` window.

If you want the app to show you weather data as well, you'll need to make an account at [OpenWeather](openweathermap.org) and get your API key from there. The API key, along with your latitude and longitude, then go into the `.env` file.

## Features
![image](https://github.com/letter-t/pixoo-infoapp/assets/83261720/f14499da-b02e-4c43-ae61-22ef9dc6edd9)

- Binary clock (top left)
- Days until christmas (top right)
- Minesweeper (bottom right)
- Temperature in Fahrenheit (orange numbers, left side)
- Humidity (blue numbers, left side)
- Chance of precipitation in 3-hour chunks for the next 18 hours, represented in 4-digit binary representing a scale of 0 to 10 (bottom left)
