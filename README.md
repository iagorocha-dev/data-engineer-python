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
- addresses.json → Arquivo JSON contendo os endereços processados com sucesso
- addresses.xml → Arquivo XML contendo os endereços processados com sucesso

## 🏗️ Arquitetura (visão geral)

O projeto segue separação de responsabilidades:
- io/ → leitura e escrita de arquivos
- viacep/ → integração com API ViaCEP
- db/ → persistência em banco de dados
- config.py → configurações da aplicação
- main.py → orquestração do pipeline
- utils/logging.py → configuração de logs

## ⚙️ Configurações

As configurações do projeto estão definidas no arquivo `src/config.py`:

Exemplo .env:

```env
DATABASE_URL=sqlite:///data/output/ceps.db
VIACEP_BASE_URL=https://viacep.com.br/ws
REQUEST_TIMEOUT_SECONDS=8
MAX_CONCURRENCY=3
MAX_RETRIES=2
REQUESTS_PER_SECOND=3
BATCH_PAUSE_SECONDS=1.0
BATCH_SIZE=5
LOG_LEVEL=INFO
```

## 🚦 Controle de concorrência e taxa

Para evitar sobrecarga da API ViaCEP, o pipeline aplica múltiplas estratégias:

- Limite de concorrência (Semaphore)
- Controle de taxa de requisições por segundo (rate limiter)
- Execução em batches
- Pausa entre batches
- Retry com backoff exponencial

Essas estratégias garantem um consumo mais estável e reduzem o risco de bloqueio por IP.

## 🚀 Performance e Resiliência em Escala

Foi realizado um teste com 10.000 CEPs para validar o comportamento do pipeline em execução prolongada, considerando:

- concorrência controlada
- rate limiting
- processamento incremental em batches
- persistência contínua
- interrupção segura em caso de indisponibilidade do serviço externo

### ⚙️ Configuração utilizada

- Batch size: 20
- Concorrência máxima: 5
- Rate limit: 5 req/s
- Pausa entre batches: 1s
- Retries: 2

### 📈 Resultado observado

A execução iniciou normalmente e manteve comportamento estável durante os batches iniciais, com throughput consistente e sem falhas sistêmicas.

Após processamento prolongado, o serviço externo começou a degradar, levando a falhas de rede repetidas e aumento brusco no tempo de resposta de um batch.

### 📊 Resultado parcial antes da interrupção segura

```text
attempted_now=3860
success_now=79
errors_now=3781
total_time=762.55s
```

### ⚡ Comportamento do pipeline

Situação estável nos batches saudáveis:

```text
duration ≈ 3.2s
observed_throughput ≈ 6.1 ~ 6.2
```

Situação degradada no batch crítico:

```text
duration = 99.70s
observed_throughput = 0.20
success = 0
errors = 20
```

### 🛑 Interrupção automática por indício de bloqueio / indisponibilidade

Ao detectar um batch com falha sistêmica e throughput drasticamente reduzido, o pipeline interrompeu a execução de forma segura:

```text
Execução interrompida por indício de bloqueio ou indisponibilidade do ViaCEP
batch=193/500
remaining_after=6140
blocked_batch_errors=20
```

### 🧠 O que esse teste comprova

- ✔️ o pipeline suporta execução prolongada com milhares de registros
- ✔️ a concorrência e o rate limiting funcionam de forma estável enquanto o serviço responde normalmente
- ✔️ a persistência incremental preserva o progresso já realizado
- ✔️ a execução não insiste indefinidamente em cenário de falha sistêmica
- ✔️ a arquitetura permite retomada futura apenas dos CEPs pendentes

### 🛡️ Estratégia adotada

Como o ViaCEP é um serviço externo sujeito a indisponibilidade e possível limitação por uso prolongado, a solução foi desenhada para:

- respeitar limites de consumo
- processar em lotes pequenos e previsíveis
- persistir progresso continuamente
- interromper a execução quando houver forte indício de bloqueio ou degradação do serviço

### 🎯 Resumo técnico

O pipeline foi projetado para maximizar throughput respeitando limites externos, combinando concorrência assíncrona, rate limiting, processamento incremental e interrupção segura em caso de indisponibilidade.

## 🪵 Logging

O projeto utiliza o módulo padrão logging do Python.

Níveis disponíveis:
- INFO → visão geral da execução (batches)
- DEBUG → detalhamento completo (rate limiting, requisições, retries)

Executar com debug:
```bash
LOG_LEVEL=DEBUG python -m src.main
```

## ☁️ Conhecimento em AWS (Glue e Lambda)

### AWS Lambda

O AWS Lambda é um serviço serverless que permite executar código sob demanda, sem necessidade de gerenciar servidores.

É ideal para:
- processamento orientado a eventos
- tarefas de curta duração
- execução paralela com escalabilidade automática

No contexto deste projeto, o Lambda poderia ser utilizado para:
- processar arquivos enviados para o S3
- dividir o CSV em lotes menores
- iniciar o processamento distribuído dos CEPs

---

### AWS Glue

O AWS Glue é um serviço de ETL (Extract, Transform, Load) baseado em Apache Spark, utilizado para processamento de dados em larga escala.

É mais indicado para:
- processamento batch de grandes volumes de dados
- pipelines analíticos
- transformações complexas

No contexto deste projeto, o Glue poderia ser utilizado para:
- processar grandes volumes de CEPs diretamente a partir do S3
- executar o pipeline de forma distribuída
- integrar com data lakes ou bancos analíticos

---

### Considerações

- Lambda é mais adequado para processamento orientado a eventos e workloads menores
- Glue é mais indicado para processamento batch em larga escala
- A escolha entre eles depende principalmente do volume de dados e do tipo de processamento necessário


## 🧪 Testes

O projeto possui testes automatizados utilizando pytest.

Executar testes:
```bash
python -m pytest
```

Executar testes com cobertura:
```bash
python -m pytest --cov=src
```

Resultado atual
- ✔️ 53 testes automatizados
- ✔️ ~99% de cobertura


## 📝 Observações

- CEPs são validados em duas etapas:
  - formato (validação local)
  - existência (via API)
- CEPs inexistentes são registrados como erro (not_found)
- O processamento utiliza concorrência controlada para evitar sobrecarga da API ViaCEP
- Durante os testes, foi observado bloqueio temporário ao realizar muitas requisições sem controle de concorrência, reforçando a importância do rate limiting
- O uso de rate limiting e controle de concorrência resolve esse problema de forma segura


## 🔧 Possíveis melhorias
- Uso de banco PostgreSQL em produção
- Cache de CEPs já consultados
- Execução distribuída (fila + workers)
- Observabilidade com métricas
- Deploy em ambiente cloud (AWS)
