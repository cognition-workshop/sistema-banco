from django.db import models
from datetime import date, timedelta


class BankingHoliday(models.Model):
    HOLIDAY_TYPE_FEDERAL = 'FEDERAL'
    HOLIDAY_TYPE_BANKING = 'BANKING'
    HOLIDAY_TYPE_OPTIONAL = 'OPTIONAL'
    
    HOLIDAY_TYPE_CHOICES = [
        (HOLIDAY_TYPE_FEDERAL, 'Feriado Nacional'),
        (HOLIDAY_TYPE_BANKING, 'Feriado Bancário'),
        (HOLIDAY_TYPE_OPTIONAL, 'Ponto Facultativo'),
    ]
    
    name = models.CharField(max_length=200)
    date = models.DateField()
    holiday_type = models.CharField(
        max_length=20,
        choices=HOLIDAY_TYPE_CHOICES,
        default=HOLIDAY_TYPE_FEDERAL
    )
    is_recurring = models.BooleanField(
        default=True,
        help_text='Se True, o feriado se repete anualmente na mesma data'
    )
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Feriado Bancário'
        verbose_name_plural = 'Feriados Bancários'
        ordering = ['date']
        unique_together = ['date', 'name']
    
    def __str__(self):
        return f'{self.name} - {self.date.strftime("%d/%m/%Y")}'
    
    @classmethod
    def is_business_day(cls, check_date):
        if check_date.weekday() >= 5:
            return False
        
        return not cls.objects.filter(date=check_date).exists()
    
    @classmethod
    def get_next_business_day(cls, start_date):
        current_date = start_date + timedelta(days=1)
        
        while not cls.is_business_day(current_date):
            current_date += timedelta(days=1)
        
        return current_date
    
    @classmethod
    def count_business_days(cls, start_date, end_date):
        count = 0
        current_date = start_date
        
        while current_date <= end_date:
            if cls.is_business_day(current_date):
                count += 1
            current_date += timedelta(days=1)
        
        return count
