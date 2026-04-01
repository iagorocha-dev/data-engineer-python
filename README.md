# Case Python (ViaCEP)

Pipeline para processamento de CEPs a partir de um CSV, com integração à API ViaCEP, tratamento de erros e persistência em banco de dados.

---

## 🚀 Funcionalidades

- 📊 Leitura de CEPs a partir de CSV
- 🔍 Normalização e validação de CEPs
- 🌐 Consulta à API ViaCEP
- ⚡ Processamento paralelo com controle de concorrência
- 🔄 Retry com backoff para falhas transitórias
- 📋 Registro de erros em CSV (`errors.csv`)
- 📊 Persistência de endereços em banco SQLite
- 🏗️ Estrutura modular e organizada

---

## 📦 Requisitos

- Python 3.11+ (recomendado)
- Git

---

## ⚙️ Setup

### Criar ambiente virtual
```bash
python -m venv .venv
```

### Ativar ambiente virtual

macOS / Linux:
```bash
source .venv/bin/activate
```

Windows (CMD):
```bash
.venv\Scripts\activate
```

## 📥 Instalar dependências
```bash
pip install -r requirements.txt
```

## ▶️ Executar o pipeline
```bash
python -m src.main
```

## 📄 Geração do arquivo de entrada

Para gerar o CSV com 10.000 CEPs:

```bash
python -m src.io.generate_ceps
```

## 📤 Saídas do processamento

Após a execução, os seguintes arquivos serão gerados em `data/output/`:

- errors.csv → Relatório de erros de validação e consulta
- ceps.db → Banco SQLite contendo os endereços processados com sucesso


## 🏗️ Arquitetura (visão geral)

O projeto segue separação de responsabilidades:
- io/ → leitura e escrita de arquivos
- viacep/ → integração com API ViaCEP
- db/ → persistência em banco de dados
- config.py → configurações da aplicação
- main.py → orquestração do pipeline

## ⚙️ Configurações

As configurações do projeto estão definidas no arquivo `src/config.py`:

Exemplos:
- max_concurrency
- request_timeout_seconds
- max_retries
- database_url


## 📝 Observações

- O processamento utiliza concorrência controlada para evitar sobrecarga da API ViaCEP
- Durante os testes, foi observado bloqueio temporário ao realizar muitas requisições sem controle de concorrência, reforçando a importância do rate limiting
- CEPs são validados em duas etapas:
  - formato (validação local)
  - existência (via API)
- CEPs inexistentes são registrados como erro (not_found)