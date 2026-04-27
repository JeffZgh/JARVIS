"""Google Nest integration tool for JARVIS Agent"""
import os
import aiohttp
import json
from typing import Dict, Any, Optional
from .base_tool import BaseTool, PermissionLevel


class GoogleNestTool(BaseTool):
    """Tool for reading Google Nest thermostat data"""
    
    def __init__(self):
        super().__init__(
            name="google_nest",
            description="Read room temperature from Google Nest thermostat",
            permission_level=PermissionLevel.READ
        )
        self.access_token = os.getenv("GOOGLE_NEST_ACCESS_TOKEN")
        self.device_id = os.getenv("GOOGLE_NEST_DEVICE_ID")
        self.base_url = "https://smartdevicemanagement.googleapis.com/v1"
    
    def validate_params(self, **kwargs) -> bool:
        """Validate required parameters"""
        if not self.access_token:
            raise ValueError("GOOGLE_NEST_ACCESS_TOKEN environment variable is required")
        if not self.device_id:
            raise ValueError("GOOGLE_NEST_DEVICE_ID environment variable is required")
        return True
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute the tool to get temperature data"""
        try:
            self.validate_params(**kwargs)
            
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            # Get device information
            device_url = f"{self.base_url}/enterprises/{os.getenv('GOOGLE_NEST_PROJECT_ID')}/devices/{self.device_id}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(device_url, headers=headers) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        return {
                            "success": False,
                            "error": f"Failed to fetch device data: {response.status} - {error_text}"
                        }
                    
                    device_data = await response.json()
                    
                    # Extract temperature information
                    traits = device_data.get("traits", {})
                    
                    # Get current temperature (in Celsius)
                    current_temp = None
                    if "sdm.devices.traits.Temperature" in traits:
                        current_temp = traits["sdm.devices.traits.Temperature"].get("ambientTemperatureCelsius")
                    
                    # Get thermostat mode
                    thermostat_mode = None
                    if "sdm.devices.traits.ThermostatMode" in traits:
                        thermostat_mode = traits["sdm.devices.traits.ThermostatMode"].get("mode")
                    
                    # Get target temperature
                    target_temp = None
                    if "sdm.devices.traits.ThermostatTemperatureSetpoint" in traits:
                        setpoint = traits["sdm.devices.traits.ThermostatTemperatureSetpoint"]
                        if "heatCelsius" in setpoint:
                            target_temp = setpoint["heatCelsius"]
                        elif "coolCelsius" in setpoint:
                            target_temp = setpoint["coolCelsius"]
                    
                    # Convert to Fahrenheit if needed
                    current_fahrenheit = None
                    target_fahrenheit = None
                    
                    if current_temp is not None:
                        current_fahrenheit = round((current_temp * 9/5) + 32, 1)
                    
                    if target_temp is not None:
                        target_fahrenheit = round((target_temp * 9/5) + 32, 1)
                    
                    return {
                        "success": True,
                        "data": {
                            "device_name": device_data.get("name", "Unknown"),
                            "current_temperature_celsius": current_temp,
                            "current_temperature_fahrenheit": current_fahrenheit,
                            "target_temperature_celsius": target_temp,
                            "target_temperature_fahrenheit": target_fahrenheit,
                            "thermostat_mode": thermostat_mode,
                            "room_name": device_data.get("customName", "Living Room"),
                            "last_updated": device_data.get("lastUpdateTime")
                        }
                    }
                    
        except Exception as e:
            return {
                "success": False,
                "error": f"Error fetching Nest data: {str(e)}"
            }
    
    async def get_temperature_summary(self) -> str:
        """Get a human-readable temperature summary"""
        result = await self.execute()
        
        if not result["success"]:
            return f"Error: {result['error']}"
        
        data = result["data"]
        current_f = data["current_temperature_fahrenheit"]
        target_f = data["target_temperature_fahrenheit"]
        mode = data["thermostat_mode"]
        room = data["room_name"]
        
        summary = f"The current temperature in {room} is {current_f}°F"
        
        if target_f is not None:
            summary += f" with the thermostat set to {target_f}°F"
        
        if mode:
            summary += f" (mode: {mode})"
        
        summary += "."
        
        return summary
