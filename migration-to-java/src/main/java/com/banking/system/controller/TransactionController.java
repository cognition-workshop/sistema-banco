package com.banking.system.controller;

import com.banking.system.constant.TransactionType;
import com.banking.system.dto.TransactionDateRangeRequest;
import com.banking.system.dto.TransactionRequest;
import com.banking.system.model.Transaction;
import com.banking.system.model.User;
import com.banking.system.model.UserBankAccount;
import com.banking.system.repository.UserRepository;
import com.banking.system.service.TransactionService;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.validation.BindingResult;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.servlet.mvc.support.RedirectAttributes;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.List;

@Controller
@RequestMapping("/transactions")
@RequiredArgsConstructor
public class TransactionController {
    
    private final TransactionService transactionService;
    private final UserRepository userRepository;
    
    @Value("${banking.demo.user.email:demo@example.com}")
    private String demoUserEmail;
    
    private UserBankAccount getDemoAccount() {
        User user = userRepository.findByEmail(demoUserEmail)
            .orElseThrow(() -> new RuntimeException("Demo user not found"));
        
        if (user.getAccount() == null) {
            throw new RuntimeException("Demo user has no account");
        }
        
        return user.getAccount();
    }
    
    @GetMapping("/report")
    public String transactionReport(
        @ModelAttribute TransactionDateRangeRequest dateRangeRequest,
        Model model
    ) {
        UserBankAccount account = getDemoAccount();
        List<Transaction> transactions;
        
        if (dateRangeRequest.getDaterange() != null && !dateRangeRequest.getDaterange().isEmpty()) {
            try {
                String[] dates = dateRangeRequest.getDaterange().split(" - ");
                if (dates.length == 2) {
                    DateTimeFormatter formatter = DateTimeFormatter.ofPattern("yyyy-MM-dd");
                    LocalDateTime start = LocalDate.parse(dates[0], formatter).atStartOfDay();
                    LocalDateTime end = LocalDate.parse(dates[1], formatter).atTime(23, 59, 59);
                    
                    transactions = transactionService.getTransactionsByDateRange(account, start, end);
                } else {
                    transactions = transactionService.getTransactions(account);
                }
            } catch (Exception e) {
                transactions = transactionService.getTransactions(account);
            }
        } else {
            transactions = transactionService.getTransactions(account);
        }
        
        model.addAttribute("account", account);
        model.addAttribute("transactions", transactions);
        model.addAttribute("form", dateRangeRequest);
        model.addAttribute("TransactionType", TransactionType.class);
        
        return "transactions/transaction_report";
    }
    
    @GetMapping("/deposit")
    public String depositForm(Model model) {
        model.addAttribute("transactionRequest", new TransactionRequest());
        model.addAttribute("title", "Deposit Money to Your Account");
        return "transactions/transaction_form";
    }
    
    @PostMapping("/deposit")
    public String deposit(
        @Valid @ModelAttribute("transactionRequest") TransactionRequest request,
        BindingResult result,
        RedirectAttributes redirectAttributes,
        Model model
    ) {
        if (result.hasErrors()) {
            model.addAttribute("title", "Deposit Money to Your Account");
            return "transactions/transaction_form";
        }
        
        try {
            UserBankAccount account = getDemoAccount();
            transactionService.deposit(account, request.getAmount());
            
            redirectAttributes.addFlashAttribute("successMessage", 
                request.getAmount() + "$ was deposited to your account successfully");
            
            return "redirect:/transactions/report";
        } catch (IllegalArgumentException e) {
            model.addAttribute("errorMessage", e.getMessage());
            model.addAttribute("title", "Deposit Money to Your Account");
            return "transactions/transaction_form";
        }
    }
    
    @GetMapping("/withdraw")
    public String withdrawForm(Model model) {
        model.addAttribute("transactionRequest", new TransactionRequest());
        model.addAttribute("title", "Withdraw Money from Your Account");
        return "transactions/transaction_form";
    }
    
    @PostMapping("/withdraw")
    public String withdraw(
        @Valid @ModelAttribute("transactionRequest") TransactionRequest request,
        BindingResult result,
        RedirectAttributes redirectAttributes,
        Model model
    ) {
        if (result.hasErrors()) {
            model.addAttribute("title", "Withdraw Money from Your Account");
            return "transactions/transaction_form";
        }
        
        try {
            UserBankAccount account = getDemoAccount();
            transactionService.withdraw(account, request.getAmount());
            
            redirectAttributes.addFlashAttribute("successMessage", 
                "Successfully withdrawn " + request.getAmount() + "$ from your account");
            
            return "redirect:/transactions/report";
        } catch (IllegalArgumentException e) {
            model.addAttribute("errorMessage", e.getMessage());
            model.addAttribute("title", "Withdraw Money from Your Account");
            return "transactions/transaction_form";
        }
    }
}
