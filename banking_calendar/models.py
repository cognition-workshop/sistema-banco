from django.db import models


class BankingHoliday(models.Model):
    date = models.DateField(unique=True)
    name = models.CharField(max_length=255)
    is_national = models.BooleanField(
        default=True,
        help_text='True for national holidays, False for regional'
    )
    description = models.TextField(blank=True)

    class Meta:
        ordering = ['date']

    def __str__(self):
        return f"{self.name} - {self.date}"
