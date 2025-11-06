package com.banking.system.repository;

import com.banking.system.model.Transaction;
import com.banking.system.model.UserBankAccount;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.time.LocalDateTime;
import java.util.List;

@Repository
public interface TransactionRepository extends JpaRepository<Transaction, Long> {
    List<Transaction> findByAccountOrderByTimestampAsc(UserBankAccount account);
    
    List<Transaction> findByAccountAndTimestampBetweenOrderByTimestampAsc(
        UserBankAccount account, 
        LocalDateTime start, 
        LocalDateTime end
    );
}
