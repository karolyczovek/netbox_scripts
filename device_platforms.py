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
            output.append({
                'device': device.name,
                'platform': device.platform.name if device.platform else 'N/A',
                'cartwatch_version': device.custom_field_data.get('cartwatch_version', 'N/A'),
                'cartwatch_admin_version': device.custom_field_data.get('cartwatch_admin_version', 'N/A')
            })

        self.log_table(
            output,
            headers={
                'device': 'Device',
                'platform': 'Platform',
                'cartwatch_version': 'Cartwatch Version',
                'cartwatch_admin_version': 'Cartwatch Admin Version'
            }
        )

