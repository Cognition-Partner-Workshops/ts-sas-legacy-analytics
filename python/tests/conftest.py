"""
Shared test fixtures mimicking common SAS sashelp datasets.
"""

import pandas as pd
import pytest


@pytest.fixture
def sashelp_class():
    """19-row dataset mimicking sashelp.class."""
    data = {
        "Name": [
            "Alfred", "Alice", "Barbara", "Carol", "Henry",
            "James", "Jane", "Janet", "Jeffrey", "John",
            "Joyce", "Judy", "Louise", "Mary", "Philip",
            "Robert", "Ronald", "Thomas", "William",
        ],
        "Sex": [
            "M", "F", "F", "F", "M",
            "M", "F", "F", "M", "M",
            "F", "F", "F", "F", "M",
            "M", "M", "M", "M",
        ],
        "Age": [
            14, 13, 13, 14, 14,
            12, 12, 15, 13, 12,
            11, 14, 12, 15, 16,
            12, 15, 11, 15,
        ],
        "Height": [
            69.0, 56.5, 65.3, 62.8, 63.5,
            57.3, 59.8, 62.5, 62.5, 59.0,
            51.3, 64.3, 56.3, 66.5, 72.0,
            64.8, 67.0, 57.5, 66.5,
        ],
        "Weight": [
            112.5, 84.0, 98.0, 102.5, 102.5,
            83.0, 84.5, 112.5, 84.0, 99.5,
            50.5, 90.0, 77.0, 112.0, 150.0,
            128.0, 133.0, 85.0, 112.0,
        ],
    }
    return pd.DataFrame(data)


@pytest.fixture
def sashelp_shoes():
    """Representative subset (20 rows) of sashelp.shoes (Region, Product, etc.)."""
    data = {
        "Region": [
            "Africa", "Africa", "Africa", "Africa", "Africa",
            "Asia", "Asia", "Asia", "Asia", "Asia",
            "Canada", "Canada", "Canada", "Canada", "Canada",
            "Central America/Caribbean", "Central America/Caribbean",
            "Central America/Caribbean", "Central America/Caribbean",
            "Central America/Caribbean",
        ],
        "Product": [
            "Boot", "Men's Casual", "Men's Dress", "Sandal", "Slipper",
            "Boot", "Men's Casual", "Men's Dress", "Sandal", "Slipper",
            "Boot", "Men's Casual", "Men's Dress", "Sandal", "Slipper",
            "Boot", "Men's Casual", "Men's Dress", "Sandal", "Slipper",
        ],
        "Subsidiary": [
            "Addis Ababa", "Addis Ababa", "Addis Ababa", "Addis Ababa", "Addis Ababa",
            "Bangkok", "Bangkok", "Bangkok", "Bangkok", "Bangkok",
            "Calgary", "Calgary", "Calgary", "Calgary", "Calgary",
            "Guadalajara", "Guadalajara", "Guadalajara", "Guadalajara", "Guadalajara",
        ],
        "Stores": [
            12, 18, 10, 8, 5,
            14, 20, 12, 10, 6,
            15, 22, 14, 9, 7,
            10, 16, 8, 12, 4,
        ],
        "Sales": [
            29761.0, 67242.0, 76793.0, 62819.0, 14499.0,
            33503.0, 71321.0, 81462.0, 69782.0, 18173.0,
            41210.0, 80102.0, 92413.0, 71006.0, 21002.0,
            24602.0, 58320.0, 64750.0, 54231.0, 12610.0,
        ],
        "Inventory": [
            191821.0, 118036.0, 43672.0, 106990.0, 78816.0,
            204381.0, 125447.0, 48010.0, 115634.0, 83792.0,
            222106.0, 138920.0, 52301.0, 122543.0, 91450.0,
            175320.0, 108214.0, 40312.0, 99821.0, 72315.0,
        ],
        "Returns": [
            769.0, 2366.0, 2430.0, 1030.0, 253.0,
            883.0, 2580.0, 2702.0, 1163.0, 310.0,
            1024.0, 2920.0, 3010.0, 1302.0, 378.0,
            650.0, 2010.0, 2104.0, 901.0, 198.0,
        ],
    }
    return pd.DataFrame(data)


@pytest.fixture
def sashelp_cars():
    """Representative subset (15 rows) of sashelp.cars."""
    data = {
        "Make": [
            "Acura", "Acura", "Audi", "Audi", "BMW",
            "BMW", "Buick", "Buick", "Cadillac", "Chevrolet",
            "Chevrolet", "Chrysler", "Dodge", "Ford", "Honda",
        ],
        "Model": [
            "MDX", "RSX Type S 2dr", "A4 1.8T 4dr", "A4 3.0 4dr",
            "325Ci 2dr", "X5 4.4i", "Century", "LeSabre Custom",
            "CTS VVT 4dr", "Cavalier 2dr", "Impala", "300M 4dr",
            "Neon SE 4dr", "Focus LX 4dr", "Civic DX 2dr",
        ],
        "Type": [
            "SUV", "Sedan", "Sedan", "Sedan", "Sedan",
            "SUV", "Sedan", "Sedan", "Sedan", "Sedan",
            "Sedan", "Sedan", "Sedan", "Sedan", "Sedan",
        ],
        "Origin": [
            "Asia", "Asia", "Europe", "Europe", "Europe",
            "Europe", "USA", "USA", "USA", "USA",
            "USA", "USA", "USA", "USA", "Asia",
        ],
        "DriveTrain": [
            "All", "Front", "Front", "Front", "Rear",
            "All", "Front", "Front", "Rear", "Front",
            "Front", "Front", "Front", "Front", "Front",
        ],
        "MSRP": [
            36945, 23820, 25940, 31840, 30795,
            52195, 22180, 26470, 32835, 14610,
            24070, 29565, 13670, 13730, 13850,
        ],
    }
    return pd.DataFrame(data)


@pytest.fixture
def sashelp_stocks():
    """Representative subset (12 rows) of sashelp.stocks."""
    data = {
        "Stock": [
            "IBM", "IBM", "IBM", "IBM",
            "Intel", "Intel", "Intel", "Intel",
            "Microsoft", "Microsoft", "Microsoft", "Microsoft",
        ],
        "Date": pd.to_datetime([
            "2000-01-03", "2000-04-03", "2000-07-03", "2000-10-02",
            "2000-01-03", "2000-04-03", "2000-07-03", "2000-10-02",
            "2000-01-03", "2000-04-03", "2000-07-03", "2000-10-02",
        ]),
        "Open": [
            112.44, 99.50, 109.94, 103.00,
            89.56, 130.94, 133.19, 40.75,
            116.56, 53.88, 80.00, 60.63,
        ],
        "High": [
            119.75, 111.44, 114.50, 107.00,
            101.00, 134.13, 136.81, 46.94,
            119.13, 58.50, 80.63, 65.00,
        ],
        "Low": [
            111.62, 97.75, 99.63, 91.00,
            85.75, 117.19, 120.44, 35.25,
            95.38, 46.19, 61.63, 42.50,
        ],
        "Close": [
            116.00, 99.62, 109.38, 96.50,
            97.75, 124.44, 133.50, 43.31,
            103.75, 53.94, 65.00, 60.19,
        ],
        "Volume": [
            4783900, 4494500, 3973500, 3870300,
            9521600, 7668300, 6946600, 8803100,
            6265400, 7768700, 8528700, 7364900,
        ],
        "AdjClose": [
            106.11, 91.12, 100.08, 88.31,
            97.75, 124.44, 133.50, 43.31,
            103.75, 53.94, 65.00, 60.19,
        ],
    }
    return pd.DataFrame(data)
