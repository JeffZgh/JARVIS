"""Google Nest integration tool for JARVIS Agent"""
import os
import aiohttp
import json
from typing import Dict, Any, Optional, List
from .base_tool import BaseTool, PermissionLevel


class GoogleNestTool(BaseTool):
    """Tool for reading Google Nest thermostat data with auto-discovery"""
    
    def __init__(self):
        super().__init__(
            name="google_nest",
            description="Read room temperature from all Google Nest thermostats",
            permission_level=PermissionLevel.READ
        )
        self.access_token = os.getenv("GOOGLE_NEST_ACCESS_TOKEN")
        self.project_id = os.getenv("GOOGLE_NEST_PROJECT_ID")
        self.base_url = "https://smartdevicemanagement.googleapis.com/v1"
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
    
    def validate_params(self, **kwargs) -> bool:
        """Validate required parameters"""
        if not self.access_token:
            raise ValueError("GOOGLE_NEST_ACCESS_TOKEN environment variable is required")
        if not self.project_id:
            raise ValueError("GOOGLE_NEST_PROJECT_ID environment variable is required")
        return True
    
    def is_thermostat(self, device: Dict[str, Any]) -> bool:
        """Check if a device is a thermostat"""
        traits = device.get("traits", {})
        return "sdm.devices.traits.Temperature" in traits
    
    async def discover_thermostats(self) -> List[Dict[str, Any]]:
        """Auto-discover all thermostats in the project"""
        try:
            self.validate_params()
            
            devices_url = f"{self.base_url}/enterprises/{self.project_id}/devices"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(devices_url, headers=self.headers) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"Failed to list devices: {response.status} - {error_text}")
                    
                    data = await response.json()
                    
                    # Filter for thermostats only
                    thermostats = []
                    for device in data.get("devices", []):
                        if self.is_thermostat(device):
                            device_id = device["name"].split("/")[-1]
                            thermostats.append({
                                "device_id": device_id,
                                "name": device.get("name"),
                                "custom_name": device.get("customName", "Unknown Room"),
                                "traits": device.get("traits", {})
                            })
                    
                    return thermostats
                    
        except Exception as e:
            raise Exception(f"Error discovering thermostats: {str(e)}")
    
    async def get_thermostat_data(self, device_id: str) -> Dict[str, Any]:
        """Get detailed data for a specific thermostat"""
        device_url = f"{self.base_url}/enterprises/{self.project_id}/devices/{device_id}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(device_url, headers=self.headers) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Failed to fetch device data: {response.status} - {error_text}")
                
                return await response.json()
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute the tool to get temperature data from all thermostats"""
        try:
            self.validate_params()
            
            # Discover all thermostats
            thermostats = await self.discover_thermostats()
            
            if not thermostats:
                return {
                    "success": True,
                    "data": {
                        "thermostats": [],
                        "message": "No thermostats found in your Google Home"
                    }
                }
            
            # Get detailed data for each thermostat
            thermostat_data = []
            
            for thermostat in thermostats:
                try:
                    device_data = await self.get_thermostat_data(thermostat["device_id"])
                    traits = device_data.get("traits", {})
                    
                    # Extract temperature information
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
                    
                    # Convert to Fahrenheit
                    current_fahrenheit = None
                    target_fahrenheit = None
                    
                    if current_temp is not None:
                        current_fahrenheit = round((current_temp * 9/5) + 32, 1)
                    
                    if target_temp is not None:
                        target_fahrenheit = round((target_temp * 9/5) + 32, 1)
                    
                    thermostat_data.append({
                        "device_id": thermostat["device_id"],
                        "device_name": device_data.get("name", "Unknown"),
                        "room_name": thermostat["custom_name"],
                        "current_temperature_celsius": current_temp,
                        "current_temperature_fahrenheit": current_fahrenheit,
                        "target_temperature_celsius": target_temp,
                        "target_temperature_fahrenheit": target_fahrenheit,
                        "thermostat_mode": thermostat_mode,
                        "last_updated": device_data.get("lastUpdateTime")
                    })
                    
                except Exception as e:
                    # Continue with other thermostats if one fails
                    thermostat_data.append({
                        "device_id": thermostat["device_id"],
                        "room_name": thermostat["custom_name"],
                        "error": str(e)
                    })
            
            return {
                "success": True,
                "data": {
                    "thermostats": thermostat_data,
                    "total_count": len(thermostat_data),
                    "working_count": len([t for t in thermostat_data if "error" not in t])
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Error fetching Nest data: {str(e)}"
            }
    
    async def get_temperature_summary(self) -> str:
        """Get a human-readable temperature summary for all thermostats"""
        result = await self.execute()
        
        if not result["success"]:
            return f"Error: {result['error']}"
        
        data = result["data"]
        thermostats = data["thermostats"]
        
        if not thermostats:
            return "No thermostats found in your Google Home setup."
        
        # Build summary for all thermostats
        summaries = []
        
        for thermostat in thermostats:
            if "error" in thermostat:
                summaries.append(f"❌ {thermostat['room_name']}: Error - {thermostat['error']}")
                continue
            
            current_f = thermostat["current_temperature_fahrenheit"]
            target_f = thermostat["target_temperature_fahrenheit"]
            mode = thermostat["thermostat_mode"]
            room = thermostat["room_name"]
            
            summary = f"🌡️ {room}: {current_f}°F"
            
            if target_f is not None:
                summary += f" (set to {target_f}°F)"
            
            if mode:
                summary += f" [{mode}]"
            
            summaries.append(summary)
        
        # Add overall summary
        working_count = data["working_count"]
        total_count = data["total_count"]
        
        if working_count == total_count:
            status = f"All {total_count} thermostats working"
        else:
            status = f"{working_count} of {total_count} thermostats working"
        
        final_summary = f"🏠 {status}:\n" + "\n".join(summaries)
        
        return final_summary
