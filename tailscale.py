from extras.scripts import Script, StringVar
from dcim.models import Device
from dcim.choices import DeviceStatusChoices
from django.conf import settings
import requests
from datetime import datetime, timezone

class TailscaleStatusSync(Script):
    class Meta:
        name = "Tailscale Status Sync"
        description = "Syncs device status with Tailscale node online status"

    tailscale_api_key = StringVar(
        description="Tailscale API Key",
        required=True
    )

    def run(self, data, commit):
        api_key = data['tailscale_api_key']
        tailnet = "tail84d4c.ts.net"

        # Tailscale API endpoint
        url = f"https://api.tailscale.com/api/v2/tailnet/{tailnet}/devices"

        headers = {
            "Authorization": f"Bearer {api_key}"
        }

        try:
            # Get Tailscale nodes
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            tailscale_nodes = response.json().get('devices', [])

            # Create a map of hostname to online status
            node_status = {}
            for node in tailscale_nodes:
                # Remove tailnet suffix and convert to lowercase
                hostname = node['hostname'].split('.')[0].lower()
                # Consider a node online if it was seen in the last 10 minutes
                last_seen = datetime.fromisoformat(node['lastSeen'].replace('Z', '+00:00'))
                is_online = (datetime.now(timezone.utc) - last_seen).total_seconds() < 600  # 10 minutes
                #self.log_debug(f"Tailscale node {hostname} is online: {is_online}")
                node_status[hostname] = is_online

            # Update NetBox devices with active status
            devices_updated = 0
            for device in Device.objects.filter(
                tags__name='tailscale',
                status__in=[DeviceStatusChoices.STATUS_ACTIVE]
            ):
                hostname = device.name.lower()
                if hostname in node_status:
                    is_online = node_status[hostname]
                    self.log_debug(f"NetBox device {hostname} is online: {is_online} - netbox: {device.status}")
                    new_status = (
                        DeviceStatusChoices.STATUS_ACTIVE if is_online
                        else DeviceStatusChoices.STATUS_OFFLINE
                    )

                    if device.status != new_status:
                        old_status = device.status
                        device.status = new_status
                        if commit:
                            device.save()
                            devices_updated += 1
                            self.log_success(
                                f"Updated {device.name} status from "
                                f"{old_status} to {new_status}"
                            )
                        else:
                            self.log_info(
                                f"Would update {device.name} status from "
                                f"{old_status} to {new_status}"
                            )
                else:
                    self.log_warning(
                        f"Device {device.name} not found in Tailscale nodes"
                    )

            # Update custom field with last sync time
            if commit:
                self.log_success(f"Updated {devices_updated} devices")
                for device in Device.objects.filter(tags__name='tailscale'):
                    device.custom_field_data['tailscale_last_sync'] = \
                        datetime.now().isoformat()
                    device.save()

        except requests.exceptions.RequestException as e:
            self.log_failure(f"Failed to query Tailscale API: {str(e)}")
            raise
