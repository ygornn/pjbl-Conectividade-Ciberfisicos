# SmartRooms

**Sistema de monitoramento da disponibilidade de salas de estudo da Biblioteca Central da PUCPR, desenvolvido com Python, MQTT, Flask, SQLite e Docker.**

## 1. Sobre o projeto

O SmartRooms é uma aplicação que simula sensores IoT instalados em três salas de estudo. Os sensores virtuais geram medições de temperatura e ocupação e publicam esses dados periodicamente por MQTT.

Um servidor Python recebe as mensagens, valida os dados e registra as medições em um banco SQLite. O mesmo servidor disponibiliza uma API HTTP e serve um dashboard web que apresenta o estado das salas.

### Dados monitorados atualmente

- **Temperatura:** valor simulado em graus Celsius.
- **Ocupação:** valor binário (`0` = sala disponível; `1` = sala ocupada).
- **Horário da medição:** timestamp Unix gerado pelo servidor ao receber a mensagem.

> **Escopo da implementação atual:** o simulador não coleta um número real de pessoas, umidade ou ruído. Esses dados não fazem parte do payload implementado neste repositório.

## 2. Arquitetura

O Docker Compose inicia três serviços:

| Serviço | Responsabilidade |
|---|---|
| `mosquitto` | Broker MQTT que recebe e distribui as mensagens dos sensores. |
| `sensors` | Simulador Python que publica medições das três salas. |
| `server` | Cliente MQTT, validação e persistência SQLite, API Flask e servidor do dashboard. |

### Fluxo de dados

1. O simulador gera temperatura e ocupação para `room_A`, `room_B` e `room_C`.
2. A cada três segundos, publica uma mensagem MQTT por sala.
3. O Mosquitto recebe as mensagens no tópico `pjbl/{room}/environment`.
4. O servidor assina `pjbl/+/environment`, valida o payload e grava a medição no SQLite.
5. O dashboard consulta a API Flask e atualiza os indicadores e cartões das salas a cada cinco segundos.

### Tecnologias

- Python 3.13.3 nas imagens dos serviços Python.
- Docker e Docker Compose.
- Eclipse Mosquitto 2 (broker MQTT).
- Paho-MQTT (publicação e assinatura MQTT).
- Flask (API HTTP e entrega do dashboard).
- SQLite (persistência das medições).
- HTML, CSS e JavaScript (interface web).

## 3. Estrutura do repositório

