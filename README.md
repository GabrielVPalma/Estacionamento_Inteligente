# EstacionaAI — Estacionamento Inteligente

Sistema de estacionamento inteligente desenvolvido como projeto acadêmico de Engenharia de Computação. O projeto utiliza uma **ESP32-CAM**, processamento digital de imagens com **OpenCV** e uma API desenvolvida em **Python e Flask** para identificar automaticamente a ocupação de vagas em uma maquete.

## Sobre o projeto

O EstacionaAI tem como objetivo monitorar a disponibilidade de vagas em um estacionamento por meio de uma câmera posicionada sobre a maquete.

A ESP32-CAM captura imagens do estacionamento e as disponibiliza pela rede Wi-Fi. O backend, desenvolvido em Python, recebe essas imagens e utiliza técnicas de processamento de imagens para analisar a tonalidade das regiões previamente calibradas.

Com base na análise, o sistema identifica quais vagas estão ocupadas e disponibiliza os resultados por meio de uma API REST, consumida pelo frontend.

## Funcionalidades

- Captura de imagens utilizando ESP32-CAM.
- Comunicação entre a câmera e o computador por Wi-Fi.
- Calibração das dez vagas por seleção de regiões na imagem.
- Reconhecimento de ocupação por análise de cores no espaço HSV.
- Identificação individual das vagas de A1 a A10.
- API REST para disponibilização dos estados das vagas.
- Interface gráfica com atualização periódica dos dados.
- Contabilização de vagas livres e ocupadas.

## Arquitetura do sistema

O projeto é dividido em três componentes principais:

**1. ESP32-CAM — Aquisição de imagens**

Responsável por capturar imagens da maquete e disponibilizá-las por meio de um servidor HTTP local, utilizando a rota `/capture`.

**2. Backend — Processamento e API**

Desenvolvido em Python, utiliza OpenCV e NumPy para analisar as imagens recebidas.

O processamento utiliza o espaço de cores HSV, considerando principalmente o canal de saturação (S), para identificar pixels com tonalidades vibrantes nas regiões correspondentes às vagas.

O Flask disponibiliza os resultados por meio de uma API HTTP.

**3. Frontend — Interface de monitoramento**

Desenvolvido com HTML, CSS e JavaScript, apresenta a disposição das dez vagas, indicando visualmente quais estão livres e quais estão ocupadas.

A interface consulta periodicamente a API para atualizar as informações.

## Tecnologias utilizadas

| Tecnologia | Aplicação |
|---|---|
| Python | Lógica e processamento do backend |
| OpenCV | Processamento de imagens |
| NumPy | Manipulação de matrizes e pixels |
| Flask | Desenvolvimento da API |
| Flask-CORS | Comunicação entre frontend e backend |
| HTML5 | Estrutura da interface |
| CSS3 | Estilização da interface |
| JavaScript | Consumo da API e atualização dos dados |
| ESP32-CAM | Captura de imagens |
| Arduino IDE | Programação da ESP32-CAM |

## Estrutura do projeto

```text
Estacionamento_Inteligente/
│
├── backend/
│   ├── main.py
│   └── vagas_A1_A10.json
│
├── frontend/
│   └── index.html
│
├── esp32/
│   ├── camera.ino
│   ├── secrets.example.h
│   └── secrets.h (arquivo local, não versionado)
│
├── requirements.txt
├── .gitignore
└── README.md
```

## Pré-requisitos

Antes de executar o projeto, é necessário ter:

- Python instalado.
- Git instalado.
- Arduino IDE configurada para placas ESP32.
- ESP32-CAM compatível com o firmware do projeto.
- Computador e ESP32-CAM conectados à mesma rede local.
- Dependências Python instaladas.

## Instalação e configuração

### 1. Clonar o repositório

```bash
git clone <URL_DO_REPOSITORIO>
cd smart-parking
```

### 2. Criar o ambiente virtual

No Windows, utilizando PowerShell:

```powershell
py -m venv .venv
```

Ativar o ambiente:

```powershell
.\.venv\Scripts\Activate.ps1
```

### 3. Instalar as dependências

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configurar a ESP32-CAM

Na pasta `esp32`, existe o arquivo `secrets.example.h`, que contém o modelo das credenciais necessárias para a conexão Wi-Fi.

Crie uma cópia desse arquivo com o nome `secrets.h` e configure:

