package com.banking.system.model;

import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.math.BigDecimal;

@Entity
@Table(name = "users")
@Data
@NoArgsConstructor
@AllArgsConstructor
public class User {
    
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    
    @Column(unique = true, nullable = false)
    private String email;
    
    @Column(nullable = false)
    private String password;
    
    private String firstName;
    private String lastName;
    
    @OneToOne(mappedBy = "user", cascade = CascadeType.ALL)
    private UserBankAccount account;
    
    @OneToOne(mappedBy = "user", cascade = CascadeType.ALL)
    private UserAddress address;
    
    public BigDecimal getBalance() {
        if (account != null) {
            return account.getBalance();
        }
        return BigDecimal.ZERO;
    }
}
