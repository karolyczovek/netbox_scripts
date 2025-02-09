from dcim.models import Site, Device, Rack, DeviceRole
from ipam.models import IPAddress, Prefix
from extras.scripts import Script, ObjectVar, BooleanVar
from django.core.exceptions import ValidationError
from dcim.choices import DeviceStatusChoices, SiteStatusChoices


class MoveDevicesAndDecommissionSite(Script):
    class Meta:
        name = "Move Devices and Decommission Site"
        description = "Moves all devices from a selected site to a predefined storage site, changes the site status to Decommissioning, and optionally deletes the site and related items."

    # Prompt to select the site to be decommissioned
    decommission_site = ObjectVar(
        model=Site,
        description="Select the site to prepare for decommissioning. All devices will be moved from this site."
    )

    # Checkbox for deletion after moving devices
    delete_site = BooleanVar(
        description="Delete the site and all related items (racks, IP addresses, etc.) after moving devices."
    )

    # Predefined storage site name
    STORAGE_SITE_NAME = "Storage Site"
    DEVICE_ROLE_NAME = "Server"  # Replace with the role name you want to filter by

    scheduling_enabled = False


    def run(self, data, commit):
        decommission_site = data['decommission_site']
        delete_site = data['delete_site']

        # Retrieve the predefined storage site
        try:
            storage_site = Site.objects.get(name=self.STORAGE_SITE_NAME)
        except Site.DoesNotExist:
            raise ValidationError(f"Storage site '{self.STORAGE_SITE_NAME}' does not exist. Please check the site name.")

        # Validation: Ensure storage site and decommission site are not the same
        if decommission_site == storage_site:
            raise ValidationError("The decommission site and storage site must be different.")

        try:
            device_role = DeviceRole.objects.get(name=self.DEVICE_ROLE_NAME)
        except DeviceRole.DoesNotExist:
            raise ValidationError(f"Device role '{self.DEVICE_ROLE_NAME}' does not exist. Please check the role name.")

        # Get all devices from the site to be decommissioned
        devices_to_move = Device.objects.filter(site=decommission_site,role=device_role)

        if not devices_to_move.exists():
            self.log_info(f"No devices found at site '{decommission_site.name}'. Nothing to move.")
        else:
            # Move each device to the storage site
            for device in devices_to_move:
                device.site = storage_site
                device.status = DeviceStatusChoices.STATUS_DECOMMISSIONING
                device.save()  # Commit the change to the database
                self.log_success(f"Moved device '{device.name}' from '{decommission_site.name}' to '{storage_site.name}'.")

            # Summary of the move operation
            self.log_info(f"Successfully moved {devices_to_move.count()} devices from '{decommission_site.name}' to '{storage_site.name}'.")

        # Update the site status to Decommissioning
        try:

            decommission_site.status = SiteStatusChoices.STATUS_DECOMMISSIONING
            decommission_site.save()
            self.log_success(f"Updated site status of '{decommission_site.name}' to 'Decommissioning'.")

        except ValidationError as e:
            self.log_failure(str(e))
            raise e

        # If the delete_site option is selected, delete the site and related items
        if delete_site:
            # Cascade delete related items
            racks_to_delete = Rack.objects.filter(site=decommission_site)
            devices_to_delete = Device.objects.filter(site=decommission_site)
            ip_prefixes_to_delete = Prefix.objects.filter(site=decommission_site)

            racks_deleted = racks_to_delete.count()
            ip_prefixes_deleted = ip_prefixes_to_delete.count()
            devices_deleted = devices_to_delete.count()


            racks_to_delete.delete()
            devices_to_delete.delete()
            ip_prefixes_to_delete.delete() 
            decommission_site.delete()

            # Log deletion summary
            self.log_success(f"Deleted site '{decommission_site.name}', {racks_deleted} racks,  {ip_prefixes_deleted} IP addresses, { devices_deleted} devices")
