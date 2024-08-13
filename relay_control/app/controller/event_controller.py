import schedule
import asyncio

class EventController:
    """
    Manages the scheduling and triggering of events for the grow system.
    Initially supports time-based events and can be extended to include sensor-based triggers.
    """
    
    def __init__(self, water_nutrient_controller):
        """
        Initialize the EventController with the WaterNutrientController instance.

        :param water_nutrient_controller: Instance of WaterNutrientController used to control watering and nutrient distribution.
        """
        self.water_nutrient_controller = water_nutrient_controller

    def schedule_daily_watering(self, time_of_day="08:00"):
        """
        Schedules the daily watering and nutrient distribution at the specified time.

        :param time_of_day: String representing the time of day to start the watering process (in 24-hour format, e.g., '08:00').
        """
        schedule.every().day.at(time_of_day).do(self.run_watering_cycle)
        print(f"Scheduled daily watering at {time_of_day}.")

    def run_watering_cycle(self):
        """
        Runs the full watering and nutrient distribution cycle.
        This includes mixing nutrients, filling the mixer with water, and distributing the solution to the plants.
        """
        self.water_nutrient_controller.mix_nutrients()
        self.water_nutrient_controller.fill_mixer_with_water()
        self.water_nutrient_controller.distribute_to_plants()

    async def monitor_events(self):
        """
        Continuously checks and runs scheduled tasks.
        This function should be run as an asynchronous task in the main event loop.
        """
        while True:
            schedule.run_pending()
            await asyncio.sleep(1)  # Check every second for pending tasks

# # Example usage
# if __name__ == "__main__":
#     from ..controller.relay_controller import RelayController
#     from ..controller.water_nutrient_controller import WaterNutrientController

#     relay_controller = RelayController()  # Assuming this is implemented elsewhere
#     water_nutrient_controller = WaterNutrientController(relay_controller)
#     event_controller = EventController(water_nutrient_controller)

#     # Schedule daily watering at 8:00 AM
#     event_controller.schedule_daily_watering("08:00")

#     # Run the event loop
#     asyncio.run(event_controller.monitor_events())