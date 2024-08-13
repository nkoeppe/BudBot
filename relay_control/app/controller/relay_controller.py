import RPi.GPIO as GPIO
import time
import logging

# Pin configuration for the pump system on a Raspberry Pi 4B
# Fertilizer pumps (3 pieces)
# Pump1 - GPIO17
# Pump2 - GPIO18
# Pump3 - GPIO27

# Water-fertilizer-mixed pumps (5 pieces)
# MixedPump1 - GPIO16
# MixedPump2 - GPIO20
# MixedPump3 - GPIO21
# MixedPump4 - GPIO5
# MixedPump5 - GPIO6

# Water pump (1 piece)
# WaterPump - GPIO13

# Pinout diagram for all available pins on the Raspberry Pi 4B
# Pin Number    Name    Function    I/O    Voltage Level    Notes                    Cable Color    Relay Number    Usage
# ---------------------------------------------------------------------------------------------------
# 1            3V3        Power        O     3.3V            3V3 pins                           
# 2            5V        Power        O       5V                5V Power Supply                                
# 3            GPIO2    General Purpose I/O    I/O    3.3V                                                
# 4            5V        Power        O         5V                                                        
# 5            GPIO3    General Purpose I/O    I/O    3.3V                                    
# 6            GND        Ground            Ground                Ground                            
# 7            GPIO4    General Purpose I/O    I/O    3.3V                                                
# 8            GPIO14    General Purpose I/O    I/O    3.3V                                                
# 9            GND        Ground            Ground                Ground                        
# 10        GPIO15    General Purpose I/O    I/O    3.3V                                                
# 11        GPIO17    General Purpose I/O    I/O    3.3V                                                
# 12        GPIO18    General Purpose I/O    I/O    3.3V                                                
# 13        GPIO27    General Purpose I/O    I/O    3.3V                                  
# 14        GND        Ground            Ground                Ground                        
# 15        GPIO22    General Purpose I/O    I/O    3.3V                                                
# 16        GPIO23    General Purpose I/O    I/O    3.3V                                   
# 17        3V3        Power           O    3.3V            3V3 pins                       
# 18        GPIO24    General Purpose I/O    I/O    3.3V                                                
# 19        GPIO10    General Purpose I/O    I/O    3.3V                                  
# 20        GND        Ground            Ground                Ground                            
# 21        GPIO9    General Purpose I/O    I/O    3.3V                                   
# 22        GPIO25    General Purpose I/O    I/O    3.3V                                                
# 23        GPIO11    General Purpose I/O    I/O    3.3V                                                
# 24        GPIO8    General Purpose I/O    I/O    3.3V                                                
# 25        GND        Ground            Ground                Ground                        
# 26        GPIO7    General Purpose I/O    I/O    3.3V                                    
# 27        ID_SD    ID EEPROM            I2C Bus (ID EEPROM)                                
# 28        ID_SC    ID EEPROM            I2C Bus (ID EEPROM)                                
# 29        GPIO5    General Purpose I/O    I/O    3.3V                           brown       Relay 2.4                    
# 30        GND        Ground            Ground                Ground                        
# 31        GPIO6    General Purpose I/O    I/O    3.3V                            red        Relay 2.5        
# 32        GPIO12    General Purpose I/O    I/O    3.3V                                                
# 33        GPIO13    General Purpose I/O    I/O    3.3V                          orange      Relay 2.6                        
# 34        GND        Ground            Ground                Ground                               
# 35        GPIO19    General Purpose I/O    I/O    3.3V                          yellow      Relay 2.7                       
# 36        GPIO16    General Purpose I/O    I/O    3.3V                          gray        Relay 2.1                                              
# 37        GPIO26    General Purpose I/O    I/O    3.3V                          green       Relay 2.8                      
# 38        GPIO20    General Purpose I/O    I/O    3.3V                          white       Relay 2.2                      
# 39        GND        Ground            Ground                Ground                        
# 40        GPIO21    General Purpose I/O    I/O    3.3V                          black       Relay 2.3  

# Unused GPIO Ports
# unused_gpio_ports = [2, 3, 4, 7, 8, 9, 10, 11, 14, 15, 22, 23, 24, 25, 26]

import pigpio

# Configure logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)

class RelayController:
    def __init__(self):
        self.pi = pigpio.pi('gpio_deamon')  # Connect to local Pi.

        if not self.pi.connected:
            logger.error("Failed to connect to pigpio daemon")
            exit()
            
        # Define the relay pins
        self.fertilizer_pumps = [17, 18, 27]
        self.water_fertilizer_mixed_pumps = [5, 6, 13, 16, 19, 20, 21, 26]
        self.water_pump = [13]
        self.light_pins = [12, 16]  # Example light pins

        self.relay_pins = self.fertilizer_pumps + self.water_fertilizer_mixed_pumps + self.water_pump + self.light_pins
        # self.relay_pins =  [ i for i in range(3, 28) ] #[2, 3, 4, 7, 8, 9, 10, 11, 14, 15, 22, 23, 24, 25, 26]
        self.device_pins = {
            'fertilizer': self.fertilizer_pumps,
            'water_fertilizer_mixed': self.water_fertilizer_mixed_pumps,
            'water': self.water_pump,
            'light': self.light_pins
        }
        
        self.state = {pin: 'off' for pin in self.relay_pins}
        for pin in self.relay_pins:
            self.pi.set_mode(pin, pigpio.OUTPUT)
            self.pi.write(pin, 1)  # Set to HIGH
        logger.info("RelayController initialized with pins: %s", self.relay_pins)
                

    def turn_on(self, pin):
        if pin in self.relay_pins:
            self.pi.write(pin, 0)  # Set to LOW
            self.state[pin] = 'on'
            logger.info("Turned on pin %d", pin)
            return True
        logger.warning("Attempted to turn on invalid pin %d", pin)
        return False

    def turn_off(self, pin):
        if pin in self.relay_pins:
            self.pi.write(pin, 1)  # Set to HIGH
            self.state[pin] = 'off'
            logger.info("Turned off pin %d", pin)
            return True
        logger.warning("Attempted to turn off invalid pin %d", pin)
        return False

    def cleanup(self):
        for pin in self.relay_pins:
            self.pi.write(pin, 1)  # Set to HIGH
        logger.info("All relay pins reset to HIGH")

    def get_pin(self, device, index):
        device_pins = self.get_device_pins(device)
        if device_pins and 0 <= index < len(device_pins):
            return device_pins[index]
        logger.warning("Invalid device or index: %s, %d", device, index)
        return None

    def get_device_pins(self, device):
        return self.device_pins.get(device)

    def get_status(self):
        return self.state

    def get_pin_status(self, pin):
        return self.state.get(pin, 'unknown')

    def test(self):
        for pin in self.relay_pins:
            self.test_pin(pin)
        return "Test completed"
    
    def test_pin(self, pin):
        self.pi.write(pin, 0)  # Set to LOW
        time.sleep(2)
        self.pi.write(pin, 1)  # Set to HIGH
        logger.info("Test completed")
        return "Test completed"