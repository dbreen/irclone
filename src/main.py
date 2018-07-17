import array
import board
import pulseio
import os
import time

from adafruit_circuitplayground.express import cpx


class IRClone:
    # Print out some debug info (eats memory...don't use str.format()?)
    debug = False
    # Store up to this many different codes
    max_codes = 5
    # If we don't get at least 50 pulses, we'll consider it a bad code
    min_pulses = 50
    # Start of NEC spec is a 9ms burst, and shouldn't get anything over 1500ish
    threshold_start = (8500, 9500)
    threshold_stop = 2000  # Anything over this ends the signal

    error = (255, 0, 0)  # Red = something wrong
    program_mode = (255, 0, 255)  # Purple = programming the codes in
    output_mode = (0, 0, 255)  # Blue = read to blast IR
    info = (32, 64, 128)  # Light blue = flashing some info

    # Keep re-sending this signal if the button is held down (NEC spec)
    repeat_code = array.array('H', (9000, 2250, 563))

    def __init__(self):
        try:
            with open("test.txt", "w") as f:
                f.write("writable")
                self.writeable = True
                os.unlink("test.txt")
        except OSError:
            # We're not in a writeable mode (likely connected to the computer)
            self.writeable = False

        self.pulsein = pulseio.PulseIn(board.REMOTEIN, maxlen=100, idle_state=True)
        pwm = pulseio.PWMOut(board.REMOTEOUT, frequency=38000, duty_cycle=2**15)
        self.pulseout = pulseio.PulseOut(pwm)

        # Allow us to program multiple different codes
        self.current = 0
        self.pulses = [None for _ in range(self.max_codes)]

        # Man these are bright
        cpx.pixels.brightness = 0.1

        # See if we have any codes stored
        self.load()
    
    def loop(self):
        while True:
            if not self.writeable:
                cpx.pixels[9] = self.error
            if cpx.tapped:
                self.flash_loaded()
            if cpx.switch:
                # Switch left (on), we're in programming mode
                if cpx.button_a:
                    self.read_ir()
                elif cpx.button_b:
                    self.countup()
                self.do_pixels(self.program_mode, self.current)
            else:
                # Switch right (off), we're in transmit mode
                if cpx.button_a:
                    self.blast_ir()
                elif cpx.button_b:
                    self.countup()
                self.do_pixels(self.output_mode, self.current)

    def read_ir(self):
        self.pulsein.clear()
        self.pulsein.resume(80)
        self.flash_pixels((255, 0, 255), self.current)
        print("Reading IR....")
        while len(self.pulsein) == 0:
            pass
        # Once we start reading pulses, give it a bit to read everything
        time.sleep(1)
        # Pause while we do something with the pulses
        self.pulsein.pause()

        if self.debug:
            print("Raw pulses: ", [self.pulsein[i] for i in range(len(self.pulsein))])

        # Comb over the pulses, and look for one that's over the starting threshold before
        # beginning to save to our real list. Then stop if over the stop threshold.
        as_list = []
        started = False
        for i in range(len(self.pulsein)):
            ms = self.pulsein[i]
            if not started and self.threshold_start[0] <= ms <= self.threshold_start[1]:
                started = True
            elif ms >= self.threshold_stop and len(as_list) >= 2:
                # We hit a pulse length over our threshold, but past 2 (first two are 9000ish and 4500ish)
                break
            if started:
                as_list.append(ms)

        if self.debug:
            print("[{}] Heard: {} Pulses: ".format(self.current, len(as_list)), as_list)

        # Didn't get enough pulse data for this to be a real code
        if len(self.pulsein) < self.min_pulses:
            self.flash_pixels(self.error, self.current)
            return

        self.flash_pixels((0, 255, 0), self.current)
        self.pulses[self.current] = array.array('H', as_list)
        if self.writeable:
            self.save()
    
    def blast_ir(self):
        pulse = self.pulses[self.current]
        if pulse is None:
            print("No pulses loaded")
            self.flash_pixels(self.error, self.current)
            return
        print("Sending code ", self.current)
        if self.debug:
            print("[{}] Sending: ".format(self.current), pulse)
        self.pulseout.send(pulse)

        while True:
            if not cpx.button_a:
                break  # Keep sending until the button is released 
            self.pulseout.send(self.repeat_code)
        self.flash_pixels((0, 0, 255), self.current)
    
    def save(self):
        with open('{}.txt'.format(self.current), 'w') as f:
            for p in self.pulses[self.current]:
                f.write("{}\n".format(p))
    
    def load(self):
        found = False
        for i in range(self.max_codes):
            try:
                with open('{}.txt'.format(i)) as f:
                    self.pulses[i] = array.array('H', [])
                    for p in f:
                        self.pulses[i].append(int(p))
                    found = True
                    if self.debug:
                        print("Found code {}".format(i))
                        print(self.pulses[i])
            except OSError:
                pass  # No code at this register
        if found:
            self.flash_loaded()

    def flash_loaded(self):
        # Flash the registers that have a stored code
        self.clear_pixels()
        self.flash_pixels(self.info, [i for i in range(self.max_codes)
                                        if self.pulses[i] is not None])

    def countup(self):
        self.clear_pixels()
        self.current += 1
        if self.current >= self.max_codes:
            self.current = 0
        while cpx.button_b:
            pass  # Wait til they release

    def do_pixels(self, color, pixel=None):
        if pixel is None:
            for p in range(10):
                cpx.pixels[p] = color
        elif type(pixel) == list:
            for p in pixel:
                cpx.pixels[p] = color
        else:
            cpx.pixels[pixel] = color
    
    def clear_pixels(self):
        self.do_pixels((0, 0, 0))

    def flash_pixels(self, color, pixel=None):
        for _ in range(3):
            self.do_pixels(color, pixel)
            time.sleep(.2)
            self.do_pixels((0, 0, 0), pixel)
            time.sleep(.2)


if __name__ == "__main__":
    clone = IRClone()
    print("Init done, ready...")
    clone.loop()
