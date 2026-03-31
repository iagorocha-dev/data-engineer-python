# Case Python (ViaCEP)

Pipeline para processar CEPs a partir de um CSV, consultar a API ViaCEP, registrar erros, persistir endereços em banco e exportar resultados (JSON e XML).

## Requisitos
- Python 3.11+ (recomendado)
- Git

## Setup

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

## Instalar dependências
```bash
pip install -r requirements.txt
```

## Executar
```bash
python -m src.main
```

## Geração do arquivo de entrada

Para gerar o CSV com 10.000 CEPs:

```bash
python -m src.io.generate_ceps