package com.banking.system.model;

import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.List;

@Entity
@Table(name = "user_bank_accounts")
@Data
@NoArgsConstructor
@AllArgsConstructor
public class UserBankAccount {
    
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    
    @OneToOne
    @JoinColumn(name = "user_id", nullable = false)
    private User user;
    
    @ManyToOne
    @JoinColumn(name = "account_type_id", nullable = false)
    private BankAccountType accountType;
    
    @Column(unique = true, nullable = false)
    private Long accountNo;
    
    @Column(nullable = false, length = 1)
    private String gender;
    
    private LocalDate birthDate;
    
    @Column(nullable = false, precision = 12, scale = 2)
    private BigDecimal balance = BigDecimal.ZERO;
    
    private LocalDate interestStartDate;
    private LocalDate initialDepositDate;
    
    @OneToMany(mappedBy = "account", cascade = CascadeType.ALL)
    private List<Transaction> transactions = new ArrayList<>();
    
    public List<Integer> getInterestCalculationMonths() {
        if (interestStartDate == null || accountType == null) {
            return new ArrayList<>();
        }
        
        int interval = 12 / accountType.getInterestCalculationPerYear();
        int start = interestStartDate.getMonthValue();
        
        List<Integer> months = new ArrayList<>();
        for (int i = start; i <= 12; i += interval) {
            months.add(i);
        }
        return months;
    }
}