```text
pjbl/
├── docker-compose.yml
├── README.md
├── broker/
│   └── mosquitto.conf
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

O arquivo `dashboard/requeriments.txt` está presente no repositório, mas não é usado pelo Dockerfile atual. As dependências do serviço Flask são instaladas a partir de `server/requirements.txt`.

## 4. Pré-requisitos

- Linux Debian (ou outra distribuição compatível), Windows ou macOS.
- Docker Engine ou Docker Desktop.
- Plugin Docker Compose (`docker compose`).

Verifique a instalação:

```bash
docker --version
docker compose version
```

Não é necessário instalar Python, Flask, Paho-MQTT ou SQLite diretamente no host para executar a versão em containers.

## 5. Configuração e portas

A configuração atual do Compose utiliza:

| Serviço/uso | Porta | Acesso |
|---|---:|---|
| Mosquitto MQTT | `1883/TCP` | Interno à rede Docker; não publicada no host. |
| Flask e dashboard | `8000` no container | Publicada como `8001` no host (`8001:8000`). |

**Atenção:** o endereço no navegador usa a porta **8001**, não 8000, conforme o `docker-compose.yml` deste repositório.

A rede Docker bridge é chamada `smartrooms-net`. Os containers usam o nome do serviço `mosquitto` para encontrar o broker. O servidor recebe as variáveis:

- `MQTT_HOST=mosquitto`
- `DATABASE_PATH=/data/smartrooms.db`
- `PYTHONUNBUFFERED=1`

O Mosquitto está configurado atualmente com `allow_anonymous true`. Portanto, a configuração incluída não exige usuário e senha MQTT; ela é apropriada para um ambiente demonstrativo isolado, não para exposição pública.

## 6. Construção e inicialização

Execute os comandos a partir da pasta que contém `docker-compose.yml`.

### 6.1. Entrar na pasta do projeto

```bash
cd pjbl
```

### 6.2. Construir as imagens

```bash
docker compose build
```

O Compose constrói as imagens dos serviços `sensors` e `server` e obtém a imagem `eclipse-mosquitto:2` para o broker.

### 6.3. Iniciar os serviços

```bash
docker compose up -d
```

### 6.4. Conferir o estado dos containers

```bash
docker compose ps
```

Os três serviços devem aparecer em execução. O serviço `server` deve publicar a porta do host `8001` para a porta `8000` do container.

### 6.5. Acompanhar os logs

```bash
docker compose logs -f
```

Para acompanhar apenas um serviço:

```bash
docker compose logs -f sensors
docker compose logs -f mosquitto
docker compose logs -f server
```

No servidor, mensagens esperadas incluem a inicialização do banco, a conexão com o broker e a assinatura do tópico `pjbl/+/environment`. O simulador imprime as medições geradas para cada sala.

Para interromper a visualização contínua dos logs, pressione `Ctrl+C`. Isso encerra o acompanhamento, não os containers.

## 7. Acessar o dashboard e a API

### Dashboard

Com os containers em execução, abra no navegador:

**http://localhost:8001/dashboard**

O dashboard apresenta:
- quantidade de salas disponíveis;
- quantidade de salas ocupadas;
- quantidade de salas sem dados atuais;
- cartões das três salas com estado e temperatura;
- horário da última atualização da interface.

O JavaScript consulta a API a cada cinco segundos. Se os dados de uma sala tiverem mais de 60 segundos, o servidor a considera sem conexão atual e o dashboard mostra o estado correspondente.

Para acessar a partir de outro computador na mesma rede, use o endereço IP do host Debian:

```text
http://IP_DO_DEBIAN:8001/dashboard
```

Descubra o IP com:

```bash
hostname -I
```

Se o acesso remoto não funcionar, verifique o mapeamento de portas do Docker e as regras do firewall do host. A aplicação precisa estar em execução e a porta TCP 8001 deve estar liberada para a rede autorizada.

### API

O servidor também disponibiliza os seguintes endpoints:

| Método | Endpoint | Descrição |
|---|---|---|
| `GET` | `/` | Retorna um JSON informando que a API está operacional. |
| `GET` | `/api/rooms` | Retorna o estado e a última medição de cada sala. |
| `GET` | `/api/rooms/room_A` | Retorna os dados da sala indicada. |
| `GET` | `/api/metrics` | Retorna os totais de salas disponíveis, ocupadas, conectadas e sem dados atuais. |

Exemplos de URLs locais:

```text
http://localhost:8001/
http://localhost:8001/api/rooms
http://localhost:8001/api/rooms/room_A
http://localhost:8001/api/metrics
```

A rota `/` retorna JSON; para abrir a interface gráfica, use `/dashboard`.

## 8. MQTT e formato das mensagens

O simulador publica nos tópicos:

```text
pjbl/room_A/environment
pjbl/room_B/environment
pjbl/room_C/environment
```

O servidor assina o filtro:

```text
pjbl/+/environment
```

Exemplo de payload publicado pelo simulador:

```json
{
  "temperature": 24.5,
  "occupancy": 1,
  "timestamp": 1795350000.0
}
```

Os valores de temperatura e ocupação são gerados aleatoriamente pelo simulador. Embora o simulador envie um timestamp, o servidor substitui esse campo pelo horário de recebimento antes de salvar a medição.

## 9. Banco de dados e persistência

O banco SQLite é criado em:

```text
/data/smartrooms.db
```

Dentro do container `server`, esse caminho está associado ao volume nomeado `smartrooms_data`. Assim, os registros permanecem armazenados quando os containers são parados ou recriados, desde que o volume não seja removido.

A tabela atual `measurements` contém:

| Coluna | Finalidade |
|---|---|
| `id` | Identificador incremental da medição. |
| `room` | Identificador da sala (`room_A`, `room_B` ou `room_C`). |
| `temperature` | Temperatura registrada. |
| `occupancy` | Estado de ocupação (0 ou 1). |
| `timestamp` | Timestamp Unix atribuído pelo servidor. |

### Verificar se o banco foi criado

```bash
docker compose exec server ls -l /data
```

### Consultar as últimas medições

```bash
docker compose exec server python -c "import sqlite3; c=sqlite3.connect('/data/smartrooms.db'); print(*c.execute('SELECT id, room, temperature, occupancy, timestamp FROM measurements ORDER BY id DESC LIMIT 10').fetchall(), sep='\n'); c.close()"
```

## 10. Gerenciamento dos serviços

| Ação | Comando |
|---|---|
| Ver containers | `docker compose ps` |
| Ver logs de todos os serviços | `docker compose logs` |
| Acompanhar logs do servidor | `docker compose logs -f server` |
| Reiniciar os serviços | `docker compose restart` |
| Parar os serviços | `docker compose stop` |
| Parar e remover containers/rede | `docker compose down` |
| Reconstruir e iniciar | `docker compose up --build -d` |

`docker compose down` preserva os volumes nomeados por padrão. Para remover também os volumes:

```bash
docker compose down -v
```

> **Atenção:** `docker compose down -v` apaga o volume `smartrooms_data` e, consequentemente, o banco SQLite persistido. Use somente se puder descartar os dados.

## 11. Solução de problemas

### O dashboard não abre

1. Confira os containers com `docker compose ps`.
2. Confira os logs com `docker compose logs --tail=100 server`.
3. Confirme que a porta publicada aparece como `0.0.0.0:8001->8000/tcp` (ou mapeamento equivalente).
4. Acesse `http://localhost:8001/dashboard`. A rota `/` é apenas o endpoint JSON de status.

