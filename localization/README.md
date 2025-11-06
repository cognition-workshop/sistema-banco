# Localization App - Sistema Bancário Brasileiro

## Visão Geral

Aplicação Django para conformidade com regulamentações bancárias brasileiras (BACEN, LGPD, FEBRABAN, Receita Federal).

## Funcionalidades

### 1. Validação e Armazenamento de CPF
- Validação de CPF usando biblioteca validate-docbr
- Armazenamento criptografado (AES-256)
- Campo único no modelo User

### 2. Formato de Conta Bancária Brasileiro
- Agência: 4 dígitos
- Conta: 6 dígitos + 1 dígito verificador
- Conformidade com padrões FEBRABAN

### 3. Sistema PIX
- Cadastro de chaves PIX (CPF, Email, Telefone, Aleatória)
- Transferências instantâneas
- Geração e processamento de QR Code
- Limites configuráveis (por transação e diário)

### 4. Calendário Bancário
- Feriados nacionais, estaduais e municipais
- Cálculo de dias úteis
- Integração com sistema de juros

### 5. Log de Auditoria Imutável (BACEN)
- Hash criptográfico SHA-256
- Encadeamento de registros
- Verificação de integridade
- Retenção de 5 anos

### 6. Relatórios IRPF
- Relatório anual por CPF
- Exportação em CSV e PDF
- Resumo de movimentações financeiras

## Modelos

### ChavePIX
```python
- usuario: ForeignKey(User)
- tipo: CharField (CPF, EMAIL, TELEFONE, ALEATORIA)
- chave: CharField (unique)
- ativa: BooleanField
- data_cadastro: DateTimeField
```

### TransacaoPIX
```python
- conta_origem: ForeignKey(UserBankAccount)
- conta_destino: ForeignKey(UserBankAccount)
- chave_pix_destino: CharField
- valor: DecimalField
- status: CharField (PENDENTE, CONCLUIDA, FALHA, CANCELADA)
- identificador_transacao: CharField (unique)
```

### Feriado
```python
- nome: CharField
- data: DateField (unique)
- tipo: CharField (NACIONAL, ESTADUAL, MUNICIPAL)
- recorrente: BooleanField
```

### AuditLog
```python
- usuario: ForeignKey(User)
- conta: ForeignKey(UserBankAccount)
- tipo_operacao: CharField
- valor: DecimalField
- saldo_anterior/posterior: DecimalField
- hash_registro: CharField (unique)
- hash_anterior: CharField
- timestamp: DateTimeField
```

## REST APIs

### Usuários
- `POST /api/v1/usuarios/` - Cadastro com CPF
- `PUT /api/v1/usuarios/{id}/` - Atualização
- `GET /api/v1/usuarios/{id}/validar-cpf/` - Validação CPF

### PIX
- `POST /api/v1/pix/chaves/` - Cadastrar chave PIX
- `GET /api/v1/pix/chaves/` - Listar chaves
- `DELETE /api/v1/pix/chaves/{id}/` - Remover chave
- `POST /api/v1/pix/transferencias/` - Realizar transferência PIX
- `POST /api/v1/pix/transferencias/gerar_qrcode/` - Gerar QR Code
- `POST /api/v1/pix/transferencias/processar_qrcode/` - Processar QR Code

### Calendário
- `GET /api/v1/calendario/feriados/` - Listar feriados
- `POST /api/v1/calendario/feriados/calcular_prazo/` - Calcular prazo útil

### Auditoria
- `GET /api/v1/audit/logs/` - Consultar audit logs
- `GET /api/v1/audit/logs/{id}/verificar/` - Verificar integridade

### Relatórios IRPF
- `GET /api/v1/relatorios/irpf/gerar/?ano=2024` - Gerar relatório
- `GET /api/v1/relatorios/irpf/pdf/?ano=2024` - Download PDF
- `GET /api/v1/relatorios/irpf/csv/?ano=2024` - Download CSV

## Configurações de Segurança (LGPD)

```python
FIELD_ENCRYPTION_KEY = env('ENCRYPTION_KEY')
AUDIT_LOG_RETENTION_DAYS = 1825
PIX_TRANSACTION_LIMIT = Decimal('1000.00')
PIX_DAILY_LIMIT = Decimal('5000.00')
```

## Testes

Execute os testes:
```bash
python manage.py test localization
```

Verificar cobertura:
```bash
coverage run --source='localization' manage.py test localization
coverage report
```

Cobertura mínima esperada: 90%

## Documentação API

Acesse a documentação Swagger em:
- Swagger UI: `http://localhost:8000/swagger/`
- ReDoc: `http://localhost:8000/redoc/`

## Conformidade Regulatória

### BACEN (Banco Central do Brasil)
- Log de auditoria imutável com hash criptográfico
- Retenção de dados por 5 anos
- Rastreabilidade completa de operações

### LGPD (Lei Geral de Proteção de Dados)
- Criptografia de dados sensíveis (CPF)
- Controle de acesso baseado em autenticação
- Mascaramento de dados em logs

### FEBRABAN
- Formato padrão de conta bancária
- Dígito verificador conforme especificação

### Receita Federal
- Relatórios IRPF formatados
- Histórico completo de rendimentos

## Instalação

1. Adicionar ao INSTALLED_APPS:
```python
INSTALLED_APPS = [
    ...
    'localization',
]
```

2. Executar migrações:
```bash
python manage.py migrate
```

3. Popular dados iniciais:
```bash
python manage.py migrate localization
```

## Uso

### Exemplo: Transferência PIX

```python
from localization.services.pix_service import PIXService

transacao = PIXService.realizar_transferencia(
    conta_origem=conta_origem,
    chave_destino='user@example.com',
    valor=Decimal('100.00'),
    descricao='Pagamento'
)
```

### Exemplo: Verificar Dia Útil

```python
from localization.services.calendario_service import CalendarioService
from datetime import date

eh_util = CalendarioService.eh_dia_util(date(2024, 1, 1))
```

### Exemplo: Audit Log

```python
from localization.services.audit_service import AuditService

registro = AuditService.registrar_operacao(
    usuario=user,
    conta=account,
    tipo_operacao='DEPOSITO',
    valor=Decimal('100.00'),
    saldo_anterior=Decimal('900.00'),
    saldo_posterior=Decimal('1000.00'),
    descricao='Depósito via API'
)
```

## Licença

MIT License
