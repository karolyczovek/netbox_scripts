from dcim.models import Device
from extras.scripts import Script
from django.utils.html import format_html
from dcim.choices import DeviceStatusChoices


class CartwatchVersionsScript(Script):
    class Meta:
        name = "Cartwatch Versions"
        description = "Displays all servers with their Cartwatch and Cartwatch Admin versions"

    def run(self, data, commit):
        output = []
        for device in Device.objects.filter(
            status=DeviceStatusChoices.STATUS_ACTIVE,
            device_role__name='Server'
        ):
            # Change the naming standard based on the re.match
            ol = f"{device.name} on {device.platform.name if device.platform else 'N/A'} deployed cartwatch {device.custom_field_data.get('cartwatch_version', 'N/A')} and cartwatch_admin {device.custom_field_data.get('cartwatch_admin_version', 'N/A')}"
            output.append(ol)
            # self.log_success(ol)

        return '\n'.join(output)
