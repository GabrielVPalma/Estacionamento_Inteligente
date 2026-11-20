import cv2
import json
import os
import time
import threading
import urllib.request
import numpy as np
from flask import Flask, jsonify
from flask_cors import CORS

# =========================================================================
# CONFIGURAÇÕES GERAIS E TOLERÂNCIA DE TONALIDADE
# =========================================================================
URL_CAPTURE = "http://IP_DA_ESP32/capture"  # <-- INSIRA O IP DA ESP32-CAM
ARQUIVO_COORDENADAS = "vagas_A1_A10.json"
PREFIXO_VAGA = "A"

# Taxa de tolerância de tonalidade (Saturação HSV de 0 a 255):
# - Branco / Cinza / Sombras ficam entre 0 e 45.
# - Cores vibrantes ficam acima de 65.
# Aumente se o piso tiver reflexo colorido; diminua se o carro tiver cor pastel.
TOLERANCIA_SATURACAO = 65

# Porcentagem mínima da área da vaga que precisa ter cor vibrante para considerar ocupada
PORCENTAGEM_MINIMA_OCUPACAO = 0.15  # 15% da área da vaga

# JSON compartilhado com o Frontend (apenas vagas ocupadas)
dados_para_frontend = {
    "vagas_ocupadas": []
}
lock = threading.Lock()

app = Flask(__name__)
CORS(app)

@app.route("/api/vagas", methods=["GET"])
def rota_api_vagas():
    with lock:
        return jsonify(dados_para_frontend)

# =========================================================================
# 1. CAPTURA DE IMAGEM DA ESP32-CAM
# =========================================================================
def obter_frame_esp32():
    resposta = urllib.request.urlopen(URL_CAPTURE, timeout=3)
    bytes_img = bytearray(resposta.read())
    np_img = np.frombuffer(bytes_img, dtype=np.uint8)
    return cv2.imdecode(np_img, cv2.IMREAD_COLOR)

# =========================================================================
# 2. CALIBRAÇÃO POR ARRASTO DE MOUSE (A1, A2... A10)
# =========================================================================
def calibrar_vagas():
    print("\n=== MODO DE CALIBRAÇÃO ===")
    print("Arraste o mouse para desenhar o retângulo de cada vaga (A1, A2...).")
    print("Pressione 'z' para desfazer a última | Pressione 's' para SALVAR.")

    frame_base = None
    while frame_base is None:
        try:
            frame_base = obter_frame_esp32()
        except Exception:
            print("Aguardando imagem da ESP32-CAM...")
            time.sleep(1)

    vagas_salvas = {}
    desenhando = False
    ix, iy, rx, ry = -1, -1, -1, -1

    def mouse_callback(event, x, y, flags, param):
        nonlocal desenhando, ix, iy, rx, ry
        if event == cv2.EVENT_LBUTTONDOWN:
            desenhando = True
            ix, iy, rx, ry = x, y, x, y
        elif event == cv2.EVENT_MOUSEMOVE and desenhando:
            rx, ry = x, y
        elif event == cv2.EVENT_LBUTTONUP:
            desenhando = False
            x1, x2 = min(ix, x), max(ix, x)
            y1, y2 = min(iy, y), max(iy, y)
            if (x2 - x1) > 15 and (y2 - y1) > 15:
                nome = f"{PREFIXO_VAGA}{len(vagas_salvas) + 1}"
                vagas_salvas[nome] = [x1, y1, x2, y2]
                print(f"Vaga {nome} salva: {[x1, y1, x2, y2]}")

    cv2.namedWindow("Calibrar Vagas")
    cv2.setMouseCallback("Calibrar Vagas", mouse_callback)

    while True:
        img = frame_base.copy()
        for nome, (x1, y1, x2, y2) in vagas_salvas.items():
            cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(img, nome, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        if desenhando:
            cv2.rectangle(img, (ix, iy), (rx, ry), (0, 255, 255), 2)

        cv2.imshow("Calibrar Vagas", img)
        tecla = cv2.waitKey(1) & 0xFF
        if tecla == ord('z') and vagas_salvas:
            del vagas_salvas[list(vagas_salvas.keys())[-1]]
        elif tecla == ord('s') and vagas_salvas:
            with open(ARQUIVO_COORDENADAS, "w") as f:
                json.dump(vagas_salvas, f, indent=4)
            break

    cv2.destroyAllWindows()
    return vagas_salvas

# =========================================================================
# 3. DETECÇÃO POR TOLERÂNCIA DE TONALIDADE (SATURAÇÃO HSV)
# =========================================================================
def processar_vagas_por_cor(mapa_vagas):
    print("\nMonitoramento ativo! Pressione 'q' na janela de vídeo para sair.")

    while True:
        try:
            frame = obter_frame_esp32()
            if frame is None:
                continue

            # Suaviza levemente para eliminar ruído granulado da câmera
            frame_suavizado = cv2.GaussianBlur(frame, (5, 5), 0)
            
            # Converte o frame inteiro para o espaço de cores HSV
            hsv = cv2.cvtColor(frame_suavizado, cv2.COLOR_BGR2HSV)

            lista_ocupadas = []

            for nome_vaga, (x1, y1, x2, y2) in mapa_vagas.items():
                # Recorta apenas a região da vaga no espaço HSV
                recorte_hsv = hsv[y1:y2, x1:x2]

                # Extrai apenas o canal S (Saturação - índice 1)
                canal_saturacao = recorte_hsv[:, :, 1]

                # Cria uma máscara: pixels com saturação > tolerância viram 255 (branco)
                # Pixels brancos/cinzas do piso (saturação baixa) viram 0 (preto)
                _, mascara_cor = cv2.threshold(canal_saturacao, TOLERANCIA_SATURACAO, 255, cv2.THRESH_BINARY)

                # Calcula a porcentagem de pixels coloridos dentro da vaga
                total_pixels = mascara_cor.size
                pixels_coloridos = cv2.countNonZero(mascara_cor)
                taxa_ocupacao = pixels_coloridos / total_pixels

                # Verifica se ultrapassou a porcentagem mínima definida
                vaga_ocupada = taxa_ocupacao >= PORCENTAGEM_MINIMA_OCUPACAO

                if vaga_ocupada:
                    lista_ocupadas.append(nome_vaga)
                    cor = (0, 0, 255)  # Vermelho
                else:
                    cor = (0, 255, 0)  # Verde

                # Exibe o retângulo e a porcentagem de cor detectada (útil para ajuste fino)
                cv2.rectangle(frame, (x1, y1), (x2, y2), cor, 2)
                cv2.putText(
                    frame,
                    f"{nome_vaga} ({int(taxa_ocupacao * 100)}%)",
                    (x1, y1 - 5),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    cor,
                    2
                )

            # Atualiza o JSON para o Frontend
            with lock:
                dados_para_frontend["vagas_ocupadas"] = lista_ocupadas

            cv2.imshow("Smart Parking - Filtro de Tonalidade", frame)

        except Exception as e:
            print(f"Erro no ciclo: {e}")

        time.sleep(0.05)  # ~20 FPS
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cv2.destroyAllWindows()

if __name__ == "__main__":
    if os.path.exists(ARQUIVO_COORDENADAS):
        with open(ARQUIVO_COORDENADAS, "r") as f:
            coordenadas = json.load(f)
    else:
        coordenadas = calibrar_vagas()

    t = threading.Thread(target=processar_vagas_por_cor, args=(coordenadas,), daemon=True)
    t.start()

    print("API JSON rodando em: http://localhost:5000/api/vagas")
    app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)