# Task Manager Flask

Aplicação Flask de gerenciamento de tarefas pessoais, adaptada com autenticação obrigatória, logging em stdout, preparação para Docker e requisitos iniciais de DevSecOps.

## Estrutura principal

- `todo_project/run.py`: ponto de entrada da aplicação.
- `todo_project/todo_project/__init__.py`: configuração da aplicação, extensões e logging.
- `todo_project/todo_project/routes.py`: rotas web, autenticação e operações de tarefa.
- `todo_project/todo_project/models.py`: modelos `User` e `Task`.
- `todo_project/todo_project/forms.py`: formulários Flask-WTF.
- `todo_project/todo_project/templates/`: telas HTML.
- `tests/`: testes automatizados com `pytest`.

## Medidas de segurança aplicadas

- Autenticação obrigatória nas rotas internas de tarefas e logout.
- Redirecionamento para login em acesso não autenticado, com log de segurança.
- Senhas armazenadas com hash via `Flask-Bcrypt`.
- `SECRET_KEY` lida de variável de ambiente, com fallback somente para desenvolvimento.
- Proteção CSRF preservada nos formulários Flask-WTF.
- Exclusão de tarefas alterada para `POST`, evitando remoção por `GET`.
- Validação de propriedade da tarefa para impedir acesso de um usuário aos dados de outro.
- SQLAlchemy ORM mantido, sem SQL manual inseguro.

## Eventos de log

Os logs são enviados para `stdout`, compatíveis com `docker logs` e coletores como syslog/rsyslog, Loki/Promtail, Fluent Bit e ELK.

Eventos registrados:

- `LOGIN_SUCESSO`
- `LOGIN_FALHA`
- `LOGOUT`
- `ACESSO_NAO_AUTENTICADO`
- `TAREFA_CRIADA`
- `TAREFA_EDITADA`
- `TAREFA_EXCLUIDA`
- `TAREFA_CONSULTADA`
- `PESQUISA_REALIZADA`
- `ERRO_INTERNO`

## Instalação local

```powershell
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
cd todo_project
python run.py
```

Por padrão a aplicação sobe em `http://127.0.0.1:5000`.

Variáveis úteis:

```powershell
$env:SECRET_KEY="uma-chave-segura"
$env:FLASK_DEBUG="1"
```

## Docker

Build:

```powershell
docker build -t task-manager-flask .
```

Execução:

```powershell
docker run -p 8080:8080 -e SECRET_KEY="uma-chave-segura" task-manager-flask
```

Também é possível usar:

```powershell
docker compose up --build
```

No container a aplicação escuta em `0.0.0.0:8080`.

## Testes

```powershell
pytest
```

Os testes cobrem:

- resposta da página de login;
- redirecionamento de rota protegida sem autenticação;
- falha de login inválido;
- proteção de rota principal de tarefa.

Para rodar um teste mais verboso localmente:

```powershell
pytest -v
```

## Pipeline GitHub Actions

O projeto utiliza GitHub Actions com o workflow em [.github/workflows/ci.yml](/C:/Users/Ryzen/Task-Manager-using-Flask/.github/workflows/ci.yml).

O workflow executa em `push` e `pull_request` nas branches:

- `main`
- `develop`
- `staging`
- `production`

Jobs configurados:

- `test`: usa `ubuntu-latest`, faz checkout do código, configura Python 3.11, atualiza o `pip`, instala `requirements.txt` e executa `pytest`.
- `sast_bandit`: depende de `test`, executa SAST com Bandit e publica relatórios JSON e HTML como artifacts.
- `dependency_check`: depende de `test`, executa análise de dependências com OWASP Dependency-Check e publica relatório HTML como artifact.
- `build`: depende de `test`, `sast_bandit` e `dependency_check`, faz checkout do código e executa `docker build -t task-manager-flask:latest .`.

Como é um fluxo acadêmico, as etapas de segurança priorizam a geração de relatórios para análise posterior no GitHub Actions.

O antigo pipeline GitLab (`.gitlab-ci.yml`) foi removido para evitar ambiguidade, já que a entrega será feita com GitHub Actions.

## Branches e versionamento

Criação das branches dedicadas:

```powershell
git checkout -b develop
git push -u origin develop

git checkout -b staging
git push -u origin staging

git checkout -b production
git push -u origin production
```

Criação de tag de versão:

```powershell
git tag -a v1.0.0 -m "Release v1.0.0"
git push origin v1.0.0
```

Fluxo básico para registrar alterações:

```powershell
git add .
git commit -m "Configura pipeline inicial com GitHub Actions"
git push origin <nome-da-branch>
```

## Preparação para DevSecOps

Análise estática de segurança:

```powershell
bandit -r .
```

Para instalar e rodar o Bandit localmente:

```powershell
pip install bandit
bandit -r . -f json -o bandit-report.json
bandit -r . -f html -o bandit-report.html
```

Análise de dependências local via Docker:

```powershell
docker run --rm -v "${PWD}:/src" -v "${PWD}/dependency-check-report:/report" owasp/dependency-check --scan /src --format HTML --out /report
```

No GitHub Actions, os relatórios de Bandit e OWASP Dependency-Check ficam disponíveis como artifacts da execução do workflow.

Dependências:

- `requirements.txt` está versionado para instalação reproduzível com `pip install -r requirements.txt`.
- O projeto pode ser submetido ao OWASP Dependency-Check apontando para a raiz do repositório.

## Funcionalidades principais

- login e logout;
- cadastro de usuários;
- criação, listagem, edição e exclusão de tarefas;
- pesquisa de tarefas por palavra-chave no conteúdo.