```cpp
#pragma once

#define WIFI_SSID "NOME_DA_REDE"
#define WIFI_PASSWORD "SENHA_DA_REDE"
```

O arquivo `secrets.h` deve permanecer local e não deve ser enviado ao GitHub.

Abra `camera.ino` na Arduino IDE, selecione a placa AI Thinker ESP32-CAM e configure as opções de programação correspondentes ao hardware utilizado.

Após gravar o firmware, abra o Monitor Serial com velocidade de 115200 baud para consultar o endereço IP atribuído à câmera.

### 5. Configurar o backend

Abra o arquivo:

```text
backend/main.py
```

Atualize a variável `URL_CAPTURE` com o endereço IP atual da ESP32-CAM:

```python
URL_CAPTURE = "http://IP_DA_CAMERA/capture"
```

Certifique-se de que o arquivo `vagas_A1_A10.json` esteja presente na pasta `backend`.

### 6. Executar o backend

No terminal, entre na pasta:

```powershell
cd backend
```

Com o ambiente virtual ativado, execute:

```powershell
python main.py
```

Caso ainda não exista um arquivo de coordenadas, o sistema iniciará o modo de calibração.

Durante a calibração:

- Arraste o mouse para delimitar cada vaga.
- As regiões serão identificadas sequencialmente como A1, A2, até A10.
- Pressione `Z` para desfazer a última marcação.
- Pressione `S` para salvar as coordenadas.

Após a calibração, as coordenadas serão armazenadas em `vagas_A1_A10.json` e poderão ser reutilizadas nas próximas execuções.

Durante o monitoramento, pressione `Q` na janela de processamento para encerrar a visualização.

## Processamento de imagens

O sistema utiliza parâmetros configuráveis para determinar a ocupação das vagas.

Atualmente, os principais parâmetros são:

| Parâmetro | Valor padrão | Finalidade |
|---|---:|---|
| `TOLERANCIA_SATURACAO` | 65 | Limite de saturação HSV para identificar pixels coloridos |
| `PORCENTAGEM_MINIMA_OCUPACAO` | 0.15 | Proporção mínima de pixels coloridos para considerar uma vaga ocupada |
| `URL_CAPTURE` | IP da ESP32-CAM | Endereço para obtenção das imagens |

A análise considera a porcentagem de pixels que ultrapassam o limite de saturação dentro da região de cada vaga.

Quando essa proporção atinge ou ultrapassa o limite configurado, a vaga é classificada como ocupada.

Os parâmetros podem ser ajustados conforme as características físicas da maquete, as cores utilizadas e as condições de iluminação.

## API

O backend disponibiliza uma rota HTTP para consulta dos estados das vagas.

**Consultar vagas**

```http
GET /api/vagas
```

Endereço local:

```text
http://localhost:5000/api/vagas
```

Exemplo de resposta:

```json
{
    "vagas_ocupadas": [
        "A2",
        "A5",
        "A8"
    ]
}
```

A API retorna a lista de vagas identificadas como ocupadas. As demais são consideradas livres pelo frontend.

## Frontend

A interface consulta a API periodicamente, utilizando o endpoint `/api/vagas`.

A atualização padrão ocorre a cada segundo.

Por padrão, o frontend está configurado para acessar:

```javascript
const API_BASE_URL = "http://localhost:5000";
```

Caso o frontend seja acessado por outro dispositivo da rede local, será necessário substituir `localhost` pelo endereço IP do computador que executa o Flask.

## Observações e limitações

- O sistema utiliza análise de saturação de cores, não um modelo de inteligência artificial treinado, o que é um ponto de melhoria futura.
- As coordenadas das vagas são definidas durante a calibração, podendo variar conforme o ângulo da câmera.
- O posicionamento da câmera deve permanecer estável após a calibração.
- A iluminação, as sombras, os reflexos e as cores dos elementos da maquete podem influenciar os resultados.
- Os parâmetros de saturação e ocupação podem exigir ajustes para melhorar a confiabilidade das detecções.

## Objetivo acadêmico

O projeto integra conceitos de Engenharia de Computação, Sistemas Embarcados, Internet das Coisas (IoT), Processamento Digital de Imagens, desenvolvimento de software e comunicação entre dispositivos.

A proposta é demonstrar como a integração entre hardware, software e visão computacional pode ser aplicada à automação e ao monitoramento de estacionamentos.

---

**EstacionaAI — Engenharia de Computação**