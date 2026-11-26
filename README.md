# SmartRooms

**Sistema IoT para monitoramento da disponibilidade e das condições de salas de estudo.**

O SmartRooms é um projeto acadêmico de Internet das Coisas (IoT) que simula sensores em salas de estudo, transmite as leituras por MQTT, processa os dados em uma aplicação Flask, armazena as medições em SQLite e disponibiliza as informações em um dashboard web.

> **Estado da implementação:** esta documentação descreve a arquitetura e os recursos identificados no projeto. A autenticação MQTT é apresentada como configuração protegida a ser aplicada ao `docker-compose.yml`, ao `mosquitto.conf` e aos dois clientes Python. Confirme que essas alterações também estão presentes nos arquivos locais antes de iniciar o sistema.

## Sumário

- [1. Objetivo](#1-objetivo)
- [2. Arquitetura](#2-arquitetura)
- [3. Tecnologias](#3-tecnologias)
- [4. Estrutura do projeto](#4-estrutura-do-projeto)
- [5. Pré-requisitos](#5-pré-requisitos)
- [6. Configuração](#6-configuração)
- [7. Inicialização](#7-inicialização)
- [8. Dashboard e API](#8-dashboard-e-api)
- [9. Comunicação MQTT](#9-comunicação-mqtt)
- [10. Banco de dados SQLite](#10-banco-de-dados-sqlite)
- [11. Concorrência](#11-concorrência)
- [12. Comandos úteis](#12-comandos-úteis)
- [13. Solução de problemas](#13-solução-de-problemas)
- [14. Segurança e limitações](#14-segurança-e-limitações)

## 1. Objetivo

Em bibliotecas, laboratórios e espaços compartilhados, pode ser difícil descobrir quais salas estão livres sem verificar cada ambiente presencialmente. O SmartRooms propõe centralizar essas informações em uma interface web.

Na versão atual, o simulador gera dados para três salas:

- `room_A`
- `room_B`
- `room_C`

Cada sala recebe leituras de temperatura e ocupação. O sistema classifica a sala com base na última leitura válida:

| Condição | Estado retornado |
|---|---|
| Leitura recente e ocupação igual a `0` | `available` |
| Leitura recente e ocupação maior que `0` | `occupied` |
| Sem leitura ou leitura com mais de 60 segundos | `unknown` |

Os dados são simulados por software. Não há sensores físicos obrigatórios para executar esta versão.

## 2. Arquitetura

O projeto é composto por três serviços Docker conectados por uma rede bridge criada pelo Docker Compose.

```text
                 HOST / COMPUTADOR
                        |
                  Docker Compose
                        |
              Rede Docker: smartrooms-net
                        |
        +---------------+----------------+
        |               |                |
        v               v                v
   +----------+    +-----------+    +-----------+
   | Sensors  |--->| Mosquitto |<---|  Server   |
   | Python   |MQTT| Broker    |MQTT| Flask     |
   +----------+    +-----------+    +-----+-----+
                                          |
                                     +----+----+
                                     | SQLite  |
                                     | /data   |
                                     +---------+
                                          |
                                      HTTP :8000
                                          |
                                    Host :8001
                                          |
                                      Navegador
```

### Serviços

1. **Mosquitto:** broker MQTT. Recebe as mensagens dos sensores e as disponibiliza aos clientes inscritos.
2. **Sensors:** simulador Python que gera temperatura e ocupação e publica as mensagens MQTT.
3. **Server:** aplicação Python/Flask que assina o tópico MQTT, valida e armazena as medições no SQLite e disponibiliza API e dashboard.

### Fluxo de dados

1. O simulador gera uma medição para cada sala.
2. Publica a medição no tópico MQTT correspondente.
3. O Mosquitto recebe a publicação e a encaminha ao servidor inscrito.
4. O servidor valida o tópico e o conteúdo JSON, atribui o horário de recebimento e grava a medição no SQLite.
5. O navegador consulta a API HTTP e atualiza o dashboard.

## 3. Tecnologias

| Tecnologia | Função |
|---|---|
| Python 3.13 | Implementação do simulador e do servidor |
| Docker / Docker Compose | Empacotamento e execução dos serviços |
| Eclipse Mosquitto 2 | Broker MQTT |
| Paho-MQTT | Cliente Python para publicar e receber mensagens MQTT |
| Flask | API HTTP e entrega da página do dashboard |
| SQLite | Persistência das medições |
| HTML, CSS e JavaScript | Interface web |

## 4. Estrutura do projeto

```text
pjbl/
├── docker-compose.yml
├── .env                  # Criado localmente; não versionar
├── .gitignore
├── broker/
│   ├── mosquitto.conf
│   └── passwordfile      # Criado localmente; não versionar
├── sensors/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── simulator.py
├── server/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py
│   └── database.py
└── dashboard/
    ├── templates/
    │   └── index.html
    ├── static/
    │   ├── dashboard.js
    │   └── style.css
    └── requeriments.txt
```

As dependências do serviço Flask são instaladas a partir de `server/requirements.txt`; as dependências do simulador, de `sensors/requirements.txt`. O arquivo `dashboard/requeriments.txt`, se mantido no repositório, não é utilizado pelo Dockerfile atual.

## 5. Pré-requisitos

- Docker Engine ou Docker Desktop.
- Docker Compose (comando `docker compose`).
- Terminal com acesso à pasta do projeto.

Verifique a instalação:

```bash
docker --version
docker compose version
```

Não é necessário instalar Python, Flask, Paho-MQTT ou SQLite diretamente no computador hospedeiro para executar os serviços em containers.

## 6. Configuração

Execute os comandos a seguir na pasta que contém `docker-compose.yml`.

### 6.1. Variáveis de ambiente

Crie um arquivo `.env` ao lado do `docker-compose.yml`:

```env
MQTT_USER=smartrooms
MQTT_PASSWORD=SUBSTITUA_POR_UMA_SENHA_FORTE
```

Use uma senha forte e não a compartilhe. Adicione ao `.gitignore`:

```gitignore
.env
broker/passwordfile
```

### 6.2. Criar o arquivo de senhas do Mosquitto

Crie o arquivo `broker/passwordfile` com o utilitário `mosquitto_passwd`:

```bash
docker run --rm -it \
  -v "$PWD/broker:/mosquitto/config" \
  eclipse-mosquitto:2 \
  mosquitto_passwd -c /mosquitto/config/passwordfile smartrooms
```

O comando solicitará a senha. Informe a mesma senha definida em `.env`.

O processo Mosquitto precisa conseguir ler o arquivo. Em ambientes Linux nos quais o processo usa UID/GID 1883, pode ser necessário:

```bash
sudo chown 1883:1883 broker/passwordfile
sudo chmod 600 broker/passwordfile
```

Se a imagem ou a distribuição usar outro UID/GID, verifique antes com:

```bash
docker run --rm eclipse-mosquitto:2 id mosquitto
```

### 6.3. Configurar o broker

O arquivo `broker/mosquitto.conf` deve conter:

```conf
listener 1883
allow_anonymous false
password_file /mosquitto/config/passwordfile
persistence true
persistence_location /mosquitto/data/
```

No serviço `mosquitto` do `docker-compose.yml`, monte o arquivo de senhas:

```yaml
volumes:
  - ./broker/mosquitto.conf:/mosquitto/config/mosquitto.conf
  - ./broker/passwordfile:/mosquitto/config/passwordfile
  - mqtt_data:/mosquitto/data
```

### 6.4. Passar as credenciais aos clientes

Nos serviços `sensors` e `server` do `docker-compose.yml`, inclua as variáveis de ambiente:

```yaml
environment:
  MQTT_HOST: mosquitto
  MQTT_USER: ${MQTT_USER}
  MQTT_PASSWORD: ${MQTT_PASSWORD}
```

Preserve as demais variáveis do serviço `server`, como:

```yaml
DATABASE_PATH: /data/smartrooms.db
PYTHONUNBUFFERED: 1
```

O serviço `server` também deve manter o mapeamento de porta e o volume:

```yaml
ports:
  - "8001:8000"
volumes:
  - smartspace_data:/data
```

### 6.5. Configurar autenticação nos clientes Python

Nos arquivos `sensors/simulator.py` e `server/main.py`, antes de `client.connect(...)`, configure as credenciais:

```python
username = os.getenv("MQTT_USER")
password = os.getenv("MQTT_PASSWORD")

if not username or not password:
    raise RuntimeError("MQTT_USER e MQTT_PASSWORD devem estar configurados")

client.username_pw_set(username, password)
```

O simulador e o servidor já utilizam `os`; confirme que `import os` está presente no início de cada arquivo. Não imprima a senha nos logs.

### 6.6. Verificar a configuração de autenticação

Depois de salvar as alterações, reconstrua e recrie os serviços:

```bash
docker compose up -d --build --force-recreate
```

Verifique se os containers estão ativos:

```bash
docker compose ps
```

Para conferir se as variáveis chegaram aos serviços sem revelar a senha:

```bash
docker compose exec sensors python -c \
"import os; print('HOST:', os.getenv('MQTT_HOST')); print('USER:', os.getenv('MQTT_USER')); print('PASSWORD CONFIGURADA:', bool(os.getenv('MQTT_PASSWORD')))"
```

```bash
docker compose exec server python -c \
"import os; print('HOST:', os.getenv('MQTT_HOST')); print('USER:', os.getenv('MQTT_USER')); print('PASSWORD CONFIGURADA:', bool(os.getenv('MQTT_PASSWORD')))"
```

Resultado esperado nos dois serviços:

```text
HOST: mosquitto
USER: smartrooms
PASSWORD CONFIGURADA: True
```

Isso confirma que as variáveis foram carregadas. A autenticação efetiva deve ser confirmada também pelos logs do broker.

## 7. Inicialização

Com a configuração concluída, construa e inicie os serviços:

```bash
docker compose up -d --build
```

Confira o estado:

```bash
docker compose ps
```

Acompanhe os logs:

```bash
docker compose logs -f mosquitto
docker compose logs -f sensors
docker compose logs -f server
```

Para acompanhar todos de uma vez:

```bash
docker compose logs -f
```

Para sair da visualização dos logs, pressione `Ctrl+C`. Isso interrompe apenas o acompanhamento, não os containers.

### Logs esperados

No broker, após autenticação bem-sucedida, devem aparecer conexões dos clientes, com os respectivos identificadores e usuário MQTT, por exemplo:

```text
New client connected ... as smartspace_sensors ... u'smartrooms'.
New client connected ... as smartspace_server ... u'smartrooms'.
```

No servidor, mensagens esperadas incluem:

```text
Connected to MQTT broker!
Subscribed to pjbl/+/environment
Measurement saved: room_A | Temperature: ... | Occupancy: ...
```

Uma mensagem `not authorised` indica que o broker rejeitou uma tentativa por credenciais ausentes/incorretas ou por configuração de autorização. Verifique também se uma tentativa posterior foi bem-sucedida.

## 8. Dashboard e API

Com os containers em execução, abra:

**Dashboard:** <http://localhost:8001/dashboard>

O dashboard apresenta as informações das três salas e consulta a API periodicamente para atualizar os dados.

### Endpoints disponíveis

| Método | Endpoint | Descrição |
|---|---|---|
| `GET` | `/` | Estado geral da API em JSON |
| `GET` | `/api/rooms` | Estado e última medição de todas as salas |
| `GET` | `/api/rooms/room_A` | Dados da sala especificada |
| `GET` | `/api/metrics` | Indicadores agregados das salas |
| `GET` | `/dashboard` | Interface web |

Exemplos:

```bash
curl http://localhost:8001/
curl http://localhost:8001/api/rooms
curl http://localhost:8001/api/rooms/room_A
curl http://localhost:8001/api/metrics
```

O mapeamento `8001:8000` significa que a porta 8001 do host encaminha as requisições para a porta 8000 do container Flask. Entre containers, o broker é acessado pelo hostname `mosquitto` na porta 1883.

Para acesso a partir de outro computador na mesma rede, use o IP do computador hospedeiro:

```text
http://IP_DO_HOST:8001/dashboard
```

O firewall do host deve permitir o acesso à porta TCP 8001 para a rede desejada.

## 9. Comunicação MQTT

### Tópicos

O simulador publica nos seguintes tópicos:

```text
pjbl/room_A/environment
pjbl/room_B/environment
pjbl/room_C/environment
```

O servidor assina o filtro:

```text
pjbl/+/environment
```

O caractere `+` representa um único nível do tópico e permite receber mensagens de qualquer uma das salas nesse padrão.

### Formato da mensagem

Exemplo de payload JSON:

```json
{
  "temperature": 24.5,
  "occupancy": 1,
  "timestamp": 1795350000.0
}
```

- `temperature`: temperatura simulada em graus Celsius.
- `occupancy`: quantidade simulada de ocupantes (na versão atual, `0` ou `1`).
- `timestamp`: instante Unix enviado pelo simulador.

O servidor valida a sala e os campos numéricos. Em seguida, substitui o timestamp recebido pelo horário de recebimento da mensagem e grava a medição no banco.

O simulador gera valores de temperatura entre 20 °C e 30 °C e publica as leituras aproximadamente a cada três segundos.

## 10. Banco de dados SQLite

O banco é armazenado no caminho:

```text
/data/smartrooms.db
```

No Compose, o diretório `/data` do container `server` é persistido no volume nomeado `smartspace_data`. Assim, os registros permanecem após parar ou recriar os containers, desde que o volume não seja removido.

### Estrutura da tabela `measurements`

| Coluna | Descrição |
|---|---|
| `id` | Identificador incremental |
| `room` | Nome da sala |
| `temperature` | Temperatura medida |
| `occupancy` | Ocupação registrada |
| `timestamp` | Horário Unix atribuído pelo servidor |

### Consultar a quantidade de registros

```bash
docker compose exec server python -c \
"import sqlite3; c=sqlite3.connect('/data/smartrooms.db'); print('Total:', c.execute('SELECT COUNT(*) FROM measurements').fetchone()[0]); c.close()"
```

### Consultar as últimas dez medições

```bash
docker compose exec server python -c \
"import sqlite3; c=sqlite3.connect('/data/smartrooms.db'); print(*c.execute('SELECT id, room, temperature, occupancy, timestamp FROM measurements ORDER BY id DESC LIMIT 10').fetchall(), sep='\n'); c.close()"
```

### Contar registros por sala

```bash
docker compose exec server python -c \
"import sqlite3; c=sqlite3.connect('/data/smartrooms.db'); print(*c.execute('SELECT room, COUNT(*) FROM measurements GROUP BY room').fetchall(), sep='\n'); c.close()"
```

### Verificar persistência

1. Consulte a quantidade de registros.
2. Reinicie o servidor com `docker compose restart server`.
3. Consulte novamente a quantidade e as últimas medições.
4. Confirme que os dados anteriores continuam presentes e que novos registros voltam a ser inseridos.

> **Atenção:** `docker compose down -v` remove os volumes nomeados e apaga o banco persistido. Não use esse comando se precisar preservar as medições.

## 11. Concorrência

O projeto possui concorrência em diferentes partes da execução:

- O método `client.loop_start()` da biblioteca Paho-MQTT inicia uma thread em segundo plano para processar a comunicação MQTT.
- Enquanto essa thread trata as mensagens e executa o callback `on_message`, o processo Flask permanece disponível para atender requisições HTTP.
- O servidor de desenvolvimento Flask/Werkzeug utilizado por `app.run()` atende requisições em modo threaded por padrão na configuração usual.

O uso de threads permite que operações HTTP e MQTT progridam em períodos sobrepostos. Isso demonstra concorrência, mas não significa necessariamente execução paralela em múltiplos núcleos de CPU.

### Teste com várias requisições HTTP

Com os serviços ativos, execute no host:

```bash
for i in {1..20}; do
  curl -s http://localhost:8001/api/rooms > /dev/null &
done
wait
```

O comando inicia 20 requisições em segundo plano. Enquanto ele executa, acompanhe em outros terminais:

```bash
docker compose logs -f sensors
```

```bash
docker compose logs -f server
```

Verifique se as mensagens dos sensores continuam sendo recebidas e armazenadas durante as requisições HTTP.

### Teste com ThreadPoolExecutor

Opcionalmente, crie `test_concurrency.py` no host:

```python
import time
import requests
from concurrent.futures import ThreadPoolExecutor

URL = "http://localhost:8001/api/rooms"

def request_server(number):
    start = time.perf_counter()
    response = requests.get(URL, timeout=10)

    return {
        "request": number,
        "status": response.status_code,
        "elapsed_seconds": round(time.perf_counter() - start, 3)
    }

start = time.perf_counter()

with ThreadPoolExecutor(max_workers=10) as executor:
    results = list(executor.map(request_server, range(20)))

for result in results:
    print(result)

print("Total seconds:", round(time.perf_counter() - start, 3))
```

Instale a dependência no host, se necessário, e execute:

```bash
python -m pip install requests
python test_concurrency.py
```

Esse teste cria até dez requisições concorrentes por vez. Para a demonstração, mantenha os logs dos sensores e do servidor visíveis durante a execução.

**Interpretação:** o teste demonstra requisições HTTP concorrentes e a continuidade do fluxo MQTT observada nos logs. Ele não é, isoladamente, um benchmark de capacidade ou prova de paralelismo em múltiplos núcleos.

## 12. Comandos úteis

| Ação | Comando |
|---|---|
| Construir e iniciar | `docker compose up -d --build` |
| Recriar serviços após alterar variáveis | `docker compose up -d --force-recreate` |
| Ver estado dos serviços | `docker compose ps -a` |
| Ver logs de todos | `docker compose logs` |
| Acompanhar logs de um serviço | `docker compose logs -f server` |
| Reiniciar o servidor | `docker compose restart server` |
| Parar os serviços | `docker compose stop` |
| Parar e remover containers/rede | `docker compose down` |
| Entrar no container do servidor | `docker compose exec server sh` |
| Ver logs pelo nome do container | `docker logs smartrooms-broker` |

**Nome do serviço e nome do container são diferentes:**

| Uso | Nome |
|---|---|
| Serviço no Compose | `mosquitto` |
| Container Mosquitto | `smartrooms-broker` |
| Hostname MQTT dentro da rede Docker | `mosquitto` |
| Container dos sensores | `smartrooms-sensors` |
| Container do servidor | `smartrooms-server` |

Por exemplo, use `docker compose logs mosquitto` para consultar o serviço e `docker logs smartrooms-broker` para consultar o container pelo nome.

## 13. Solução de problemas

### 14.1. `No such container: mosquitto`

`mosquitto` é o nome do serviço Compose, não o nome explícito do container. Use:

```bash
docker compose logs mosquitto
```

Ou, pelo nome do container:

```bash
docker logs smartrooms-broker
```

### 14.2. `not authorised` nos logs do Mosquitto

Verifique:

1. Se `.env` está ao lado do `docker-compose.yml`.
2. Se `MQTT_USER` e `MQTT_PASSWORD` são passados aos serviços `sensors` e `server`.
3. Se ambos os clientes executam `client.username_pw_set(...)` antes de `connect()`.
4. Se a senha usada para gerar `passwordfile` é a mesma do `.env`.
5. Se `passwordfile` está montado no caminho correto e pode ser lido pelo Mosquitto.
6. Se `allow_anonymous false` está ativo.

Consulte:

```bash
docker compose logs --tail=100 mosquitto sensors server
```

### 14.3. `password-file: Unable to open pwfile`

Confira se o arquivo existe:

```bash
ls -l broker/passwordfile
```

Confira se o volume está configurado no serviço `mosquitto` e se as permissões permitem que o usuário do broker leia o arquivo.

### 14.4. `attempt to write a readonly database`

O processo do servidor precisa ter permissão de escrita no arquivo SQLite e no diretório `/data`. O SQLite pode criar arquivos auxiliares no mesmo diretório, portanto não basta tornar apenas o arquivo `.db` gravável.

Verifique o usuário do processo e as permissões:

```bash
docker compose exec server sh -c 'id && ls -ld /data && ls -l /data'
```

Se a imagem executar a aplicação com UID 10001, por exemplo, e o volume estiver pertencendo a `root`, ajuste a propriedade sem remover o volume:

```bash
docker compose run --rm --user root --entrypoint sh server \
  -c "chown -R 10001:10001 /data && chmod -R u+rwX /data"
```

Use o UID/GID correspondente ao usuário configurado no Dockerfile real. Não execute `docker compose down -v` para tentar corrigir permissões: isso apagaria os dados persistidos.

### 14.5. `address already in use` na porta 8001

Verifique quem está utilizando a porta:

```bash
sudo ss -ltnp | grep :8001
docker ps
```

Se necessário, encerre o serviço antigo que ocupa a porta ou altere o mapeamento no Compose, por exemplo:

```yaml
ports:
  - "8002:8000"
```

Nesse caso, o dashboard passa a ser acessado em `http://localhost:8002/dashboard`.

### 14.6. Serviço `sensors` ou `server` não está em execução

`docker compose exec` só funciona em containers ativos. Verifique:

```bash
docker compose ps -a
docker compose logs --tail=100 sensors
docker compose logs --tail=100 server
```

Para executar um diagnóstico sem iniciar o comando principal do serviço, use `docker compose run --rm --no-deps` com um `--entrypoint` apropriado.

### 14.7. Dashboard não abre

Verifique:

```bash
docker compose ps
curl -i http://localhost:8001/
curl -i http://localhost:8001/dashboard
```

Confirme o mapeamento `8001:8000`, os logs do Flask e as regras de firewall do host. A rota `/` retorna JSON; a interface gráfica fica em `/dashboard`.

## 14. Segurança e limitações

### Segurança

- Não versione `.env` nem `broker/passwordfile`.
- Não compartilhe credenciais em logs, capturas de tela ou documentação pública.
- Mantenha a porta MQTT 1883 apenas na rede interna Docker, se não houver necessidade de acesso externo.
- A autenticação MQTT sem TLS não criptografa o conteúdo transmitido. Em redes não confiáveis, configure TLS.
- Use usuário não privilegiado nos containers sempre que possível e conceda apenas as permissões necessárias aos diretórios da aplicação e do banco.
- O servidor Flask integrado é apropriado para desenvolvimento e demonstração. Para implantação de produção, utilize um servidor WSGI apropriado.

### Limitações da versão atual

- Os sensores são simulados por software; não há hardware físico conectado.
- São geradas leituras de temperatura e ocupação para três salas.
- O simulador utiliza valores aleatórios, portanto não representa medições ambientais reais.
- O estado de disponibilidade depende da última leitura e de um limite de atualidade de 60 segundos.
- O SQLite atende ao escopo demonstrativo; sua capacidade de escrita é serializada e pode exigir ajustes para cargas maiores.
- O teste de concorrência descrito demonstra sobreposição de tarefas em uma carga pequena, não estabelece limites máximos de desempenho.
- A autenticação depende de aplicar as configurações descritas na seção 6 a todos os componentes locais.

### Possíveis evoluções

- Substituir sensores virtuais por dispositivos físicos.
- Adicionar umidade, luminosidade e qualidade do ar.
- Implementar gráficos históricos e relatórios.
- Adicionar TLS à comunicação MQTT.
- Adotar servidor WSGI de produção.
- Avaliar um banco de dados mais adequado caso o volume de escrita cresça.

---

**SmartRooms — Monitoramento inteligente de salas de estudo.**
