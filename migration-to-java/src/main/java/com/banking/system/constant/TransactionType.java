package com.banking.system.constant;

public class TransactionType {
    public static final Integer DEPOSIT = 1;
    public static final Integer WITHDRAWAL = 2;
    public static final Integer INTEREST = 3;
    
    public static String getDisplayName(Integer type) {
        return switch (type) {
            case 1 -> "Deposit";
            case 2 -> "Withdrawal";
            case 3 -> "Interest";
            default -> "Unknown";
        };
    }
}
