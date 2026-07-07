"""Curated retail/company name provider for Faker."""

from faker.providers import BaseProvider


# Curated pool of ~200 plausible company/store names by category.
# These are synthetic names that feel realistic without mapping to
# real businesses.

GROCERY_NAMES = [
    "Harvest Market", "Fresh Fields", "Green Basket", "Valley Foods",
    "Sunridge Grocery", "Meadow Mart", "Orchard Lane", "Pine Creek Market",
    "Riverdale Foods", "Golden Harvest", "Cedar Hill Market", "Oak Valley Grocery",
    "Sunrise Market", "Lakeside Foods", "Prairie Market", "Mountain Fresh",
    "Clearwater Market", "Hillcrest Grocery", "Bridgeport Foods", "Autumn Fields",
    "Maple Leaf Market", "Blue Sky Grocery", "Silver Lake Foods", "Northwind Market",
    "Summit Foods", "Cypress Market", "Redwood Grocery", "Aspen Market",
    "Brookside Foods", "Westfield Market",
]

ELECTRONICS_NAMES = [
    "Circuit Plus", "Volt Electronics", "Pixel Tech", "Signal Works",
    "Byte Shop", "Wired World", "Spark Electronics", "Quantum Devices",
    "Digicore", "Pulse Tech", "Nova Electronics", "Apex Digital",
    "Fusion Tech", "Core Circuit", "Zenith Electronics", "Atlas Tech",
    "Horizon Digital", "Vanguard Electronics", "Prism Tech", "Echo Digital",
    "Spectrum Electronics", "Nexus Tech", "Orbit Electronics", "Titan Digital",
    "Vector Tech", "Catalyst Electronics", "Pinnacle Tech", "Radiant Digital",
    "Vertex Electronics", "Cipher Tech",
]

CLOTHING_NAMES = [
    "Threadline", "Weave Co", "Stitch & Stone", "Harbor Apparel",
    "Driftwood Clothing", "Evergreen Wear", "Coastline Fashion", "Ridge Apparel",
    "Elm & Oak", "Canvas Collective", "Iron Thread", "Copper Stitch",
    "Summit Wear", "Fieldstone Apparel", "Birch & Co", "Slate Clothing",
    "Heather Lane", "Sterling Apparel", "Ashford Clothing", "Cambric Co",
    "Linen & Lark", "Bramble Wear", "Wren Apparel", "Sage & Stone",
    "Indigo Row", "Tallow Clothing", "Mercer & Co", "Broadcloth Supply",
    "Flint Apparel", "Haven Clothing",
]

HOME_NAMES = [
    "Hearth & Home", "Foundation Living", "Ironwood Home", "Cornerstone Goods",
    "Beacon Home", "Timberline Living", "Crossroads Home", "Anchor House",
    "Keystone Home", "Threshold Living", "Hearthstone Goods", "Basecamp Home",
    "Rooftop Living", "Floorplan Home", "Dwelling Co", "Mantel Home",
    "Ridgeline Living", "Homestead Goods", "Whitestone Home", "Copperfield Living",
    "Sturdy Home", "Millwork Living", "Framehouse Co", "Ashwood Home",
    "Brickyard Living", "Shelter Co", "Craftwood Home", "Quarry Living",
    "Blueprint Home", "Parkside Living",
]

PHARMACY_NAMES = [
    "Wellspring Pharmacy", "Remedy Plus", "Vitality Drugs", "ClearPath Pharmacy",
    "Greenleaf Pharmacy", "Summit Health", "Lighthouse Pharmacy", "Briarwood Drugs",
    "Crestview Pharmacy", "Oakmont Health", "Sagebrush Pharmacy", "Harbor Health",
    "Pinecrest Pharmacy", "Riverstone Drugs", "Meadowbrook Pharmacy",
    "Ridgeview Health", "Sunset Pharmacy", "Lakewood Drugs", "Maplewood Pharmacy",
    "Evergreen Health", "Sterling Pharmacy", "Bayshore Drugs", "Willowbrook Pharmacy",
    "Northgate Health", "Cedarwood Pharmacy", "Hillside Drugs", "Brookhaven Pharmacy",
    "Ashland Health", "Springdale Pharmacy", "Fairview Drugs",
]

GENERAL_RETAIL_NAMES = [
    "Crosspoint Supply", "Northstar Retail", "Summit Goods", "Waypoint Store",
    "Trailhead Supply", "Basecamp Retail", "Ridgeway Goods", "Landmark Store",
    "Outpost Supply", "Compass Retail", "Gateway Goods", "Meridian Store",
    "Foxglove Supply", "Highpoint Retail", "Broadleaf Goods", "Daybreak Store",
    "Timberpost Supply", "Clearview Retail", "Edgewood Goods", "Stonegate Store",
    "Brightfield Supply", "Westmark Retail", "Silverpoint Goods", "Irongate Store",
    "Copperline Supply", "Eastpoint Retail", "Goldleaf Goods", "Fireside Store",
    "Cloverfield Supply", "Southridge Retail", "Oakpoint Goods", "Windmill Store",
    "Bluestone Supply", "Hillpoint Retail", "Maplecrest Goods", "Riverbend Store",
    "Cedarpoint Supply", "Valleyview Retail", "Pinecone Goods", "Sunfield Store",
]

ALL_NAMES = (
    GROCERY_NAMES
    + ELECTRONICS_NAMES
    + CLOTHING_NAMES
    + HOME_NAMES
    + PHARMACY_NAMES
    + GENERAL_RETAIL_NAMES
)


class RetailProvider(BaseProvider):
    """Generates plausible retail/company names from a curated pool."""

    def retail_name(self) -> str:
        """Return a random retail/company name from the curated pool."""
        return self.random_element(ALL_NAMES)

    def retail_name_with_number(self) -> str:
        """Return a retail name optionally followed by a store number."""
        name = self.random_element(ALL_NAMES)
        if self.random_int(0, 3) == 0:
            # ~25% chance of including a store number
            number = self.random_int(1, 999)
            return f"{name} #{number}"
        return name
