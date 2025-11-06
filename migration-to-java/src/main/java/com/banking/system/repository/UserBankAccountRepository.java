package com.banking.system.repository;

import com.banking.system.model.UserBankAccount;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.stereotype.Repository;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.List;

@Repository
public interface UserBankAccountRepository extends JpaRepository<UserBankAccount, Long> {
    
    @Query("SELECT a FROM UserBankAccount a " +
           "WHERE a.balance > :minBalance " +
           "AND a.interestStartDate >= :currentDate " +
           "AND a.initialDepositDate IS NOT NULL")
    List<UserBankAccount> findAccountsEligibleForInterest(
        BigDecimal minBalance, 
        LocalDate currentDate
    );
}
