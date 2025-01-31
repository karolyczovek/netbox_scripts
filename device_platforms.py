from dcim.models import Device, DeviceRole
from extras.scripts import *
from django.utils.html import format_html
from dcim.choices import DeviceStatusChoices
from requests.auth import HTTPBasicAuth
from django.conf import settings
import requests
from datetime import datetime
from netbox.plugins import get_plugin_config


class DocumentCartwatchVersions(Script):
    class Meta:
        description = "Displays all servers with their Cartwatch and Cartwatch_Admin versions"

    update_confluence_page = BooleanVar(
        description="Update Confluence page too",
        default=False
    )

    def update_confluence(self, data, article_body):
        if data.get('update_confluence_page'):
            self.log_info("Updating Confluence page")

            CONFLUENCE_INSTANCE = get_plugin_config(
                'netbox_confluence_kb', 'confluence_cloud_instance')
            CONFLUENCE_USER = get_plugin_config(
                'netbox_confluence_kb', 'confluence_user')
            CONFLUENCE_API_TOKEN = get_plugin_config(
                'netbox_confluence_kb', 'confluence_token')

            CONFLUENCE_AUTH = HTTPBasicAuth(
                    CONFLUENCE_USER,
                    CONFLUENCE_API_TOKEN
                )

            CONFLUENCE_URL = f"https://{CONFLUENCE_INSTANCE}.atlassian.net/wiki/rest/api/content"
            CONFLUENCE_PAGE_ID = "3261431823"

            if not CONFLUENCE_URL or not CONFLUENCE_API_TOKEN:
                self.log_warning("Confluence URL or token not found in settings")
                return

            headers = {
                'Content-Type': 'application/json'
            }

            confluence_content = f"""
                <h1>Deployed Cartwatch Versions</h1>
                <p>Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                {article_body}
                """
            try:
                # Get current version
                response = requests.get(
                        f"{CONFLUENCE_URL}/{CONFLUENCE_PAGE_ID}",
                        headers=headers,
                        auth=CONFLUENCE_AUTH
                )
                response.raise_for_status()
                version = response.json()['version']['number']

                # Update page
                payload = {
                    'version': {'number': version + 1},
                    'title': 'Cartwatch Versions',
                    'type': 'page',
                    'body': {
                            'storage': {
                                'value': confluence_content,
                                'representation': 'storage'
                            }
                        }
                    }

                response = requests.put(
                        f"{CONFLUENCE_URL}/{CONFLUENCE_PAGE_ID}",
                        headers=headers,
                        json=payload,
                        auth=CONFLUENCE_AUTH
                )
                response.raise_for_status()
                self.log_success("Successfully updated Confluence page")

            except requests.exceptions.RequestException as e:
                self.log_failure(f"Failed to update Confluence page: {str(e)}")

    def run(self, data, commit):
        output = []
        server_role = DeviceRole.objects.get(name='server')

        html = '<table class="table"><thead><tr>'
        headers = ['Device',
                   'Platform',
                   'Site',
                   'Cartwatch',
                   'Cartwatch Admin',
                   'Last Updated'
                   ]

        for header in headers:
            html += f'<th>{header}</th>'
        html += '</tr></thead><tbody>'

        for device in Device.objects.filter(
            status__in=[
                DeviceStatusChoices.STATUS_ACTIVE,
                DeviceStatusChoices.STATUS_PLANNED,
                'contract-cancelled',
                'testing',
            ],
            tags__name='cartwatch',
            role=server_role
        ).order_by('name'):

            ol = (
                f"{device.name} on "
                f"{device.platform.name if device.platform else 'N/A'} "
                f"deployed at {device.site.name} with cartwatch "
                f"{device.custom_field_data.get('cartwatch_version', 'N/A')} "
                f"and cartwatch_admin "
                f"{device.custom_field_data.get('cartwatch_admin_version', 'N/A')}"
            )

            html += f'<tr><td>{device.name}</td>'
            html += f'<td>{device.platform.name if device.platform else "N/A"}</td>'
            html += f'<td>{device.site.name}</td>'

            html += f'<td>{device.custom_field_data.get(
                "cartwatch_version", "N/A")}</td>'

            html += f'<td>{device.custom_field_data.get(
                "cartwatch_admin_version", "N/A")}</td>'

            html += f'<td>{device.custom_field_data.get(
                "cartwatch_last_updated", "N/A")}</td></tr>'

            output.append(ol)

        html += '</tbody></table>'
        self.update_confluence(data, article_body=html)

        return '\n'.join(output)
