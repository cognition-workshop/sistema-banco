package com.banking.system.model;

import jakarta.persistence.*;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.List;

@Entity
@Table(name = "bank_account_types")
@Data
@NoArgsConstructor
@AllArgsConstructor
public class BankAccountType {
    
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    
    @Column(nullable = false, length = 128)
    private String name;
    
    @Column(nullable = false, precision = 12, scale = 2)
    private BigDecimal maximumWithdrawalAmount;
    
    @Column(nullable = false, precision = 5, scale = 2)
    @Min(0)
    @Max(100)
    private BigDecimal annualInterestRate;
    
    @Column(nullable = false)
    @Min(1)
    @Max(12)
    private Integer interestCalculationPerYear;
    
    @OneToMany(mappedBy = "accountType")
    private List<UserBankAccount> accounts;
    
    public BigDecimal calculateInterest(BigDecimal principal) {
        BigDecimal p = principal;
        BigDecimal r = annualInterestRate;
        BigDecimal n = new BigDecimal(interestCalculationPerYear);
        
        BigDecimal interest = p.multiply(
            BigDecimal.ONE.add(
                r.divide(new BigDecimal(100), 10, RoundingMode.HALF_UP)
                 .divide(n, 10, RoundingMode.HALF_UP)
            )
        ).subtract(p);
        
        return interest.setScale(2, RoundingMode.HALF_UP);
    }
}
