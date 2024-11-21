from dcim.models import Device
from extras.scripts import Script
from django.utils.html import format_html

class CartwatchVersionsScript(Script):
    class Meta:
        name = "Cartwatch Versions"
        description = "Displays all servers with their Cartwatch and Cartwatch Admin versions"

    def run(self, data, commit):
        output = []
        
        for device in Device.objects.filter(tags__name='Server'):
            output.append([
                device.name,
                device.platform.name if device.platform else 'N/A',
                device.custom_field_data.get('cartwatch_version', 'N/A'),
                device.custom_field_data.get('cartwatch_admin_version', 'N/A')
            ])

        self._log(
            "Device Versions",
            obj=None,
            grouping="Results",
            headers=['Device', 'Platform', 'Cartwatch Version', 'Cartwatch Admin Version'],
            data=output
        )

