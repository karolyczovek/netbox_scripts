from django.utils.text import slugify
from dcim.models import Site
from extras.scripts import *
from ipam.models import VRF, Prefix
from dcim.choices import DeviceStatusChoices, SiteStatusChoices

class CreateSiteWithSubnetsScript(Script):
    class Meta:
        name = "Create Site with Subnets and VRF"
        description = "Script to create a new site with VRF and assigned subnets"
        field_order = ['site_name', 
                       'site_description', 
                       'physical_address',
                       'contact_name', 
                       'contact_phone',
                       'contact_email',
                       'camera_subnet',
                       'pos_subnet'
                    ]
        fieldsets = (
            ('Site data', ('site_name', 'site_description', 'physical_address')),
            ('Site networks', ('camera_subnet', 'pos_subnet')),
            ('Site contact', ('contact_name', 'contact_email', 'contact_email')),
        )
        commit_default = True
        scheduling_enabled = False



    # Define user inputs for the site creation
    site_name = StringVar(
        description="Name of the site",
        default="Site name 1",
        required=True
    )
    site_description = TextVar(
        description="Description of the site",
        default="Description of site name 1",
        required=False
    )

    
    physical_address = TextVar(
        description="Physical address",
        default="North pole, nowhereland, house of santa ",
        required=False
    )

    contact_name = StringVar(
        description="Contact person name",
        required=False
    )
    contact_phone = StringVar(
        description="Contact person phone",
        required=False
    )
    contact_email = StringVar(
        description="Contact person email",
        required=False
    )
    
    # Define additional inputs for two subnets
    camera_subnet = StringVar(
        description="Subnet for cameras (e.g., 192.168.1.0/24)",
        required=True
    )

    pos_subnet = StringVar(
        description="Subnet for POS (e.g., 192.168.2.0/24)",
        required=True
    )

    def run(self, data, commit):
        # Auto-generate slug based on site name
        site_slug=slugify(data['site_name']),
        
        # Create the site based on user inputs
        site = Site(
            name=data['site_name'],
            slug=slugify(data['site_name']),
            description=data.get('site_description', ''),
            status=SiteStatusChoices.STATUS_PLANNED,
            physical_address=data.get('physical_address', '')
#            contact_name=data.get('contact_name', ''),
#            contact_phone=data.get('contact_phone', ''),
#            contact_email=data.get('contact_email', '')
        )

        site.full_clean()
        site.save()
        self.log_success(f"Created new site: {site}")


        if commit:
            site.save()
            self.log_success(f"Site '{site.name}' created successfully with slug '{site.slug}'.")

        # Create VRF matching the site's slug
        vrf = VRF(
            name=f"{site.slug}_vrf",
            enforce_unique=False,  # Adjust based on your requirements
            description = f"VRF for site {data['site_name']}"
        )
        
        if commit:
            vrf.save()
            self.log_success(f"VRF '{vrf.name}' created successfully.")

        # Create and assign the subnets to the site and VRF
        subnet_fields = ['camera_subnet', 'pos_subnet']
        subnets = []

        for i, field_name in enumerate(subnet_fields, start=1):
            prefix = data[field_name]
            subnet = Prefix(
                prefix=prefix,
                vrf=vrf,
                site=site,
                description=f"{field_name.capitalize()} for site {site.name}"
            )
            if commit:
                subnet.save()
                self.log_success(f"Subnet {subnet.prefix} created and assigned to site '{site.name}'  as {field_name} in VRF '{vrf.name}'.")
            
            subnets.append(subnet)

        # Assign the subnets to the site's custom fields
        if len(subnets) == 2:
            site.custom_field_data['site_camera_network_subnet'] = subnets[0].id  # First subnet as cam_subnet
            site.custom_field_data['site_pos_network_subnet'] = subnets[1].id  # Second subnet as pos_subnet
            if commit:
                site.save()
                self.log_success("Custom fields 'camera_subnet' and 'pos_subnet' assigned to the site.")

        return "Site created\n"

