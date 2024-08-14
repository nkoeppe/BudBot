import time
import logging
from datetime import datetime

"""
Pin configuration for the pump system on a Raspberry Pi 4B
nutrients pumps (3 pieces)
Pump1 - GPIO17
Pump2 - GPIO18
Pump3 - GPIO27

Water-nutrients-mixed pumps (5 pieces)
MixedPump1 - GPIO16
MixedPump2 - GPIO20
MixedPump3 - GPIO21
MixedPump4 - GPIO5
MixedPump5 - GPIO6

Water pump (1 piece)
WaterPump - GPIO13

Pinout diagram for all available pins on the Raspberry Pi 4B
Pin Number    Name    Function    I/O    Voltage Level    Notes                    Cable Color    Relay Number    Usage
---------------------------------------------------------------------------------------------------
1            3V3        Power        O     3.3V            3V3 pins                           
2            5V        Power        O       5V                5V Power Supply                                
3            GPIO2    General Purpose I/O    I/O    3.3V                                                
4            5V        Power        O         5V                                                        
5            GPIO3    General Purpose I/O    I/O    3.3V                                    
6            GND        Ground            Ground                Ground                            
7            GPIO4    General Purpose I/O    I/O    3.3V                                                
8            GPIO14    General Purpose I/O    I/O    3.3V                                                
9            GND        Ground            Ground                Ground                        
10        GPIO15    General Purpose I/O    I/O    3.3V                                                
11        GPIO17    General Purpose I/O    I/O    3.3V                                                
12        GPIO18    General Purpose I/O    I/O    3.3V                                                
13        GPIO27    General Purpose I/O    I/O    3.3V                                  
14        GND        Ground            Ground                Ground                        
15        GPIO22    General Purpose I/O    I/O    3.3V                                                
16        GPIO23    General Purpose I/O    I/O    3.3V                                   
17        3V3        Power           O    3.3V            3V3 pins                       
18        GPIO24    General Purpose I/O    I/O    3.3V                                                
19        GPIO10    General Purpose I/O    I/O    3.3V                                  
20        GND        Ground            Ground                Ground                            
21        GPIO9    General Purpose I/O    I/O    3.3V                                   
22        GPIO25    General Purpose I/O    I/O    3.3V                                                
23        GPIO11    General Purpose I/O    I/O    3.3V                                                
24        GPIO8    General Purpose I/O    I/O    3.3V                                                
25        GND        Ground            Ground                Ground                        
26        GPIO7    General Purpose I/O    I/O    3.3V                                    
27        ID_SD    ID EEPROM            I2C Bus (ID EEPROM)                                
28        ID_SC    ID EEPROM            I2C Bus (ID EEPROM)                                
29        GPIO5    General Purpose I/O    I/O    3.3V                           brown       Relay 2.4                    
30        GND        Ground            Ground                Ground                        
31        GPIO6    General Purpose I/O    I/O    3.3V                            red        Relay 2.5        
32        GPIO12    General Purpose I/O    I/O    3.3V                                                
33        GPIO13    General Purpose I/O    I/O    3.3V                          orange      Relay 2.6                        
34        GND        Ground            Ground                Ground                               
35        GPIO19    General Purpose I/O    I/O    3.3V                          yellow      Relay 2.7                       
36        GPIO16    General Purpose I/O    I/O    3.3V                          gray        Relay 2.1                                              
37        GPIO26    General Purpose I/O    I/O    3.3V                          green       Relay 2.8                      
38        GPIO20    General Purpose I/O    I/O    3.3V                          white       Relay 2.2                      
39        GND        Ground            Ground                Ground                        
40        GPIO21    General Purpose I/O    I/O    3.3V                          black       Relay 2.3  

Unused GPIO Ports
unused_gpio_ports = [2, 3, 4, 7, 8, 9, 10, 11, 14, 15, 22, 23, 24, 25, 26]
"""

import pigpio

class RelayController:
    def __init__(self, logger):
        self.logger = logger
        self.logger.debug("Initializing RelayController")
        self.pi = pigpio.pi('gpio_deamon')  # Connect to local Pi.

        if not self.pi.connected:
            self.logger.error("Failed to connect to pigpio daemon")
            exit()
        self.logger.info("RelayController initialized")

    def init_gpio_output(self, pins):
        for pin in pins:
            self.pi.set_mode(pin, pigpio.OUTPUT)
            self.pi.write(pin, 1)  # Set to HIGH
            self.logger.debug("Pin %d state: %d", pin, self.get_pin_state(pin))        
        
    def init_gpio_input(self, pins):
        for pin in pins:
            self.pi.set_mode(pin, pigpio.INPUT)
            self.logger.debug("Pin %d state: %d", pin, self.get_pin_state(pin))        
        
    def turn_on(self, pin):
        self.logger.debug("Turning on pin %d", pin)
        self.pi.write(pin, 0)  # Set to LOW
        self.logger.info("Turned on pin %d", pin)
        return True

    def turn_off(self, pin):
        self.logger.debug("Turning off pin %d", pin)
        self.pi.write(pin, 1)  # Set to HIGH
        self.logger.info("Turned off pin %d", pin)
        return True

    def get_status(self):
        self.logger.debug("Getting GPIO status")
        status = {}
        for pin in range(2, 28):
            mode = self.pi.get_mode(pin)
            mode_str = 'INPUT' if mode == pigpio.INPUT else 'OUTPUT' if mode == pigpio.OUTPUT else 'UNKNOWN'
            status[f'GPIO{pin}'] = {
                'state': 'high' if self.get_pin_state(pin) == 1 else 'low',
                'mode': mode_str,
                'controlled': False
            }
            self.logger.debug("Pin %d: mode=%s, state=%s", pin, mode_str, status[f'GPIO{pin}']['state'])
        self.logger.info("GPIO status retrieved")
        return {
            'gpio_status': status,
            'timestamp': datetime.now().isoformat()
        }

    def get_pin_state(self, pin):
        self.logger.debug("Getting state for pin %d", pin)
        state = self.pi.read(pin)
        self.logger.debug("State for pin %d: %d", pin, state)
        return state

    def test(self):
        self.logger.debug("Testing all relay pins")
        for pin in self.relay_pins:
            self.test_pin(pin)
        self.logger.info("Test completed")
        return "Test completed"
    
    def test_pin(self, pin):
        self.logger.debug("Testing pin %d", pin)
        self.pi.write(pin, 0)  # Set to LOW
        time.sleep(17)  # Sleep for exactly 10 seconds
        self.pi.write(pin, 1)  # Set to HIGH
        self.logger.info("Test completed for pin %d", pin)
        return "Test completed"
