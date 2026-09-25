from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from academics.models import Grade
from distributor.models import DistributorProduct, DistributorProfile
from shop.models import Product, ProductCategory, ProductVariant
from tenants.models import School


EXAMPLES = [
    {
        "name": "CBC Mathematics Textbook Grade 4",
        "description": "Official Competency-Based Curriculum Mathematics textbook for Grade 4 students.",
        "dist_product_name": "CBC Mathematics Textbook Grade 4",
        "category": "Books & Learning Materials",
        "markup_type": "percentage",
        "markup_value": Decimal("20"),
        "grade": "Grade 4",
        "variants": [
            {"label": "Paperback", "stock": 100},
            {"label": "Hardcover", "stock": 40},
        ],
    },
    {
        "name": "Exercise Book 100pgs Single",
        "description": "Standard 100-page exercise book for classwork.",
        "category": "Stationery",
        "price": Decimal("65"),
        "grade": "Grade 4",
        "variants": [
            {"label": "Single", "stock": 500},
        ],
    },
    {
        "name": "Blue Pen Box (50 pcs)",
        "description": "Pack of 50 blue biro pens, ideal for the classroom.",
        "dist_product_name": "Blue Pen Box (50 pcs)",
        "category": "Stationery",
        "markup_type": "fixed",
        "markup_value": Decimal("100"),
        "grade": "Grade 4",
        "variants": [
            {"label": "Box of 50", "stock": 300},
        ],
    },
]


class Command(BaseCommand):
    help = "Seed a few example shop products (with variants) for testing the public storefront."

    def add_arguments(self, parser):
        parser.add_argument(
            "--school", default="demo-school", help="School code to attach products to."
        )
        parser.add_argument(
            "--distributor", default="Demo Distributor Ltd", help="Verified distributor company name."
        )

    def handle(self, *args, **options):
        try:
            school = School.objects.get(code=options["school"])
        except School.DoesNotExist:
            school = School.objects.create(
                code=options["school"],
                name=options["school"].replace("-", " ").title(),
                phone="+254700000000",
                email="admin@demo.com",
            )
            self.stdout.write(self.style.SUCCESS(f"Created school: {school.name}"))

        try:
            distributor = DistributorProfile.objects.get(
                company_name=options["distributor"], is_verified=True
            )
        except DistributorProfile.DoesNotExist:
            raise CommandError(
                f"Verified distributor '{options['distributor']}' not found. "
                "Run 'seed_distributor_catalog' or create a verified distributor first."
            )

        created_products = 0
        created_variants = 0
        with transaction.atomic():
            for example in EXAMPLES:
                category, _ = ProductCategory.objects.get_or_create(
                    school=school, name=example["category"]
                )

                product_kwargs = {
                    "school": school,
                    "category": category,
                    "name": example["name"],
                    "description": example.get("description", ""),
                    "is_active": True,
                    "is_reseller_listing": "dist_product_name" in example,
                }

                dist_product = None
                if "dist_product_name" in example:
                    dist_product = DistributorProduct.objects.filter(
                        distributor=distributor,
                        name=example["dist_product_name"],
                        is_active=True,
                    ).first()
                    if dist_product is None:
                        self.stdout.write(
                            self.style.WARNING(
                                f"  Distributor product '{example['dist_product_name']}' "
                                f"not found; creating as a non-reseller listing."
                            )
                        )
                    else:
                        product_kwargs["linked_distributor_product"] = dist_product
                        product_kwargs["markup_type"] = example["markup_type"]
                        product_kwargs["markup_value"] = example["markup_value"]

                if "price" in example:
                    product_kwargs["price"] = example["price"]

                product, created = Product.objects.get_or_create(
                    school=school, category=category, name=example["name"],
                    defaults=product_kwargs,
                )
                if created:
                    # save() recomputes price/commission from the markup.
                    product.save()
                    created_products += 1
                    self.stdout.write(self.style.SUCCESS(f"Created product: {product.name}"))
                else:
                    self.stdout.write(self.style.WARNING(f"Product exists: {product.name}"))

                grade = None
                if example.get("grade"):
                    grade = Grade.objects.filter(name=example["grade"]).first()

                for variant_def in example["variants"]:
                    variant, v_created = ProductVariant.objects.get_or_create(
                        product=product, label=variant_def["label"],
                        defaults={"stock_quantity": variant_def["stock"]},
                    )
                    if v_created:
                        created_variants += 1
                    if grade:
                        product.applicable_levels.add(grade)

        self.stdout.write(
            self.style.SUCCESS(
                f"Done. {created_products} new product(s), {created_variants} new variant(s)."
            )
        )
