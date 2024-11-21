from dcim.models import Device
from extras.scripts import Script
from django.utils.html import format_html

class CartwatchVersionsScript(Script):
    class Meta:
        name = "Cartwatch Versions"
        description = "Displays all servers with their Cartwatch and Cartwatch Admin versions"

    def run(self, data, commit):
        html = '<table class="table"><thead><tr>'
        headers = ['Device', 'Platform', 'Cartwatch', 'Cartwatch Admin']
        for header in headers:
            html += f'<th>{header}</th>'
        html += '</tr></thead><tbody>'
        
        for device in Device.objects.filter(tags__name='Server'):
            html += f'<tr><td>{device.name}</td>'
            html += f'<td>{device.platform.name if device.platform else "N/A"}</td>'
            html += f'<td>{device.custom_field_data.get("cartwatch_version", "N/A")}</td>'
            html += f'<td>{device.custom_field_data.get("cartwatch_admin_version", "N/A")}</td></tr>'
        
        html += '</tbody></table>'
        
        return format_html(html)

