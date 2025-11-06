package com.banking.system.initializer;

import com.banking.system.constant.Gender;
import com.banking.system.constant.TransactionType;
import com.banking.system.model.*;
import com.banking.system.repository.*;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.boot.CommandLineRunner;
import org.springframework.context.annotation.Profile;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Component;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;

@Component
@Profile("demo")
@RequiredArgsConstructor
@Slf4j
public class DemoDataInitializer implements CommandLineRunner {
    
    private final UserRepository userRepository;
    private final BankAccountTypeRepository accountTypeRepository;
    private final UserBankAccountRepository bankAccountRepository;
    private final UserAddressRepository addressRepository;
    private final TransactionRepository transactionRepository;
    private final PasswordEncoder passwordEncoder;
    
    @Override
    public void run(String... args) {
        log.info("Initializing demo data...");
        
        BankAccountType savingsType = accountTypeRepository
            .findByName("Savings Account")
            .orElseGet(() -> {
                BankAccountType type = new BankAccountType();
                type.setName("Savings Account");
                type.setMaximumWithdrawalAmount(new BigDecimal("5000.00"));
                type.setAnnualInterestRate(new BigDecimal("5.00"));
                type.setInterestCalculationPerYear(12);
                return accountTypeRepository.save(type);
            });
        
        BankAccountType currentType = accountTypeRepository
            .findByName("Current Account")
            .orElseGet(() -> {
                BankAccountType type = new BankAccountType();
                type.setName("Current Account");
                type.setMaximumWithdrawalAmount(new BigDecimal("10000.00"));
                type.setAnnualInterestRate(new BigDecimal("2.50"));
                type.setInterestCalculationPerYear(6);
                return accountTypeRepository.save(type);
            });
        
        User demoUser = userRepository
            .findByEmail("demo@example.com")
            .orElseGet(() -> {
                User user = new User();
                user.setEmail("demo@example.com");
                user.setPassword(passwordEncoder.encode("demo123"));
                user.setFirstName("John");
                user.setLastName("Doe");
                return userRepository.save(user);
            });
        
        UserBankAccount account;
        if (demoUser.getAccount() == null) {
            account = new UserBankAccount();
            account.setUser(demoUser);
            account.setAccountType(savingsType);
            account.setAccountNo(1001L);
            account.setGender(Gender.MALE);
            account.setBirthDate(LocalDate.of(1990, 1, 1));
            account.setBalance(new BigDecimal("5000.00"));
            account.setInitialDepositDate(LocalDate.now().minusMonths(6));
            account.setInterestStartDate(LocalDate.now().plusMonths(1));
            account = bankAccountRepository.save(account);
        } else {
            account = demoUser.getAccount();
        }
        
        if (demoUser.getAddress() == null) {
            UserAddress address = new UserAddress();
            address.setUser(demoUser);
            address.setStreetAddress("123 Main Street");
            address.setCity("New York");
            address.setPostalCode(10001);
            address.setCountry("USA");
            addressRepository.save(address);
        }
        
        transactionRepository.deleteAll(
            transactionRepository.findByAccountOrderByTimestampAsc(account)
        );
        
        List<Object[]> transactionsData = List.of(
            new Object[]{TransactionType.DEPOSIT, new BigDecimal("1000.00"), LocalDateTime.now().minusDays(30)},
            new Object[]{TransactionType.DEPOSIT, new BigDecimal("2000.00"), LocalDateTime.now().minusDays(25)},
            new Object[]{TransactionType.WITHDRAWAL, new BigDecimal("500.00"), LocalDateTime.now().minusDays(20)},
            new Object[]{TransactionType.DEPOSIT, new BigDecimal("1500.00"), LocalDateTime.now().minusDays(15)},
            new Object[]{TransactionType.WITHDRAWAL, new BigDecimal("200.00"), LocalDateTime.now().minusDays(10)},
            new Object[]{TransactionType.DEPOSIT, new BigDecimal("800.00"), LocalDateTime.now().minusDays(5)},
            new Object[]{TransactionType.WITHDRAWAL, new BigDecimal("300.00"), LocalDateTime.now().minusDays(2)}
        );
        
        BigDecimal balance = BigDecimal.ZERO;
        List<Transaction> transactions = new ArrayList<>();
        
        for (Object[] data : transactionsData) {
            Integer transType = (Integer) data[0];
            BigDecimal amount = (BigDecimal) data[1];
            LocalDateTime timestamp = (LocalDateTime) data[2];
            
            if (transType.equals(TransactionType.DEPOSIT)) {
                balance = balance.add(amount);
            } else {
                balance = balance.subtract(amount);
            }
            
            Transaction transaction = new Transaction();
            transaction.setAccount(account);
            transaction.setAmount(amount);
            transaction.setBalanceAfterTransaction(balance);
            transaction.setTransactionType(transType);
            transaction.setTimestamp(timestamp);
            
            transactions.add(transaction);
        }
        
        transactionRepository.saveAll(transactions);
        
        account.setBalance(balance);
        bankAccountRepository.save(account);
        
        log.info("✅ Demo data created successfully!");
        log.info("Demo User: demo@example.com / demo123");
        log.info("Account Number: {}", account.getAccountNo());
        log.info("Balance: ${}", account.getBalance());
        log.info("Transactions: {}", transactions.size());
    }
}
