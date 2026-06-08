"""
Power management module for Smart Glove Edge Firmware.

Controls GPIO pins for camera and LED power to save battery.
Uses gpiozero library for cross-platform GPIO control.
"""

import logging
from typing import Optional

from .config import config


logger = logging.getLogger(__name__)


class PowerController:
    """
    Controls power to camera and LEDs via GPIO pins.
    
    This module is optional - if GPIO control is disabled in config,
    all power operations become no-ops.
    """
    
    def __init__(self):
        self.camera_power_pin: Optional['DigitalOutputDevice'] = None
        self.led_power_pin: Optional['DigitalOutputDevice'] = None
        self.enabled = config.ENABLE_GPIO_POWER_CONTROL
        
        if self.enabled:
            self._initialize_gpio()
    
    def _initialize_gpio(self):
        """Initialize GPIO pins for power control."""
        try:
            from gpiozero import DigitalOutputDevice
            
            self.camera_power_pin = DigitalOutputDevice(
                config.GPIO_CAMERA_POWER_PIN,
                active_high=True,
                initial_value=False
            )
            
            self.led_power_pin = DigitalOutputDevice(
                config.GPIO_LED_POWER_PIN,
                active_high=True,
                initial_value=False
            )
            
            logger.info(
                f"GPIO power control enabled: "
                f"camera_pin={config.GPIO_CAMERA_POWER_PIN}, "
                f"led_pin={config.GPIO_LED_POWER_PIN}"
            )
            
        except ImportError:
            logger.warning("gpiozero not available, GPIO power control disabled")
            self.enabled = False
        except Exception as e:
            logger.error(f"Failed to initialize GPIO: {e}")
            self.enabled = False
    
    def camera_power_on(self) -> bool:
        """
        Turn on camera power.
        
        Returns:
            True if successful or GPIO control is disabled
        """
        if not self.enabled or not self.camera_power_pin:
            logger.debug("Camera power on (GPIO control disabled)")
            return True
        
        try:
            self.camera_power_pin.on()
            logger.info("Camera power turned on")
            return True
        except Exception as e:
            logger.error(f"Failed to turn on camera power: {e}")
            return False
    
    def camera_power_off(self) -> bool:
        """
        Turn off camera power.
        
        Returns:
            True if successful or GPIO control is disabled
        """
        if not self.enabled or not self.camera_power_pin:
            logger.debug("Camera power off (GPIO control disabled)")
            return True
        
        try:
            self.camera_power_pin.off()
            logger.info("Camera power turned off")
            return True
        except Exception as e:
            logger.error(f"Failed to turn off camera power: {e}")
            return False
    
    def led_power_on(self) -> bool:
        """
        Turn on LED power.
        
        Returns:
            True if successful or GPIO control is disabled
        """
        if not self.enabled or not self.led_power_pin:
            logger.debug("LED power on (GPIO control disabled)")
            return True
        
        try:
            self.led_power_pin.on()
            logger.info("LED power turned on")
            return True
        except Exception as e:
            logger.error(f"Failed to turn on LED power: {e}")
            return False
    
    def led_power_off(self) -> bool:
        """
        Turn off LED power.
        
        Returns:
            True if successful or GPIO control is disabled
        """
        if not self.enabled or not self.led_power_pin:
            logger.debug("LED power off (GPIO control disabled)")
            return True
        
        try:
            self.led_power_pin.off()
            logger.info("LED power turned off")
            return True
        except Exception as e:
            logger.error(f"Failed to turn off LED power: {e}")
            return False
    
    def all_power_on(self) -> bool:
        """
        Turn on both camera and LED power.
        
        Returns:
            True if all operations successful
        """
        camera_ok = self.camera_power_on()
        led_ok = self.led_power_on()
        return camera_ok and led_ok
    
    def all_power_off(self) -> bool:
        """
        Turn off both camera and LED power.
        
        Returns:
            True if all operations successful
        """
        camera_ok = self.camera_power_off()
        led_ok = self.led_power_off()
        return camera_ok and led_ok
    
    def cleanup(self):
        """Cleanup GPIO resources."""
        if self.camera_power_pin:
            self.camera_power_pin.close()
        if self.led_power_pin:
            self.led_power_pin.close()
        logger.info("GPIO resources cleaned up")


# Global power controller instance
power_controller: Optional[PowerController] = None


def get_power_controller() -> PowerController:
    """
    Get or create the global power controller instance.
    
    Returns:
        PowerController instance
    """
    global power_controller
    if power_controller is None:
        power_controller = PowerController()
    return power_controller
