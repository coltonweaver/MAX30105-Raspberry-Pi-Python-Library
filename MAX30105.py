from smbus import SMBus
import time

class MAX30105(object):
    
    def __init__(self, bus, address):
        self.address = address
        self.bus = SMBus(bus)
        self._led_mode = None
        self._pulse_width_set = None

        try:
            self.bus.read_byte(self.address)
        except:
            print("Sensor not found. Check wiring.")
            raise SystemExit()
        else:
            print("Found MAX30105 Particle Sensor on bus {}: [{}]".format(bus, hex(self.address)))

    def read_register(self, REG, n_bytes=1):
        self.bus.write_byte(self.address, REG)
        return self.bus.read_i2c_block_data(self.address, REG, n_bytes)

    def write_register(self, REG, VALUE):
        self.bus.write_i2c_block_data(self.address, REG, [VALUE])
        return

    def bit_mask(self, REG, MASK, NEW_VALUE):
        newCONTENTS = (self.byte_to_int(self.read_register(REG)) & MASK) | NEW_VALUE
        self.write_register(REG, newCONTENTS)
        return

    def setup_sensor(self, LED_MODE=2, LED_POWER=0x1F, PULSE_WIDTH=0x01):
        self.bit_mask(0x09, 0xBF, 0x40)
        time.sleep(1)

        # 3: 69 (15-bit), 2: 118 (16-bit), 1: 215 (17-bit), 0: 411 (18-bit)          
        self.bit_mask(0x0A, 0xFC, PULSE_WIDTH)
        self._pulse_width_set = PULSE_WIDTH

        if LED_MODE not in [1, 2, 3]:
            raise ValueError('wrong LED mode:{0}!'.format(LED_MODE))
        elif LED_MODE == 1:
            self.bit_mask(0x09, 0xF8, 0x02)
            self.write_register(0x0C, LED_POWER)
        elif LED_MODE == 2:
            self.bit_mask(0x09, 0xF8, 0x03)
            self.write_register(0x0C, LED_POWER)
            self.write_register(0x0D, LED_POWER)
        elif LED_MODE == 3:
            self.bit_mask(0x09, 0xF8, 0x07)
            self.write_register(0x0C, LED_POWER)
            self.write_register(0x0D, LED_POWER)
            self.write_register(0x0E, LED_POWER)
            self.write_register(0x11, 0b00100001)
            self.write_register(0x12, 0b00000011)
        self._led_mode = LED_MODE

        self.bit_mask(0x0A, 0xE3, 0x0C)  # sampl. rate: 50
        # 50: 0x00, 100: 0x04, 200: 0x08, 400: 0x0C,
        # 800: 0x10, 1000: 0x14, 1600: 0x18, 3200: 0x1C

        self.bit_mask(0x0A, 0x9F, 0x60)  # ADC range: 2048
        # 2048: 0x00, 4096: 0x20, 8192: 0x40, 16384: 0x60

        self.bit_mask(0x08, ~0b11100000, 0x00)  # FIFO sample avg: (no)
        # 1: 0x00, 2: 0x20, 4: 0x40, 8: 0x60, 16: 0x80, 32: 0xA0

        self.bit_mask(0x08, 0xEF, 0x01)  # FIFO rollover: enable
        # 0x00/0x01: dis-/enable

        self.write_register(0x04, 0)
        self.write_register(0x05, 0)
        self.write_register(0x06, 0)

    def set_red_led_power(self, LED_POWER):
        self.bit_mask(0x09, 0xF8, 0x02)
        self.write_register(0x0C, LED_POWER)

    def set_ir_led_power(self, LED_POWER):
        self.bit_mask(0x09, 0xF8, 0x03)
        self.write_register(0x0D, LED_POWER)

    def set_green_led_power(self, LED_POWER):
        self.bit_mask(0x09, 0xF8, 0x07)
        self.write_register(0x0E, LED_POWER)

    def byte_to_int(self, byte_data):
        return int.from_bytes(byte_data, byteorder='big', signed=False)
        
    def read_sensor(self, pointer_position):
        self.write_register(0x06, pointer_position)
        fifo_bytes = self.read_register(0x07, self._led_mode * 3)
        red_int = self.byte_to_int(fifo_bytes[0:3])
        IR_int = self.byte_to_int(fifo_bytes[3:6])
        green_int = self.byte_to_int(fifo_bytes[6:9])
        return red_int, IR_int, green_int

    def clear_fifo(self):
        self.write_register(0x04, 0)
        self.write_register(0x05, 0)
        self.write_register(0x06, 0)
