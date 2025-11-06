package com.banking.system.repository;

import com.banking.system.model.BankAccountType;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.Optional;

@Repository
public interface BankAccountTypeRepository extends JpaRepository<BankAccountType, Long> {
    Optional<BankAccountType> findByName(String name);
}
