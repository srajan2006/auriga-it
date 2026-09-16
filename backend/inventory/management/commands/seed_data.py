from django.core.management.base import BaseCommand
from django.db import transaction

from accounts.models import User
from inventory.models import Category, EquipmentModel, EquipmentUnit


class Command(BaseCommand):
    help = "Create repeatable AVault development users and inventory data."

    @transaction.atomic
    def handle(self, *args, **options):
        users = [
            ("admin@avault.local", "AVault Admin", User.Role.ADMIN, "ADMIN-001"),
            ("staff@avault.local", "AVault Staff", User.Role.STAFF, None),
            *[(f"student{i}@avault.local", f"Student {i}", User.Role.STUDENT, f"STU-{i:03d}") for i in range(1, 6)],
        ]
        for email, name, role, student_id in users:
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    "name": name,
                    "role": role,
                    "student_id": student_id,
                    "is_staff": role in {User.Role.STAFF, User.Role.ADMIN},
                    "is_superuser": role == User.Role.ADMIN,
                },
            )
            if created or not user.check_password("ChangeMe123!"):
                user.set_password("ChangeMe123!")
                user.save(update_fields=["password"])

        equipment = [
            ("DSLR", "Canon EOS 1500D", "Canon", "EOS-1500D", "5000.00", "50.00", ["DSLR-001", "DSLR-002", "DSLR-003"]),
            ("Projector", "Epson Projector", "Epson", "EB-X06", "3000.00", "30.00", ["PROJECTOR-001", "PROJECTOR-002"]),
            ("Microphone", "Wireless Microphone", "Shure", "BLX24", "1500.00", "20.00", ["MIC-001", "MIC-002", "MIC-003"]),
            ("Tripod", "Manfrotto Tripod", "Manfrotto", "MT190XPRO4", "1000.00", "15.00", ["TRIPOD-001", "TRIPOD-002"]),
            ("Lighting", "LED Video Light", "Godox", "SL-60W", "1200.00", "20.00", ["LIGHT-001", "LIGHT-002"]),
        ]
        for category_name, name, manufacturer, model_number, deposit, late_fee, asset_codes in equipment:
            category, _ = Category.objects.get_or_create(name=category_name)
            equipment_model, _ = EquipmentModel.objects.update_or_create(
                name=name,
                manufacturer=manufacturer,
                model_number=model_number,
                defaults={
                    "category": category,
                    "deposit_amount": deposit,
                    "late_fee_per_day": late_fee,
                    "max_borrow_quantity": len(asset_codes),
                    "is_active": True,
                },
            )
            for asset_code in asset_codes:
                EquipmentUnit.objects.get_or_create(
                    asset_code=asset_code,
                    defaults={"equipment_model": equipment_model, "location": "AV Room"},
                )

        self.stdout.write(self.style.SUCCESS("AVault development users and inventory seeded."))
        self.stdout.write("Default password for seeded users: ChangeMe123!")
