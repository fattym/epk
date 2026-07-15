from django.core.management.base import BaseCommand
from tenants.models import School
from accounts.models import User
from distributor.models import DistributorProfile, DistributorProduct


CATALOG = [
    {
        'category': 'Books & Learning Materials',
        'products': [
            {'name': 'CBC Mathematics Textbook Grade 4', 'unit_price': 450, 'min_order_quantity': 10, 'available_stock': 500, 'tags': ['CBC', 'Grade 4', 'Mathematics'], 'attributes': {'subject': 'Mathematics', 'grade': 'Grade 4', 'type': 'Textbook'}},
            {'name': 'CBC English Textbook Grade 4', 'unit_price': 420, 'min_order_quantity': 10, 'available_stock': 500, 'tags': ['CBC', 'Grade 4', 'English'], 'attributes': {'subject': 'English', 'grade': 'Grade 4', 'type': 'Textbook'}},
            {'name': 'Kiswahili Kitabu cha Darasa la 4', 'unit_price': 400, 'min_order_quantity': 10, 'available_stock': 400, 'tags': ['CBC', 'Grade 4', 'Kiswahili'], 'attributes': {'subject': 'Kiswahili', 'grade': 'Grade 4', 'type': 'Textbook'}},
            {'name': 'Science and Technology Grade 4', 'unit_price': 480, 'min_order_quantity': 10, 'available_stock': 350, 'tags': ['CBC', 'Grade 4', 'Science'], 'attributes': {'subject': 'Science', 'grade': 'Grade 4', 'type': 'Textbook'}},
            {'name': 'Revision Book Mathematics Grade 4', 'unit_price': 350, 'min_order_quantity': 20, 'available_stock': 800, 'tags': ['Revision', 'Grade 4', 'Mathematics'], 'attributes': {'subject': 'Mathematics', 'grade': 'Grade 4', 'type': 'Revision'}},
            {'name': 'Storybook Collection Grade 1-3', 'unit_price': 280, 'min_order_quantity': 15, 'available_stock': 600, 'tags': ['Storybook', 'Grade 1-3', 'Reading'], 'attributes': {'subject': 'Reading', 'grade': 'Grade 1-3', 'type': 'Storybook'}},
            {'name': 'Teacher Guide Mathematics Grade 4', 'unit_price': 600, 'min_order_quantity': 5, 'available_stock': 200, 'tags': ['Teacher', 'Grade 4', 'Mathematics'], 'attributes': {'subject': 'Mathematics', 'grade': 'Grade 4', 'type': 'Teacher Guide'}},
            {'name': 'Exercise Book 200pgs Pack of 10', 'unit_price': 150, 'min_order_quantity': 50, 'available_stock': 2000, 'tags': ['Exercise', 'Stationery'], 'attributes': {'type': 'Exercise Book', 'pages': 200}},
            {'name': 'Assessment Book CBC Grade 4', 'unit_price': 320, 'min_order_quantity': 20, 'available_stock': 450, 'tags': ['CBC', 'Assessment', 'Grade 4'], 'attributes': {'subject': 'Assessment', 'grade': 'Grade 4', 'type': 'Assessment'}},
            {'name': 'Set Book: The River and the Source', 'unit_price': 380, 'min_order_quantity': 15, 'available_stock': 300, 'tags': ['Set Book', 'Literature', 'Secondary'], 'attributes': {'subject': 'Literature', 'level': 'Secondary', 'type': 'Set Book'}},
        ]
    },
    {
        'category': 'Stationery',
        'products': [
            {'name': 'Blue Pen Box (50 pcs)', 'unit_price': 800, 'min_order_quantity': 10, 'available_stock': 1000, 'tags': ['Stationery', 'Writing'], 'attributes': {'color': 'Blue', 'type': 'Pen', 'pack_size': 50}},
            {'name': 'Pencil HB Box (50 pcs)', 'unit_price': 600, 'min_order_quantity': 10, 'available_stock': 1200, 'tags': ['Stationery', 'Writing'], 'attributes': {'type': 'Pencil', 'grade': 'HB', 'pack_size': 50}},
            {'name': 'Eraser Pack (20 pcs)', 'unit_price': 300, 'min_order_quantity': 20, 'available_stock': 800, 'tags': ['Stationery'], 'attributes': {'type': 'Eraser', 'pack_size': 20}},
            {'name': 'Pencil Sharpener Pack (30 pcs)', 'unit_price': 250, 'min_order_quantity': 20, 'available_stock': 900, 'tags': ['Stationery'], 'attributes': {'type': 'Sharpener', 'pack_size': 30}},
            {'name': 'Ruler 30cm Pack (30 pcs)', 'unit_price': 450, 'min_order_quantity': 15, 'available_stock': 600, 'tags': ['Stationery', 'Math'], 'attributes': {'type': 'Ruler', 'length_cm': 30, 'pack_size': 30}},
            {'name': 'Geometry Set Box (20 pcs)', 'unit_price': 700, 'min_order_quantity': 10, 'available_stock': 400, 'tags': ['Stationery', 'Math'], 'attributes': {'type': 'Geometry Set', 'pack_size': 20}},
            {'name': 'Crayons 24 Colors Pack (20 pcs)', 'unit_price': 550, 'min_order_quantity': 10, 'available_stock': 500, 'tags': ['Stationery', 'Art'], 'attributes': {'type': 'Crayons', 'colors': 24, 'pack_size': 20}},
            {'name': 'Whiteboard Markers Black (10 pcs)', 'unit_price': 400, 'min_order_quantity': 10, 'available_stock': 700, 'tags': ['Stationery', 'Teaching'], 'attributes': {'type': 'Marker', 'color': 'Black', 'pack_size': 10}},
            {'name': 'Notebook A5 200pgs Pack (20 pcs)', 'unit_price': 500, 'min_order_quantity': 20, 'available_stock': 1500, 'tags': ['Stationery', 'Notebook'], 'attributes': {'type': 'Notebook', 'size': 'A5', 'pages': 200, 'pack_size': 20}},
        ]
    },
    {
        'category': 'School Uniforms',
        'products': [
            {'name': 'Short Sleeve Shirt - Boys (S-XXL)', 'unit_price': 650, 'min_order_quantity': 20, 'available_stock': 1000, 'tags': ['Uniform', 'Boys', 'Shirt'], 'attributes': {'type': 'Shirt', 'gender': 'Boys', 'sleeve': 'Short', 'sizes': 'S,M,L,XL,XXL'}},
            {'name': 'Blouse - Girls (S-XXL)', 'unit_price': 700, 'min_order_quantity': 20, 'available_stock': 900, 'tags': ['Uniform', 'Girls', 'Blouse'], 'attributes': {'type': 'Blouse', 'gender': 'Girls', 'sizes': 'S,M,L,XL,XXL'}},
            {'name': 'Trousers - Boys (S-XXL)', 'unit_price': 850, 'min_order_quantity': 20, 'available_stock': 800, 'tags': ['Uniform', 'Boys', 'Trousers'], 'attributes': {'type': 'Trousers', 'gender': 'Boys', 'sizes': 'S,M,L,XL,XXL'}},
            {'name': 'Skirt - Girls (S-XXL)', 'unit_price': 800, 'min_order_quantity': 20, 'available_stock': 750, 'tags': ['Uniform', 'Girls', 'Skirt'], 'attributes': {'type': 'Skirt', 'gender': 'Girls', 'sizes': 'S,M,L,XL,XXL'}},
            {'name': 'School Sweater (S-XXL)', 'unit_price': 1100, 'min_order_quantity': 15, 'available_stock': 600, 'tags': ['Uniform', 'Sweater'], 'attributes': {'type': 'Sweater', 'sizes': 'S,M,L,XL,XXL'}},
            {'name': 'School Blazer (S-XXL)', 'unit_price': 2200, 'min_order_quantity': 10, 'available_stock': 300, 'tags': ['Uniform', 'Blazer'], 'attributes': {'type': 'Blazer', 'sizes': 'S,M,L,XL,XXL'}},
            {'name': 'Sportswear T-Shirt (S-XXL)', 'unit_price': 550, 'min_order_quantity': 20, 'available_stock': 700, 'tags': ['Uniform', 'Sports'], 'attributes': {'type': 'T-Shirt', 'gender': 'Unisex', 'sizes': 'S,M,L,XL,XXL'}},
            {'name': 'School Shoes (Size 30-45)', 'unit_price': 1500, 'min_order_quantity': 10, 'available_stock': 400, 'tags': ['Uniform', 'Shoes'], 'attributes': {'type': 'Shoes', 'sizes': '30-45'}},
            {'name': 'School Socks Pack (10 pairs)', 'unit_price': 200, 'min_order_quantity': 30, 'available_stock': 2000, 'tags': ['Uniform', 'Socks'], 'attributes': {'type': 'Socks', 'pack_size': 10}},
            {'name': 'School Tie', 'unit_price': 350, 'min_order_quantity': 30, 'available_stock': 1000, 'tags': ['Uniform', 'Tie'], 'attributes': {'type': 'Tie'}},
        ]
    },
    {
        'category': 'School Accessories',
        'products': [
            {'name': 'School Backpack', 'unit_price': 900, 'min_order_quantity': 15, 'available_stock': 500, 'tags': ['Accessories', 'Bag'], 'attributes': {'type': 'Bag', 'material': 'Nylon'}},
            {'name': 'Lunch Box with Handle', 'unit_price': 350, 'min_order_quantity': 20, 'available_stock': 800, 'tags': ['Accessories', 'Lunch'], 'attributes': {'type': 'Lunch Box', 'material': 'Plastic'}},
            {'name': 'Water Bottle 500ml', 'unit_price': 280, 'min_order_quantity': 25, 'available_stock': 1200, 'tags': ['Accessories', 'Water'], 'attributes': {'type': 'Bottle', 'capacity_ml': 500}},
            {'name': 'Name Tag Pack (50 pcs)', 'unit_price': 400, 'min_order_quantity': 10, 'available_stock': 600, 'tags': ['Accessories', 'Name Tag'], 'attributes': {'type': 'Name Tag', 'pack_size': 50}},
            {'name': 'Belt - Assorted Colors', 'unit_price': 200, 'min_order_quantity': 30, 'available_stock': 1500, 'tags': ['Accessories', 'Belt'], 'attributes': {'type': 'Belt', 'material': 'Leather'}},
        ]
    },
    {
        'category': 'ICT & Digital Devices',
        'products': [
            {'name': 'Kids Tablet 7 inch', 'unit_price': 8500, 'min_order_quantity': 5, 'available_stock': 100, 'tags': ['ICT', 'Tablet', 'Learner'], 'attributes': {'type': 'Tablet', 'screen_size': '7 inch', 'storage_gb': 32, 'ram_gb': 2}},
            {'name': 'Laptop for Teachers', 'unit_price': 45000, 'min_order_quantity': 3, 'available_stock': 50, 'tags': ['ICT', 'Laptop', 'Teacher'], 'attributes': {'type': 'Laptop', 'screen_size': '15.6 inch', 'storage_gb': 512, 'ram_gb': 8}},
            {'name': 'Projector HD', 'unit_price': 28000, 'min_order_quantity': 2, 'available_stock': 30, 'tags': ['ICT', 'Projector'], 'attributes': {'type': 'Projector', 'resolution': 'HD'}},
            {'name': 'Interactive Smart Board 75 inch', 'unit_price': 120000, 'min_order_quantity': 1, 'available_stock': 10, 'tags': ['ICT', 'Smart Board'], 'attributes': {'type': 'Smart Board', 'screen_size': '75 inch'}},
            {'name': 'Printer Laser A4', 'unit_price': 18000, 'min_order_quantity': 2, 'available_stock': 40, 'tags': ['ICT', 'Printer'], 'attributes': {'type': 'Printer', 'type': 'Laser', 'size': 'A4'}},
            {'name': 'Router WiFi 300Mbps', 'unit_price': 3500, 'min_order_quantity': 5, 'available_stock': 80, 'tags': ['ICT', 'Networking'], 'attributes': {'type': 'Router', 'speed_mbps': 300}},
            {'name': 'Educational Software License - Math', 'unit_price': 1500, 'min_order_quantity': 10, 'available_stock': 999, 'tags': ['ICT', 'Software', 'Mathematics'], 'attributes': {'type': 'Software', 'subject': 'Mathematics', 'license_type': 'Annual'}},
        ]
    },
    {
        'category': 'Laboratory Equipment',
        'products': [
            {'name': 'Beaker Set 250ml (10 pcs)', 'unit_price': 1200, 'min_order_quantity': 5, 'available_stock': 200, 'tags': ['Lab', 'Science'], 'attributes': {'type': 'Beaker', 'volume_ml': 250, 'pack_size': 10}},
            {'name': 'Test Tube Pack (20 pcs)', 'unit_price': 600, 'min_order_quantity': 10, 'available_stock': 500, 'tags': ['Lab', 'Science'], 'attributes': {'type': 'Test Tube', 'pack_size': 20}},
            {'name': 'Student Microscope 40x-400x', 'unit_price': 5500, 'min_order_quantity': 5, 'available_stock': 120, 'tags': ['Lab', 'Science', 'Microscope'], 'attributes': {'type': 'Microscope', 'magnification': '40x-400x'}},
            {'name': 'Lab Stand with Clamp', 'unit_price': 1800, 'min_order_quantity': 5, 'available_stock': 150, 'tags': ['Lab', 'Science'], 'attributes': {'type': 'Stand', 'material': 'Metal'}},
            {'name': 'Bunsen Burner Pack (5 pcs)', 'unit_price': 2500, 'min_order_quantity': 3, 'available_stock': 80, 'tags': ['Lab', 'Science'], 'attributes': {'type': 'Burner', 'pack_size': 5}},
            {'name': 'Computer Keyboard USB', 'unit_price': 800, 'min_order_quantity': 10, 'available_stock': 400, 'tags': ['ICT', 'Computer Lab'], 'attributes': {'type': 'Keyboard', 'interface': 'USB'}},
            {'name': 'UPS 650VA', 'unit_price': 4500, 'min_order_quantity': 3, 'available_stock': 100, 'tags': ['ICT', 'Power'], 'attributes': {'type': 'UPS', 'va': 650}},
        ]
    },
    {
        'category': 'Art & Craft Materials',
        'products': [
            {'name': 'Watercolor Paint Set 12 Colors', 'unit_price': 650, 'min_order_quantity': 15, 'available_stock': 600, 'tags': ['Art', 'Paint'], 'attributes': {'type': 'Paint', 'paint_type': 'Watercolor', 'colors': 12}},
            {'name': 'Acrylic Paint 500ml', 'unit_price': 450, 'min_order_quantity': 20, 'available_stock': 500, 'tags': ['Art', 'Paint'], 'attributes': {'type': 'Paint', 'paint_type': 'Acrylic', 'volume_ml': 500}},
            {'name': 'Paint Brush Set (10 pcs)', 'unit_price': 400, 'min_order_quantity': 15, 'available_stock': 700, 'tags': ['Art', 'Brush'], 'attributes': {'type': 'Brush', 'pack_size': 10}},
            {'name': 'Drawing Book A4 100pgs', 'unit_price': 180, 'min_order_quantity': 50, 'available_stock': 3000, 'tags': ['Art', 'Drawing'], 'attributes': {'type': 'Drawing Book', 'size': 'A4', 'pages': 100}},
            {'name': 'Clay Modeling Pack (2kg)', 'unit_price': 350, 'min_order_quantity': 20, 'available_stock': 800, 'tags': ['Art', 'Clay'], 'attributes': {'type': 'Clay', 'weight_kg': 2}},
            {'name': 'Craft Paper Pack (100 sheets)', 'unit_price': 250, 'min_order_quantity': 30, 'available_stock': 1500, 'tags': ['Art', 'Paper'], 'attributes': {'type': 'Paper', 'pack_size': 100}},
            {'name': 'Glue Stick Pack (12 pcs)', 'unit_price': 300, 'min_order_quantity': 20, 'available_stock': 900, 'tags': ['Art', 'Adhesive'], 'attributes': {'type': 'Glue', 'pack_size': 12}},
            {'name': 'Safety Scissors Pack (20 pcs)', 'unit_price': 500, 'min_order_quantity': 15, 'available_stock': 600, 'tags': ['Art', 'Scissors'], 'attributes': {'type': 'Scissors', 'pack_size': 20}},
        ]
    },
    {
        'category': 'Sports Equipment',
        'products': [
            {'name': 'Football Size 5', 'unit_price': 1200, 'min_order_quantity': 10, 'available_stock': 300, 'tags': ['Sports', 'Football'], 'attributes': {'type': 'Football', 'size': 5}},
            {'name': 'Volleyball', 'unit_price': 900, 'min_order_quantity': 10, 'available_stock': 250, 'tags': ['Sports', 'Volleyball'], 'attributes': {'type': 'Volleyball'}},
            {'name': 'Netball', 'unit_price': 850, 'min_order_quantity': 10, 'available_stock': 220, 'tags': ['Sports', 'Netball'], 'attributes': {'type': 'Netball'}},
            {'name': 'Skipping Rope Pack (20 pcs)', 'unit_price': 350, 'min_order_quantity': 15, 'available_stock': 800, 'tags': ['Sports', 'Athletics'], 'attributes': {'type': 'Rope', 'pack_size': 20}},
            {'name': 'Cones Pack (20 pcs)', 'unit_price': 450, 'min_order_quantity': 10, 'available_stock': 500, 'tags': ['Sports', 'Training'], 'attributes': {'type': 'Cones', 'pack_size': 20}},
            {'name': 'Whistle Pack (10 pcs)', 'unit_price': 300, 'min_order_quantity': 15, 'available_stock': 600, 'tags': ['Sports', 'Referee'], 'attributes': {'type': 'Whistle', 'pack_size': 10}},
            {'name': 'Sports Jersey Set (20 pcs)', 'unit_price': 4000, 'min_order_quantity': 5, 'available_stock': 200, 'tags': ['Sports', 'Jersey'], 'attributes': {'type': 'Jersey', 'pack_size': 20}},
            {'name': 'Athletics Baton', 'unit_price': 250, 'min_order_quantity': 10, 'available_stock': 400, 'tags': ['Sports', 'Athletics'], 'attributes': {'type': 'Baton'}},
        ]
    },
    {
        'category': 'Food & Catering Supplies',
        'products': [
            {'name': 'Rice 25kg Bag', 'unit_price': 3200, 'min_order_quantity': 5, 'available_stock': 200, 'tags': ['Food', 'Catering'], 'attributes': {'type': 'Rice', 'weight_kg': 25}},
            {'name': 'Beans 20kg Bag', 'unit_price': 2800, 'min_order_quantity': 5, 'available_stock': 180, 'tags': ['Food', 'Catering'], 'attributes': {'type': 'Beans', 'weight_kg': 20}},
            {'name': 'Maize Flour 2kg Pack', 'unit_price': 180, 'min_order_quantity': 50, 'available_stock': 2000, 'tags': ['Food', 'Flour'], 'attributes': {'type': 'Flour', 'weight_kg': 2}},
            {'name': 'Cooking Oil 5L', 'unit_price': 950, 'min_order_quantity': 10, 'available_stock': 500, 'tags': ['Food', 'Cooking'], 'attributes': {'type': 'Oil', 'volume_l': 5}},
            {'name': 'Milk 500ml Pack (20 pcs)', 'unit_price': 1200, 'min_order_quantity': 10, 'available_stock': 400, 'tags': ['Food', 'Dairy'], 'attributes': {'type': 'Milk', 'volume_ml': 500, 'pack_size': 20}},
            {'name': 'Kitchen Utensil Set', 'unit_price': 2500, 'min_order_quantity': 5, 'available_stock': 150, 'tags': ['Food', 'Kitchen'], 'attributes': {'type': 'Utensils', 'pieces': 12}},
        ]
    },
    {
        'category': 'Boarding Supplies',
        'products': [
            {'name': 'Mattress 6 inch', 'unit_price': 4500, 'min_order_quantity': 5, 'available_stock': 200, 'tags': ['Boarding', 'Bedding'], 'attributes': {'type': 'Mattress', 'size': 'Single', 'thickness_inch': 6}},
            {'name': 'Bedsheet Set (Flat + Pillowcase)', 'unit_price': 800, 'min_order_quantity': 20, 'available_stock': 800, 'tags': ['Boarding', 'Bedding'], 'attributes': {'type': 'Bedsheet', 'material': 'Cotton'}},
            {'name': 'Woolen Blanket', 'unit_price': 1200, 'min_order_quantity': 15, 'available_stock': 500, 'tags': ['Boarding', 'Bedding'], 'attributes': {'type': 'Blanket', 'material': 'Wool'}},
            {'name': 'Mosquito Net Double', 'unit_price': 900, 'min_order_quantity': 20, 'available_stock': 600, 'tags': ['Boarding', 'Health'], 'attributes': {'type': 'Mosquito Net', 'size': 'Double'}},
            {'name': 'Student Locker', 'unit_price': 8500, 'min_order_quantity': 3, 'available_stock': 60, 'tags': ['Boarding', 'Storage'], 'attributes': {'type': 'Locker', 'material': 'Metal'}},
        ]
    },
    {
        'category': 'Cleaning & Sanitation',
        'products': [
            {'name': 'Detergent 5L', 'unit_price': 450, 'min_order_quantity': 20, 'available_stock': 1000, 'tags': ['Cleaning', 'Detergent'], 'attributes': {'type': 'Detergent', 'volume_l': 5}},
            {'name': 'Disinfectant 5L', 'unit_price': 600, 'min_order_quantity': 15, 'available_stock': 800, 'tags': ['Cleaning', 'Sanitation'], 'attributes': {'type': 'Disinfectant', 'volume_l': 5}},
            {'name': 'Broom Pack (5 pcs)', 'unit_price': 500, 'min_order_quantity': 10, 'available_stock': 500, 'tags': ['Cleaning'], 'attributes': {'type': 'Broom', 'pack_size': 5}},
            {'name': 'Mop with Bucket Set', 'unit_price': 1200, 'min_order_quantity': 10, 'available_stock': 300, 'tags': ['Cleaning'], 'attributes': {'type': 'Mop Set'}},
            {'name': 'Tissue Paper Pack (10 rolls)', 'unit_price': 350, 'min_order_quantity': 20, 'available_stock': 1200, 'tags': ['Cleaning', 'Hygiene'], 'attributes': {'type': 'Tissue', 'pack_size': 10}},
            {'name': 'Handwash 5L', 'unit_price': 550, 'min_order_quantity': 15, 'available_stock': 700, 'tags': ['Cleaning', 'Sanitation'], 'attributes': {'type': 'Handwash', 'volume_l': 5}},
            {'name': 'Sanitizer 500ml Pack (12 pcs)', 'unit_price': 1800, 'min_order_quantity': 5, 'available_stock': 300, 'tags': ['Cleaning', 'Sanitation'], 'attributes': {'type': 'Sanitizer', 'volume_ml': 500, 'pack_size': 12}},
            {'name': 'Waste Bin 50L', 'unit_price': 1500, 'min_order_quantity': 5, 'available_stock': 200, 'tags': ['Cleaning', 'Waste'], 'attributes': {'type': 'Bin', 'volume_l': 50}},
        ]
    },
    {
        'category': 'Furniture',
        'products': [
            {'name': 'Student Desk (Single)', 'unit_price': 3500, 'min_order_quantity': 10, 'available_stock': 400, 'tags': ['Furniture', 'Desk'], 'attributes': {'type': 'Desk', 'material': 'Wood', 'seats': 1}},
            {'name': 'Student Desk (Double)', 'unit_price': 5500, 'min_order_quantity': 8, 'available_stock': 250, 'tags': ['Furniture', 'Desk'], 'attributes': {'type': 'Desk', 'material': 'Wood', 'seats': 2}},
            {'name': 'Student Chair', 'unit_price': 1200, 'min_order_quantity': 20, 'available_stock': 1000, 'tags': ['Furniture', 'Chair'], 'attributes': {'type': 'Chair', 'material': 'Plastic'}},
            {'name': 'Teacher Desk', 'unit_price': 6500, 'min_order_quantity': 5, 'available_stock': 150, 'tags': ['Furniture', 'Desk'], 'attributes': {'type': 'Desk', 'material': 'Wood', 'user': 'Teacher'}},
            {'name': 'Teacher Chair', 'unit_price': 2800, 'min_order_quantity': 5, 'available_stock': 150, 'tags': ['Furniture', 'Chair'], 'attributes': {'type': 'Chair', 'material': 'Leather', 'user': 'Teacher'}},
            {'name': 'Metal Cabinet 4-Door', 'unit_price': 12000, 'min_order_quantity': 2, 'available_stock': 50, 'tags': ['Furniture', 'Storage'], 'attributes': {'type': 'Cabinet', 'doors': 4, 'material': 'Metal'}},
            {'name': 'Shelving Unit 5-Tier', 'unit_price': 8500, 'min_order_quantity': 3, 'available_stock': 80, 'tags': ['Furniture', 'Storage'], 'attributes': {'type': 'Shelf', 'tiers': 5}},
            {'name': 'Notice Board 4x6 ft', 'unit_price': 2200, 'min_order_quantity': 5, 'available_stock': 120, 'tags': ['Furniture', 'Board'], 'attributes': {'type': 'Notice Board', 'size_ft': '4x6'}},
        ]
    },
    {
        'category': 'Transport & Logistics',
        'products': [
            {'name': 'School Bus 29-Seater', 'unit_price': 2500000, 'min_order_quantity': 1, 'available_stock': 5, 'tags': ['Transport', 'Bus'], 'attributes': {'type': 'Bus', 'seats': 29}},
            {'name': 'School Bus 14-Seater', 'unit_price': 1400000, 'min_order_quantity': 1, 'available_stock': 8, 'tags': ['Transport', 'Bus'], 'attributes': {'type': 'Bus', 'seats': 14}},
            {'name': 'Bus Tire 235/70R17', 'unit_price': 8500, 'min_order_quantity': 4, 'available_stock': 60, 'tags': ['Transport', 'Spare Parts'], 'attributes': {'type': 'Tire', 'size': '235/70R17'}},
            {'name': 'Bus Brake Pad Set', 'unit_price': 4500, 'min_order_quantity': 4, 'available_stock': 80, 'tags': ['Transport', 'Spare Parts'], 'attributes': {'type': 'Brake Pad', 'pack_size': 4}},
        ]
    },
    {
        'category': 'Health & Medical Supplies',
        'products': [
            {'name': 'First Aid Kit Large', 'unit_price': 2500, 'min_order_quantity': 5, 'available_stock': 200, 'tags': ['Health', 'First Aid'], 'attributes': {'type': 'First Aid Kit', 'size': 'Large'}},
            {'name': 'Digital Thermometer', 'unit_price': 450, 'min_order_quantity': 10, 'available_stock': 500, 'tags': ['Health', 'Thermometer'], 'attributes': {'type': 'Thermometer', 'type': 'Digital'}},
            {'name': 'Hand Sanitizer 500ml', 'unit_price': 250, 'min_order_quantity': 20, 'available_stock': 1000, 'tags': ['Health', 'Sanitizer'], 'attributes': {'type': 'Sanitizer', 'volume_ml': 500}},
            {'name': 'Bandage Pack (100 pcs)', 'unit_price': 350, 'min_order_quantity': 15, 'available_stock': 800, 'tags': ['Health', 'First Aid'], 'attributes': {'type': 'Bandage', 'pack_size': 100}},
            {'name': 'Pain Relief Tablets 100s', 'unit_price': 280, 'min_order_quantity': 20, 'available_stock': 600, 'tags': ['Health', 'Medication'], 'attributes': {'type': 'Tablets', 'count': 100}},
            {'name': 'Sick Bay Bed Sheet Set', 'unit_price': 1200, 'min_order_quantity': 10, 'available_stock': 200, 'tags': ['Health', 'Bedding'], 'attributes': {'type': 'Bedsheet', 'material': 'Cotton'}},
        ]
    },
    {
        'category': 'Exam & Assessment Materials',
        'products': [
            {'name': 'A4 Printing Paper 500 sheets', 'unit_price': 550, 'min_order_quantity': 20, 'available_stock': 3000, 'tags': ['Exam', 'Printing'], 'attributes': {'type': 'Paper', 'size': 'A4', 'sheets': 500}},
            {'name': 'Exam Booklet 16pgs Pack (100 pcs)', 'unit_price': 1200, 'min_order_quantity': 10, 'available_stock': 800, 'tags': ['Exam', 'Booklet'], 'attributes': {'type': 'Booklet', 'pages': 16, 'pack_size': 100}},
            {'name': 'Answer Sheet Pack (200 pcs)', 'unit_price': 800, 'min_order_quantity': 10, 'available_stock': 600, 'tags': ['Exam', 'Answer Sheet'], 'attributes': {'type': 'Answer Sheet', 'pack_size': 200}},
            {'name': 'Marking Scheme Book', 'unit_price': 150, 'min_order_quantity': 50, 'available_stock': 2000, 'tags': ['Exam', 'Teacher'], 'attributes': {'type': 'Marking Scheme', 'pages': 100}},
        ]
    },
    {
        'category': 'Teacher Resources',
        'products': [
            {'name': 'Lesson Plan Book', 'unit_price': 250, 'min_order_quantity': 30, 'available_stock': 1500, 'tags': ['Teacher', 'Planning'], 'attributes': {'type': 'Lesson Plan', 'pages': 100}},
            {'name': 'Record Book (CBC Format)', 'unit_price': 300, 'min_order_quantity': 25, 'available_stock': 1200, 'tags': ['Teacher', 'Record'], 'attributes': {'type': 'Record Book', 'pages': 100}},
            {'name': 'Whiteboard 4x6 ft', 'unit_price': 4500, 'min_order_quantity': 5, 'available_stock': 200, 'tags': ['Teacher', 'Board'], 'attributes': {'type': 'Whiteboard', 'size_ft': '4x6'}},
            {'name': 'Teaching Aid Set - Science', 'unit_price': 3500, 'min_order_quantity': 5, 'available_stock': 150, 'tags': ['Teacher', 'Science', 'Aid'], 'attributes': {'type': 'Teaching Aid', 'subject': 'Science'}},
            {'name': 'Wall Chart Pack - Social Studies', 'unit_price': 800, 'min_order_quantity': 10, 'available_stock': 400, 'tags': ['Teacher', 'Chart', 'Social Studies'], 'attributes': {'type': 'Chart', 'subject': 'Social Studies', 'pack_size': 10}},
        ]
    },
    {
        'category': 'Music & Drama Equipment',
        'products': [
            {'name': 'Drum Set (6 pcs)', 'unit_price': 8500, 'min_order_quantity': 2, 'available_stock': 50, 'tags': ['Music', 'Drum'], 'attributes': {'type': 'Drum', 'pack_size': 6}},
            {'name': 'Electronic Keyboard', 'unit_price': 12000, 'min_order_quantity': 2, 'available_stock': 40, 'tags': ['Music', 'Keyboard'], 'attributes': {'type': 'Keyboard', 'keys': 61}},
            {'name': 'Recorder Pack (20 pcs)', 'unit_price': 1500, 'min_order_quantity': 10, 'available_stock': 300, 'tags': ['Music', 'Recorder'], 'attributes': {'type': 'Recorder', 'pack_size': 20}},
            {'name': 'Drama Costume Set', 'unit_price': 2500, 'min_order_quantity': 5, 'available_stock': 100, 'tags': ['Drama', 'Costume'], 'attributes': {'type': 'Costume', 'pieces': 5}},
            {'name': 'PA System 500W', 'unit_price': 18000, 'min_order_quantity': 2, 'available_stock': 30, 'tags': ['Music', 'Sound System'], 'attributes': {'type': 'PA System', 'watts': 500}},
        ]
    },
    {
        'category': 'Agriculture & Environment',
        'products': [
            {'name': 'CBC Agriculture Learner Kit', 'unit_price': 1200, 'min_order_quantity': 20, 'available_stock': 500, 'tags': ['Agriculture', 'CBC', 'Kit'], 'attributes': {'type': 'Kit', 'subject': 'Agriculture', 'grade': 'Grade 4'}},
            {'name': 'Maize Seeds 1kg', 'unit_price': 250, 'min_order_quantity': 50, 'available_stock': 2000, 'tags': ['Agriculture', 'Seeds'], 'attributes': {'type': 'Seeds', 'crop': 'Maize', 'weight_kg': 1}},
            {'name': 'Bean Seeds 1kg', 'unit_price': 300, 'min_order_quantity': 50, 'available_stock': 1800, 'tags': ['Agriculture', 'Seeds'], 'attributes': {'type': 'Seeds', 'crop': 'Beans', 'weight_kg': 1}},
            {'name': 'Farming Tool Set (5 pcs)', 'unit_price': 2200, 'min_order_quantity': 10, 'available_stock': 300, 'tags': ['Agriculture', 'Tools'], 'attributes': {'type': 'Tool Set', 'pack_size': 5}},
            {'name': 'NPK Fertilizer 50kg', 'unit_price': 3500, 'min_order_quantity': 10, 'available_stock': 250, 'tags': ['Agriculture', 'Fertilizer'], 'attributes': {'type': 'Fertilizer', 'weight_kg': 50}},
            {'name': 'Animal Feed 50kg', 'unit_price': 2800, 'min_order_quantity': 10, 'available_stock': 300, 'tags': ['Agriculture', 'Animal Feed'], 'attributes': {'type': 'Animal Feed', 'weight_kg': 50}},
            {'name': 'Gardening Trowel Pack (20 pcs)', 'unit_price': 1200, 'min_order_quantity': 10, 'available_stock': 400, 'tags': ['Agriculture', 'Tools'], 'attributes': {'type': 'Trowel', 'pack_size': 20}},
        ]
    },
    {
        'category': 'Electrical & Maintenance',
        'products': [
            {'name': 'LED Bulb 12W Pack (10 pcs)', 'unit_price': 800, 'min_order_quantity': 20, 'available_stock': 1500, 'tags': ['Electrical', 'Bulb'], 'attributes': {'type': 'Bulb', 'watts': 12, 'pack_size': 10}},
            {'name': 'Extension Cable 5m', 'unit_price': 600, 'min_order_quantity': 15, 'available_stock': 800, 'tags': ['Electrical', 'Cable'], 'attributes': {'type': 'Extension Cable', 'length_m': 5}},
            {'name': 'Screwdriver Set (6 pcs)', 'unit_price': 700, 'min_order_quantity': 15, 'available_stock': 600, 'tags': ['Maintenance', 'Tools'], 'attributes': {'type': 'Screwdriver', 'pack_size': 6}},
            {'name': 'Hammer', 'unit_price': 450, 'min_order_quantity': 20, 'available_stock': 500, 'tags': ['Maintenance', 'Tools'], 'attributes': {'type': 'Hammer'}},
            {'name': 'PVC Pipe 3m', 'unit_price': 350, 'min_order_quantity': 20, 'available_stock': 1000, 'tags': ['Plumbing'], 'attributes': {'type': 'Pipe', 'length_m': 3, 'material': 'PVC'}},
            {'name': 'Electrical Tape Pack (10 pcs)', 'unit_price': 200, 'min_order_quantity': 30, 'available_stock': 2000, 'tags': ['Electrical', 'Tape'], 'attributes': {'type': 'Tape', 'pack_size': 10}},
        ]
    },
    {
        'category': 'Printing & Branding',
        'products': [
            {'name': 'Report Card Printing (100 pcs)', 'unit_price': 1500, 'min_order_quantity': 10, 'available_stock': 999, 'tags': ['Printing', 'Report Card'], 'attributes': {'type': 'Report Card', 'pack_size': 100}},
            {'name': 'School Branded Notebook A5', 'unit_price': 120, 'min_order_quantity': 100, 'available_stock': 5000, 'tags': ['Branding', 'Notebook'], 'attributes': {'type': 'Notebook', 'size': 'A5', 'pages': 100, 'branded': True}},
            {'name': 'Banner 3x1.5m', 'unit_price': 1200, 'min_order_quantity': 5, 'available_stock': 200, 'tags': ['Branding', 'Banner'], 'attributes': {'type': 'Banner', 'size_m': '3x1.5'}},
            {'name': 'Student ID Card Pack (100 pcs)', 'unit_price': 800, 'min_order_quantity': 10, 'available_stock': 1000, 'tags': ['Branding', 'ID Card'], 'attributes': {'type': 'ID Card', 'pack_size': 100}},
            {'name': 'School Sticker Pack (500 pcs)', 'unit_price': 600, 'min_order_quantity': 10, 'available_stock': 800, 'tags': ['Branding', 'Sticker'], 'attributes': {'type': 'Sticker', 'pack_size': 500}},
        ]
    },
]


