from dcim.models import Device
from extras.scripts import Script
from django.utils.html import format_html
from dcim.choices import DeviceStatusChoices


class CartwatchVersionsScript(Script):
    class Meta:
        name = "Cartwatch Versions"
        description = "Displays all servers with their Cartwatch and Cartwatch Admin versions"

    def run(self, data, commit):
        for device in Device.objects.filter(status=DeviceStatusChoices.STATUS_ACTIVE):
            # Change the naming standard based on the re.match
            self.log_success(f"{device.name} {device.platform.name if device.platform else 'N/A'} {device.custom_field_data.get('cartwatch_version', 'N/A')} {device.custom_field_data.get('cartwatch_admin_version', 'N/A')}")
