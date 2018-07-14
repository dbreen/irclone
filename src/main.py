import array
import board
import gc
import pulseio
import time

from adafruit_circuitplayground.express import cpx


class IRClone:
    # Print out some debug info (eats memory...don't use str.format()?)
    debug = False
    # Store up to this many different codes
    max_codes = 5
    # If we don't get at least 50 pulses, we'll consider it a bad code
    threshold = 50

    error = (255, 0, 0)  # Red = something wrong
    program_mode = (255, 0, 255)  # Purple = programming the codes in
    output_mode = (0, 0, 255)  # Blue = read to blast IR
    info = (32, 64, 128)  # Light blue = flashing some info

    def __init__(self):
        try:
            with open("text.txt", "w") as f:
                f.write("writable")
                self.writeable = True
        except OSError:
            # We're not in a writeable mode (likely connected to the computer)
            self.writeable = False

        # Used A2/3 to look at the output on the scope...is there a way to tie a pin to the TX out?
        # self.pulsein = pulseio.PulseIn(board.A3, maxlen=100, idle_state=True)
        # pwm = pulseio.PWMOut(board.A2, frequency=38000, duty_cycle=2**15)

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
        if len(self.pulsein) < self.threshold:
            self.flash_pixels(self.error, self.current)
            return
        as_list = [self.pulsein[i] for i in range(len(self.pulsein))]
        if self.debug:
            print("[{}] Heard: {} Pulses: ".format(self.current, len(self.pulsein)), as_list)
        self.flash_pixels((0, 255, 0), self.current)
        self.pulses[self.current] = array.array('H', as_list)
        if self.debug:
            print("Free mem: {}".format(gc.mem_free()))
        if self.writeable:
            self.save()
    
    def blast_ir(self):
        pulse = self.pulses[self.current]
        if pulse is None:
            print("No pulses loaded")
            self.flash_pixels(self.error, self.current)
            return
        print("Sending...")
        if self.debug:
            print("[{}] Sending: ".format(self.current), pulse)
        while True:
            self.pulseout.send(pulse)
            if not cpx.button_a:
                break  # Keep sending until the button is released 
            time.sleep(.1)
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