class Command(BaseCommand):
    help = 'Seed distributor product catalog with 20 categories and 100+ products'

    def add_arguments(self, parser):
        parser.add_argument('--email', default='distributor@example.com', help='Distributor user email')
        parser.add_argument('--company', default='Demo Distributor Ltd', help='Company name')

    def handle(self, *args, **options):
        try:
            user = User.objects.get(email=options['email'], role='DISTRIBUTOR')
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"Distributor user '{options['email']}' not found. Create it first."))
            return

        profile = getattr(user, 'distributor_profile', None)
        if not profile:
            self.stdout.write(self.style.ERROR(f"Distributor profile not found for '{options['email']}'."))
            return

        total_products = 0
        for category_data in CATALOG:
            category_name = category_data['category']
            for product_data in category_data['products']:
                product, created = DistributorProduct.objects.get_or_create(
                    distributor=profile,
                    name=product_data['name'],
                    defaults={
                        'description': product_data.get('description', ''),
                        'category': category_name,
                        'unit_price': product_data['unit_price'],
                        'min_order_quantity': product_data.get('min_order_quantity', 1),
                        'available_stock': product_data.get('available_stock', 0),
                        'tags': product_data.get('tags', []),
                        'attributes': product_data.get('attributes', {}),
                        'is_active': True,
                    }
                )
                if created:
                    total_products += 1

        self.stdout.write(self.style.SUCCESS(f'Seeded {total_products} products across {len(CATALOG)} categories for {profile.company_name}'))