### Não consigo conectar em `localhost:8001`

Verifique o mapeamento no `docker-compose.yml`:

```yaml
ports:
  - "8001:8000"
```

Teste no próprio host:

```bash
curl -i http://localhost:8001/
curl -i http://localhost:8001/dashboard
```

Se funcionar localmente, mas não a partir de outro computador, verifique o firewall e a conectividade da rede local. No Debian, UFW é apenas uma das opções de firewall; não é um requisito para executar o projeto.

### O servidor não recebe mensagens MQTT

- Confira se `mosquitto` está ativo: `docker compose ps`.
- Confira se `MQTT_HOST` no serviço `server` está definido como `mosquitto`.
- Confira se sensores e servidor usam o mesmo padrão de tópico: `pjbl/{room}/environment`.
- Consulte os logs: `docker compose logs -f mosquitto sensors server`.

### O banco não recebe medições

- Confira os logs do servidor e procure mensagens `Measurement saved`.
- Verifique se o arquivo `/data/smartrooms.db` existe no container.
- Confira se o serviço `server` está montando o volume `smartrooms_data:/data`.

### Reconstruir após alterar o código

```bash
docker compose up --build -d
```

## 12. Limitações da versão atual

A documentação descreve o código presente neste repositório. Na versão atual:

- Os sensores são simulados por software; não há hardware físico conectado.
- São gerados apenas temperatura e ocupação binária.
- O dashboard apresenta indicadores e cartões de sala; não há gráficos históricos ou mapa interativo implementados.
- O estado da sala é classificado como disponível quando `occupancy` é `0`, ocupada quando é maior que `0` e sem dados atuais quando não há medição recente.
- O broker permite conexões anônimas na configuração fornecida.
- O banco armazena medições históricas, mas a interface exibe apenas a medição mais recente de cada sala.

Essas funcionalidades podem ser ampliadas em versões futuras, mas não são apresentadas aqui como recursos já implementados.
