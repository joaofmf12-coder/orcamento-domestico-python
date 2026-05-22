# 💰 Sistema de Orçamento Doméstico

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red?logo=streamlit&logoColor=white)
![MySQL](https://img.shields.io/badge/MySQL-8.0+-orange?logo=mysql&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0+-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

Sistema completo de controle financeiro pessoal desenvolvido em **Python + Streamlit**, com banco de dados **MySQL**. Permite gestão de receitas, despesas, cartões de crédito, investimentos, fluxo de caixa e conciliação bancária.

> 🎯 **Projeto desenvolvido para consolidar conhecimentos em Python, SQL e desenvolvimento web, com foco em boas práticas de arquitetura de software.**

---

## ✨ Funcionalidades

### 📝 Lançamentos
- **Receitas** — Salários, benefícios, serviços e rendas extras
- **Despesas** — Pagamentos à vista (Débito/PIX/Dinheiro)
- **Cartões de Crédito** — Compras parceladas com geração automática de parcelas
- **Investimentos** — Controle de aportes e resgates por tipo de ativo

### 📊 Análises e Relatórios
- **Dashboard** — KPIs financeiros, gráficos interativos (Plotly)
- **Orçamento** — Comparativo Previsto vs Realizado por categoria
- **Fluxo de Caixa** — Visão mensal + projeção dos próximos 30 dias
- **Análise por Categoria** — Distribuição de gastos com gráficos de pizza

### ⚙️ Recursos Avançados
- ✅ Parcelas de cartão geradas automaticamente (respeita dia de corte/vencimento)
- ✅ Previsões financeiras (únicas e recorrentes)
- ✅ Conciliação bancária
- ✅ Múltiplas contas bancárias
- ✅ Regime de Competência (Orçamento) vs Regime de Caixa (Fluxo de Caixa)

---

## 🎯 Arquitetura: Single Source of Truth

O projeto adota o princípio de **Single Source of Truth (Fonte Única de Verdade)**, concentrando todas as regras de negócio e cálculos financeiros em um módulo central (`services/financeiro_central.py`).

**Benefícios desta abordagem:**
| Aspecto | Descrição |
|---------|-----------|
| 🔄 **Consistência** | Mesmos dados em todas as telas (Dashboard, Relatórios, Fluxo de Caixa) |
| 🐛 **Manutenibilidade** | Correções em um único lugar propagam para todo o sistema |
| 📊 **Auditabilidade** | Fácil rastrear a origem dos dados |
| 🧪 **Testabilidade** | Funções centralizadas facilitam testes unitários |

---

## 📁 Estrutura do Projeto

### Arquivos Raiz
| Arquivo | Descrição |
|---------|-----------|
| `app.py` | Ponto de entrada da aplicação Streamlit |
| `requirements.txt` | Lista de dependências Python |
| `.env.example` | Modelo para configuração do banco de dados |
| `.gitignore` | Arquivos e pastas ignorados pelo Git |

### 📂 database/ — Camada de Dados
| Arquivo | Descrição |
|---------|-----------|
| `connection.py` | Gerencia conexão com MySQL via SQLAlchemy |
| `models.py` | Define as tabelas do banco (ORM) |

### 📂 services/ — Camada de Negócios
| Arquivo | Descrição |
|---------|-----------|
| `financeiro_central.py` | 🎯 **Módulo central** - Single Source of Truth |
| `receitas.py` | Operações de receitas |
| `despesas.py` | Operações de despesas |
| `cartoes.py` | Lógica de cartões e geração de parcelas |
| `contas.py` | Gestão de contas bancárias |

### 📂 pages/ — Camada de Apresentação
| Arquivo | Descrição |
|---------|-----------|
| `dashboard.py` | KPIs e gráficos principais |
| `lancamentos.py` | Cadastro de receitas, despesas e cartões |
| `fluxo_caixa.py` | Fluxo de caixa mensal + próximos 30 dias |
| `orcamento.py` | Comparativo Orçado vs Realizado |
| `previsoes.py` | Gestão de previsões financeiras |
| `relatorios.py` | Relatórios analíticos com gráficos |

=---

## 🛠️ Tecnologias Utilizadas

| Tecnologia | Uso no Projeto |
|------------|----------------|
| **Python 3.1+** | Linguagem principal |
| **Streamlit** | Interface web interativa |
| **MySQL 8.0** | Banco de dados relacional |
| **SQLAlchemy** | ORM para consultas estruturadas |
| **Pandas** | Manipulação e análise de dados |
| **Plotly** | Gráficos interativos |
| **python-dotenv** | Gerenciamento de variáveis de ambiente |

---

## 🚀 Como Executar

### Pré-requisitos
- Python 3.1 ou superior
- MySQL Server instalado e rodando
- Git

### 1. Clone o repositório

git clone https://github.com/seu-usuario/orcamento-domestico.git
cd orcamento-domestico

### 2. Crie e ative o ambiente virtual

python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate

### 3. Instale as dependências

pip install -r requirements.txt

### 4. Configure as variáveis de ambiente

Crie um arquivo .env na raiz do projeto:

MYSQL_USER=seu_usuario
MYSQL_PASSWORD=sua_senha
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_DATABASE=orcamento_domestico

### 5. Execute a aplicação

streamlit run app.py
A aplicação estará disponível em http://localhost:8501

# 📸 Screenshots
<img width="1804" height="867" alt="image" src="https://github.com/user-attachments/assets/d5fee93a-4ce5-49e3-aa59-93d67d23a757" />


<img width="1824" height="860" alt="image" src="https://github.com/user-attachments/assets/14171658-5d65-4fba-a772-c241004cb802" />


<img width="1816" height="812" alt="image" src="https://github.com/user-attachments/assets/a324b9dc-d887-449b-a033-2c36732cdd57" />


<img width="1819" height="833" alt="image" src="https://github.com/user-attachments/assets/17f1bf1b-8d40-480d-9522-f6edf434d250" />


📚 Aprendizados e Desafios

#Este projeto foi uma excelente oportunidade para consolidar conhecimentos em:


Arquitetura de Software — Separação de responsabilidades (MVC adaptado)
Modelagem de Dados — Relacionamentos entre tabelas (1:N, N:M)
Regras de Negócio Financeiras — Regime de competência vs caixa, cálculo de faturas
SQL Avançado — Queries com agregações, UNION, subconsultas
UI/UX — Criação de interfaces intuitivas com Streamlit
Boas Práticas — Context managers, tratamento de exceções, código limpo

🤝 Contribuições
Contribuições são bem-vindas! Sinta-se à vontade para:

🐛 Reportar bugs
💡 Sugerir melhorias
🔀 Enviar pull requests

📄 Licença
Este projeto está sob a licença MIT. Veja o arquivo para mais detalhes.

👤 Autor
João F. M. Fonseca

⭐ Se este projeto foi útil para você, considere dar uma estrela!


---
