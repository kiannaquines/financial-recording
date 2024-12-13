from django.db import models
from datetime import datetime, timedelta
from django.forms import ValidationError
from django.utils.timezone import now

class Assistance(models.Model):
    ASSISTANCE_TYPE = (
        ('Medical', 'Medical'),
        ('Education', 'Education'),
        ('Burial', 'Burial'),
    )

    client = models.ForeignKey(
        "Client", related_name="assistances", on_delete=models.CASCADE
    )
    assistance_type = models.CharField(max_length=100, choices=ASSISTANCE_TYPE)
    amount = models.DecimalField(max_digits=10, default=7000, decimal_places=2, null=True, blank=True)
    is_notified = models.BooleanField(default=False, null=True, blank=True)
    is_claimed = models.BooleanField(default=False, null=True, blank=True)
    is_ready = models.BooleanField(default=False, null=True, blank=True)
    date_provided = models.DateField(auto_now_add=False, null=True, blank=True)
    date_added = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.assistance_type} assistance for {self.client.get_fullname()}"

    class Meta:
        verbose_name = 'Assistance'
        verbose_name_plural = 'Assistance'


class Client(models.Model):

    MARITAL_STATUS = (
        ("Single", "Single"),
        ("Married", "Married"),
        ("Divorced", "Divorced"),
        ("Widowed", "Widowed"),
        ("Annulled", "Annulled"),
    )

    CLIENT_TYPE = (
        ("Senior Citizen", "Senior Citizen"),
        ("Family Solo Parent", "Family Solo Parent"),
        ("PWD", "PWD"),
    )

    first_name = models.CharField(max_length=50, unique=False, db_index=True)
    middle_name = models.CharField(max_length=50, unique=False, db_index=True, blank=True, null=True, help_text="Optional middle name")
    last_name = models.CharField(max_length=50, unique=False, db_index=True)
    contact_number = models.CharField(max_length=50, unique=True, db_index=True)
    gender = models.CharField(
        max_length=10, db_index=True, choices=(("Male", "Male"), ("Female", "Female"))
    )
    marital_status = models.CharField(
        max_length=50, db_index=True, choices=MARITAL_STATUS
    )
    birth_date = models.DateField(auto_now_add=False, null=False, db_index=True)
    barangay = models.CharField(max_length=255, null=False, db_index=True)
    address = models.TextField(max_length=255, null=False)
    client_type = models.CharField(max_length=50, choices=CLIENT_TYPE)
    date_added = models.DateTimeField(auto_now_add=True)

    def get_age(self):
        today = datetime.now().date()
        return (
            today.year
            - self.birth_date.year
            - ((today.month, today.day) < (self.birth_date.month, self.birth_date.day))
        )

    def get_fullname(self):
        middle_initial = (
            self.middle_name.split()[0].capitalize() if self.middle_name else ""
        )
        return f"{self.first_name} {middle_initial} {self.last_name}".strip()

    def __str__(self) -> str:
        return self.get_fullname()
    

    class Meta:
        verbose_name = 'Client'
        verbose_name_plural = 'Clients'


class Beneficiary(models.Model):

    RELATIONSHIP_TYPE = (
        ('Father', 'Father'),
        ('Mother','Mother'),
        ('Son','Son'),
        ('Daughter','Daughter'),
        ('Grand parent', 'Grand parent'),
    )

    client_id = models.ForeignKey(
        Client, on_delete=models.SET_NULL, null=True, blank=True
    )
    first_name = models.CharField(max_length=50, null=False, db_index=True)
    middle_name = models.CharField(max_length=50, null=False, db_index=True)
    last_name = models.CharField(max_length=50, null=False, db_index=True)
    birth_date = models.DateField(auto_now_add=False, null=False, db_index=True)
    contact_number = models.CharField(max_length=50, unique=True, db_index=True)
    relationship_type = models.CharField(
        max_length=50, db_index=True, choices=RELATIONSHIP_TYPE,
        null=True, blank=True
    )
    gender = models.CharField(
        max_length=10, db_index=True, choices=(("Male", "Male"), ("Female", "Female"))
    )
    address = models.TextField(max_length=255, null=False)
    date_added = models.DateTimeField(auto_now_add=True)

    def get_fullname(self):
        middle_initial = (
            self.middle_name.split()[0].capitalize() if self.middle_name else ""
        )
        return f"{self.first_name} {middle_initial} {self.last_name}".strip()

    def get_age(self):
        today = datetime.now().date()
        return (
            today.year
            - self.birth_date.year
            - ((today.month, today.day) < (self.birth_date.month, self.birth_date.day))
        )
    
    def __str__(self) -> str:
        return self.get_fullname()
    
    class Meta:
        verbose_name = 'Beneficiary'
        verbose_name_plural = 'Beneficiaries'



class NotificationSetting(models.Model):
    DEFAULT_TEMPLATE = """Good morning {name}, ito po ay galing sa opisina ng MSWD Carmen pina paalalahan po namin kayo na ngayong araw po pwedi na ninyo eclaim ang cash assistance niyo para sa {assistance_type} assistance.

Please be on time po dahil hanggang 8:00 am - 12:00 pm lang po ang claim hours.

Have a good day ahead,
From MSWD Carmen
    """
    notification_name = models.CharField(max_length=255)
    notification_message = models.TextField(max_length=500, default=DEFAULT_TEMPLATE)
    is_primary_notification = models.BooleanField(default=False)
    date_added = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.notification_name
    
    class Meta:
        verbose_name = 'Notification Setting'