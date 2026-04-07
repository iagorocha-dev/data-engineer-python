# Case Python (ViaCEP)

Pipeline para processamento de CEPs a partir de um CSV, com integração à API ViaCEP, tratamento de erros, persistência incremental e controles de resiliência para execução em escala.

---

## 🚀 Funcionalidades

- 📊 Leitura de CEPs a partir de CSV
- 🔍 Normalização e validação de CEPs
- 🌐 Consulta à API ViaCEP
- ⚡ Processamento assíncrono com controle de concorrência
- 🧱 Execução incremental em batches
- 🔄 Retry com backoff para falhas transitórias
- 📋 Registro de erros em CSV (`errors.csv`)
- 🗄️ Persistência de endereços em banco SQLite
- 📄 Exportação de resultados em JSON e XML
- 🛑 Interrupção segura em caso de indício de bloqueio ou indisponibilidade do serviço externo
- 🔁 Retomada de execução a partir do progresso já persistido

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

### Instalar dependências
```bash
pip install -r requirements.txt
```

---

## ▶️ Executar o pipeline

```bash
python -m src.main
```

---

## 📄 Geração do arquivo de entrada

Para gerar o CSV com 10.000 CEPs:

```bash
python -m src.io.generate_ceps
```

---

## 📤 Saídas do processamento

Após a execução, os seguintes arquivos serão gerados em `data/output/`:

- `errors.csv` → relatório de erros de validação e consulta
- `ceps.db` → banco SQLite contendo os endereços processados com sucesso
- `addresses.json` → arquivo JSON contendo os endereços processados com sucesso
- `addresses.xml` → arquivo XML contendo os endereços processados com sucesso

---

## 🏗️ Arquitetura (visão geral)

O projeto segue separação de responsabilidades:

- `io/` → leitura e escrita de arquivos
- `viacep/` → integração com API ViaCEP
- `db/` → persistência em banco de dados
- `config.py` → configurações da aplicação
- `main.py` → orquestração do pipeline
- `utils/logging.py` → configuração de logs

---

## ⚙️ Configurações

As configurações do projeto estão definidas em `src/config.py` e podem ser parametrizadas por variáveis de ambiente.

### Exemplo de `.env`

```env
DATABASE_URL=sqlite:///data/output/ceps.db
VIACEP_BASE_URL=https://viacep.com.br/ws
REQUEST_TIMEOUT_SECONDS=8
MAX_CONCURRENCY=10
MAX_RETRIES=2
REQUESTS_PER_SECOND=20
BATCH_PAUSE_SECONDS=0.5
BATCH_SIZE=100
LOG_LEVEL=INFO
```

### Parâmetros principais

- `REQUEST_TIMEOUT_SECONDS` → timeout de cada requisição HTTP
- `MAX_CONCURRENCY` → quantidade máxima de requisições simultâneas
- `MAX_RETRIES` → número de tentativas extras para falhas transitórias
- `REQUESTS_PER_SECOND` → limite de taxa de envio
- `BATCH_PAUSE_SECONDS` → pausa entre batches
- `BATCH_SIZE` → quantidade de CEPs processados por batch incremental

---

## 🚦 Estratégias de controle e proteção

Para evitar sobrecarga do ViaCEP e tornar a execução mais resiliente, o pipeline combina múltiplas estratégias:

- limite de concorrência (`Semaphore`)
- controle de taxa de requisições por segundo (rate limiter)
- processamento em batches
- pausa entre batches
- retry com backoff exponencial
- persistência incremental do progresso
- interrupção segura ao detectar forte indício de bloqueio ou indisponibilidade

Essas estratégias reduzem burst de tráfego, preservam o progresso já realizado e evitam insistência infinita em cenários degradados.

---

## 🚀 Performance e resiliência em escala

Foram realizados diversos testes empíricos com 10.000 CEPs para entender o comportamento do pipeline sob carga contínua e o padrão de tolerância da API ViaCEP.

### Objetivo dos testes

Validar:

- comportamento do pipeline em execução prolongada
- impacto de concorrência, RPS e pausas entre batches
- capacidade de retomada após bloqueios ou indisponibilidade
- configuração com melhor equilíbrio entre throughput e estabilidade

### Hipóteses levantadas ao longo dos testes

Os primeiros experimentos indicaram que reduzir apenas o throughput bruto não era suficiente para evitar bloqueios. Os sinais observados sugeriram que o ViaCEP parecia ser mais sensível a:

- frequência sustentada de chamadas ao longo do tempo
- burst de requisições
- padrão repetitivo vindo da mesma origem/IP
- excesso de concorrência combinado com baixa pausa entre lotes

Em outras palavras: não bastava “ficar mais lento”; era necessário ficar mais previsível e menos agressivo no padrão de envio.

---

## 🧪 Evolução dos testes

### Testes iniciais com interrupção segura

Dois testes anteriores mostraram que apenas reduzir a quantidade de CEPs processados não resolvia o problema de forma eficaz:

```text
Teste anterior:
attempted_now=3860
success_now=79
errors_now=3781
total_time=762.55s

Teste atual:
attempted_now=1910
success_now=33
errors_now=1877
total_time=720.45s
```

Esses números reforçaram a suspeita de que o bloqueio não estava relacionado somente ao total processado, mas também ao padrão temporal das requisições.

### Testes intermediários

Em execuções posteriores, observou-se uma janela recorrente de degradação por volta de ~190 batches em determinados cenários mais conservadores e, em cenários mais agressivos, a degradação passava a ocorrer ainda mais cedo.

Também foi possível confirmar que:

- a retomada do processamento funcionava corretamente
- o pipeline preservava o progresso anterior
- aumentar agressivamente `concurrency`, `rps_limit` e reduzir `batch_pause` elevava muito a chance de timeouts e falhas em cascata

### Cenários agressivos que degradaram

Algumas configurações com maior pressão sobre o serviço externo, como por exemplo:

- `batch_size=100`
- `max_concurrency=15`
- `rps_limit=22`
- `batch_pause=0.30s`

produziram throughput inicial mais alto, porém passaram a apresentar:

- crescimento de timeouts
- retries em massa
- falhas de conexão
- batches inteiros com `success=0`
- throughput efetivo despencando após o início da degradação

Isso indicou que o ganho inicial de velocidade não compensava a perda de estabilidade.

---

## ✅ Configuração validada empiricamente

A configuração que se mostrou estável para processar os 10.000 CEPs do início ao fim foi:

```env
BATCH_SIZE=100
MAX_CONCURRENCY=10
REQUESTS_PER_SECOND=20
BATCH_PAUSE_SECONDS=0.5
MAX_RETRIES=2
REQUEST_TIMEOUT_SECONDS=8
```

### Resultado da execução bem-sucedida

```text
attempted_now=10000
success_now=192
errors_now=9808
total_time=517.59s
```

### Leitura técnica do resultado

Esse experimento mostrou que o melhor equilíbrio não veio do cenário mais agressivo, mas sim de um perfil mais estável:

- `batch_size=100` → boa eficiência por lote
- `max_concurrency=10` → concorrência suficiente sem excesso de pressão
- `REQUESTS_PER_SECOND=20` → taxa elevada, porém ainda sustentável
- `BATCH_PAUSE_SECONDS=0.5` → pequeno respiro entre batches, reduzindo burst

### Principal conclusão prática

O fator decisivo não foi simplesmente “aumentar velocidade”, mas sim manter uma taxa alta sem parecer agressivo para o serviço externo.

Em resumo:

> o pipeline teve melhor desempenho quando foi rápido, mas previsível.

---

## 🛑 Interrupção segura por indício de bloqueio

Quando o serviço externo entra em degradação, o pipeline detecta sinais como:

- batch inteiro com falha
- throughput observado muito abaixo do normal
- explosão de retries por timeout/rede

Nesses casos, a execução é interrompida de forma segura para:

- evitar insistência infinita
- preservar o progresso já salvo
- permitir retomada posterior apenas dos CEPs pendentes

Esse comportamento foi essencial durante os testes exploratórios e comprovou a resiliência da solução.

---

## 📌 Observações importantes sobre os resultados

- O objetivo principal dos testes de escala foi validar robustez do pipeline e estratégia de consumo da API externa.
- A taxa de sucesso depende diretamente da disponibilidade e do comportamento do ViaCEP durante a janela de execução.
- O projeto foi desenhado para funcionar de forma segura mesmo quando o serviço externo oscila, degrada ou impõe algum tipo de limitação.
- A configuração vencedora é uma baseline validada empiricamente, mas ainda pode variar por IP, horário ou comportamento momentâneo do serviço externo.

---

## 🪵 Logging

O projeto utiliza o módulo padrão `logging` do Python.

### Níveis disponíveis

- `INFO` → visão geral da execução, batches e resultados acumulados
- `DEBUG` → detalhamento completo de rate limiting, retries e requisições

### Executar com debug

```bash
LOG_LEVEL=DEBUG python -m src.main
```

---

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
- iniciar processamento distribuído dos CEPs

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

### Considerações

- Lambda é mais adequado para processamento orientado a eventos e workloads menores
- Glue é mais indicado para processamento batch em larga escala
- a escolha entre eles depende principalmente do volume de dados e do tipo de processamento necessário

---

## 🧪 Testes automatizados

O projeto possui testes automatizados utilizando `pytest`.

### Executar testes

```bash
python -m pytest
```

### Executar testes com cobertura

```bash
python -m pytest --cov=src
```

### Resultado atual

- ✔️ 53 testes automatizados
- ✔️ ~99% de cobertura

---

## 📝 Observações adicionais

- CEPs são validados em duas etapas:
  - formato (validação local)
  - existência (via API)
- CEPs inexistentes são registrados como erro (`not_found`)
- CEPs inválidos também são registrados em `errors.csv`
- O processamento utiliza concorrência controlada justamente para reduzir o risco de bloqueio por IP
- Os testes mostraram, na prática, que o tuning de `concurrency`, `RPS` e `batch_pause` impacta diretamente a estabilidade da integração

---

## 🔧 Possíveis melhorias

- uso de PostgreSQL em produção
- cache de CEPs já consultados
- execução distribuída (fila + workers)
- observabilidade com métricas
- dashboard de execução e throughput
- parametrização via `.env` mais completa
- deploy em ambiente cloud (AWS)
- circuito de cooldown automático após sinais de degradação
- ajuste dinâmico de rate limit conforme comportamento observado em tempo real

---

## 🎯 Resumo técnico

O pipeline foi projetado para maximizar throughput respeitando limites externos, combinando:

- concorrência assíncrona
- rate limiting
- processamento incremental em batches
- persistência contínua
- retries com backoff
- interrupção segura em caso de indisponibilidade

Os testes em escala mostraram que a configuração mais eficiente não foi a mais agressiva, mas a mais estável. A baseline validada empiricamente para o cenário de 10.000 CEPs foi:

```text
batch_size=100
max_concurrency=10
rps_limit=20
batch_pause=0.50s
```

Essa combinação permitiu concluir a execução completa sem bloqueio, comprovando a robustez do pipeline frente às limitações de um serviço externo sujeito a degradação e controle de uso.
