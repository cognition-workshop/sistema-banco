from decimal import Decimal
from typing import List


class InterestCalculationService:
    """
    Service layer for handling interest calculation business logic.
    
    This service encapsulates all interest-related calculations,
    separating business logic from the Celery task orchestration.
    """
    
    @staticmethod
    def calculate_interest(principal: Decimal, annual_interest_rate: Decimal, 
                          interest_calculation_per_year: int) -> Decimal:
        """
        Calculate interest for a given principal amount.
        
        Uses compound interest formula: (P * (1 + (r/100 / n))) - P
        
        Args:
            principal: The principal amount (account balance)
            annual_interest_rate: Annual interest rate percentage (0-100)
            interest_calculation_per_year: Number of times interest is calculated per year (1-12)
            
        Returns:
            Calculated interest amount rounded to 2 decimal places
        """
        p = principal
        r = annual_interest_rate
        n = Decimal(interest_calculation_per_year)
        
        interest = (p * (1 + ((r / 100) / n))) - p
        
        return round(interest, 2)
    
    @staticmethod
    def get_interest_calculation_months(interest_start_month: int, 
                                       interest_calculation_per_year: int) -> List[int]:
        """
        Calculate which months interest should be calculated based on frequency.
        
        Args:
            interest_start_month: The starting month (1-12)
            interest_calculation_per_year: Number of times interest is calculated per year (1-12)
            
        Returns:
            List of month numbers (1-12) when interest should be calculated
            
        Example:
            For bi-monthly (every 2 months) starting from month 2:
            Returns [2, 4, 6, 8, 10, 12]
        """
        interval = int(12 / interest_calculation_per_year)
        return [i for i in range(interest_start_month, 13, interval)]
