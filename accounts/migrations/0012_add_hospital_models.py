# Generated migration for Hospital and HospitalStaff models

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0011_add_trust_system_and_firebase'),
    ]

    operations = [
        migrations.CreateModel(
            name='Hospital',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('hospital_type', models.CharField(choices=[('government', 'Government Hospital'), ('private', 'Private Hospital'), ('ngo', 'NGO Blood Bank'), ('blood_bank', 'Blood Bank')], default='private', max_length=20)),
                ('license_number', models.CharField(help_text='Hospital license/registration number', max_length=100, unique=True)),
                ('address', models.TextField()),
                ('city', models.CharField(max_length=100)),
                ('state', models.CharField(max_length=100)),
                ('pincode', models.CharField(max_length=10)),
                ('latitude', models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True)),
                ('longitude', models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True)),
                ('phone', models.CharField(max_length=15)),
                ('email', models.EmailField()),
                ('verification_status', models.CharField(choices=[('pending', 'Pending Verification'), ('verified', 'Verified'), ('rejected', 'Rejected')], default='pending', max_length=20)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='HospitalStaff',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role', models.CharField(choices=[('admin', 'Hospital Admin'), ('doctor', 'Doctor'), ('nurse', 'Nurse'), ('coordinator', 'Blood Donation Coordinator')], default='coordinator', max_length=20)),
                ('employee_id', models.CharField(max_length=50, unique=True)),
                ('department', models.CharField(blank=True, max_length=100)),
                ('can_create_requests', models.BooleanField(default=True)),
                ('can_approve_requests', models.BooleanField(default=False)),
                ('can_manage_inventory', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('hospital', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='staff', to='accounts.hospital')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='hospital_staff_profile', to='accounts.user')),
            ],
        ),
    ]
