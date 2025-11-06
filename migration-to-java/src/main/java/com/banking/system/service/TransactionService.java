package com.banking.system.service;

import com.banking.system.constant.TransactionType;
import com.banking.system.dto.TransactionRequest;
import com.banking.system.model.Transaction;
import com.banking.system.model.UserBankAccount;
import com.banking.system.repository.TransactionRepository;
import com.banking.system.repository.UserBankAccountRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.List;

@Service
@RequiredArgsConstructor
public class TransactionService {
    
    private final TransactionRepository transactionRepository;
    private final UserBankAccountRepository accountRepository;
    
    @Value("${banking.transaction.minimum-deposit}")
    private BigDecimal minimumDeposit;
    
    @Value("${banking.transaction.minimum-withdrawal}")
    private BigDecimal minimumWithdrawal;
    
    @Transactional
    public Transaction deposit(UserBankAccount account, BigDecimal amount) {
        if (amount.compareTo(minimumDeposit) < 0) {
            throw new IllegalArgumentException(
                "You need to deposit at least " + minimumDeposit + " $"
            );
        }
        
        if (account.getInitialDepositDate() == null) {
            LocalDate now = LocalDate.now();
            int nextInterestMonth = 12 / account.getAccountType().getInterestCalculationPerYear();
            
            account.setInitialDepositDate(now);
            account.setInterestStartDate(now.plusMonths(nextInterestMonth));
        }
        
        account.setBalance(account.getBalance().add(amount));
        accountRepository.save(account);
        
        Transaction transaction = new Transaction();
        transaction.setAccount(account);
        transaction.setAmount(amount);
        transaction.setBalanceAfterTransaction(account.getBalance());
        transaction.setTransactionType(TransactionType.DEPOSIT);
        transaction.setTimestamp(LocalDateTime.now());
        
        return transactionRepository.save(transaction);
    }
    
    @Transactional
    public Transaction withdraw(UserBankAccount account, BigDecimal amount) {
        if (amount.compareTo(minimumWithdrawal) < 0) {
            throw new IllegalArgumentException(
                "You can withdraw at least " + minimumWithdrawal + " $"
            );
        }
        
        BigDecimal maxWithdrawal = account.getAccountType().getMaximumWithdrawalAmount();
        if (amount.compareTo(maxWithdrawal) > 0) {
            throw new IllegalArgumentException(
                "You can withdraw at most " + maxWithdrawal + " $"
            );
        }
        
        account.setBalance(account.getBalance().subtract(amount));
        accountRepository.save(account);
        
        Transaction transaction = new Transaction();
        transaction.setAccount(account);
        transaction.setAmount(amount);
        transaction.setBalanceAfterTransaction(account.getBalance());
        transaction.setTransactionType(TransactionType.WITHDRAWAL);
        transaction.setTimestamp(LocalDateTime.now());
        
        return transactionRepository.save(transaction);
    }
    
    public List<Transaction> getTransactions(UserBankAccount account) {
        return transactionRepository.findByAccountOrderByTimestampAsc(account);
    }
    
    public List<Transaction> getTransactionsByDateRange(
        UserBankAccount account, 
        LocalDateTime start, 
        LocalDateTime end
    ) {
        return transactionRepository.findByAccountAndTimestampBetweenOrderByTimestampAsc(
            account, start, end
        );
    }
}
