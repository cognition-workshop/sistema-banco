package com.banking.system.service;

import com.banking.system.constant.TransactionType;
import com.banking.system.model.Transaction;
import com.banking.system.model.UserBankAccount;
import com.banking.system.repository.TransactionRepository;
import com.banking.system.repository.UserBankAccountRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;

@Service
@RequiredArgsConstructor
@Slf4j
public class InterestCalculationService {
    
    private final UserBankAccountRepository accountRepository;
    private final TransactionRepository transactionRepository;
    
    @Scheduled(cron = "0 0 0 1 * ?")
    @Transactional
    public void calculateInterest() {
        log.info("Starting monthly interest calculation");
        
        LocalDate today = LocalDate.now();
        int currentMonth = today.getMonthValue();
        
        List<UserBankAccount> accounts = accountRepository.findAccountsEligibleForInterest(
            BigDecimal.ZERO, 
            today
        );
        
        List<Transaction> transactionsToCreate = new ArrayList<>();
        List<UserBankAccount> accountsToUpdate = new ArrayList<>();
        
        for (UserBankAccount account : accounts) {
            List<Integer> interestMonths = account.getInterestCalculationMonths();
            
            if (interestMonths.contains(currentMonth)) {
                BigDecimal interest = account.getAccountType().calculateInterest(
                    account.getBalance()
                );
                
                account.setBalance(account.getBalance().add(interest));
                accountsToUpdate.add(account);
                
                Transaction transaction = new Transaction();
                transaction.setAccount(account);
                transaction.setAmount(interest);
                transaction.setBalanceAfterTransaction(account.getBalance());
                transaction.setTransactionType(TransactionType.INTEREST);
                transaction.setTimestamp(LocalDateTime.now());
                
                transactionsToCreate.add(transaction);
            }
        }
        
        if (!accountsToUpdate.isEmpty()) {
            accountRepository.saveAll(accountsToUpdate);
        }
        
        if (!transactionsToCreate.isEmpty()) {
            transactionRepository.saveAll(transactionsToCreate);
        }
        
        log.info("Interest calculation completed. Updated {} accounts", accountsToUpdate.size());
    }
}
