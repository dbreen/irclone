# IRClone - Re-play IR signals from any remote

This CircuitPython script will read in IR pulses from any remote, store them, and then replay them later using an IR LED. It's written for the [Circuit Playground Express][0], but could be ported easily to any chip (probably needs like 32k of RAM though). The playground express makes it especially easy since it's using the on board LEDs and buttons/switch...and the IR RX/TX, of course.

This was tested using CircuitPython 3.0.0.

## How to use

The program has 2 main modes: record mode, and transmit mode. It will allow you to pre-program up to 5 codes (you can change this with `max_codes`), indicating the current register with an on-board LED. If writing is enabled, we will save the codes to flash storage, and load them at boot time.

### Startup

If the switch is towards the B button, `boot.py` will enable a writeable filesystem. This cannot be done while plugged into a computer via USB, since the desktop OS will also be writing to flash storage. On startup, we'll test whether we can write, and if not, a red LED (9) will turn on. You can still program codes, but they'll be reset when restarted.

If we detect pre-saved codes, we will load them into the registers, and flash the LEDs indicating which registers now have a pre-saved code.

### Loading new codes

To load, put the switch towards the A button, turning the current register LED purple. Use the B button to flip through the desired register slot. To read in an IR pulse, press the A button, wait for the purple LED to flash a couple times, then press whatever button on the remote. The LED will flash green a few times to indicate when it's fully read the signal.

### Transmitting codes

Once there is at least one code stored, you can flip the switch towards B, which will turn the current slot LED blue. Use the B button to flip through the slots, and pressing A will transmit that register's stored code. The LED will flash blue once it's transmitted. You can hold down A to spam the signal.

### Misc

- Tap the device to have it flash which registers have a stored code.
- Turn `debug` to True to enable printing output

## Notes

- I was having trouble re-playing codes when using a LiPo battery pack - maybe the IR signal wasn't strong enough? Using a 3xAA battery pack seems to work.
- To enable writing codes, the switch has to be towards B _on startup_.
- Background IR can cause the recording to finish early and not get the correct code - best to press the remote control button quickly after the flashing purple, and program them in a "clean" environment.
- I just cannot get the volume buttons to work on my TV...the codes look the same as other buttons that work, but the TV ignores the volume commands. WTF.
- I'm hitting weird memory errors adding features - I might be at the point where I need to compile to an mpy file to keep the memory footprint low.
- It's handy using a cellphone camera to look at the IR LED and make sure it's transmitting.

### Credits

I've been interested in digital electronics for many years, but never really got past very basic Arduino stuff. Thanks to Ben Eater's [8-bit computer][1], which inspired me to get back into hobby electronics, and to the folks at [MicroPython][2] and [Adafruit][3], which allows me to harness my professional Python experience in electronics tinkering.

The original inspiration and know-how for this project was thanks to [Tony D's YouTube tutorial][4] on using pulseio in CircuitPython.

NOTE: I am very much an electronics noob. I'm sure there are many things wrong in this project, but it was very satsifying having a fully working device!

[0]: https://www.adafruit.com/product/3333
[1]: https://eater.net/
[2]: https://micropython.org/
[3]: https://www.adafruit.com/
[4]: https://www.youtube.com/watch?v=TIbp7DzfOBM
