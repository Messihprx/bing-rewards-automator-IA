import customtkinter as ctk
import time
import random
import threading
import keyboard
import json
import os
from openai import OpenAI

# Bibliotecas do Selenium
from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

CONFIG_FILE = "config_busca_selenium.json"

class AppBuscaIA(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Bing Rewards Automator Pro v2.5")
        self.geometry("480x880")
        ctk.set_appearance_mode("dark")
        
        self.rodando = False
        self.driver = None
        
        # Variáveis de Interface
        self.tecla_parar = ctk.StringVar(value="esc")
        self.api_key_var = ctk.StringVar(value="")
        self.modelo_ia_var = ctk.StringVar(value="meta/llama-3.1-8b-instruct")
        self.modo_mobile = ctk.BooleanVar(value=False)

        self.carregar_configuracoes()

        self.tabview = ctk.CTkTabview(self, width=440, height=830)
        self.tabview.pack(padx=10, pady=10)
        
        self.tab_busca = self.tabview.add("Painel de Controle")
        self.tab_config = self.tabview.add("Configurações")

        self.setup_aba_busca()
        self.setup_aba_config()
        self.iniciar_monitor_teclado()

    def log(self, mensagem):
        self.textbox.insert("end", f"> {mensagem}\n")
        self.textbox.see("end")

    def salvar_configuracoes(self):
        dados = {
            "atalho": self.tecla_parar.get(),
            "api_key": self.api_key_var.get(),
            "modelo": self.modelo_ia_var.get()
        }
        with open(CONFIG_FILE, "w") as f:
            json.dump(dados, f)
        self.log("💾 Configurações salvas!")

    def carregar_configuracoes(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f:
                    dados = json.load(f)
                    self.tecla_parar.set(dados.get("atalho", "esc"))
                    self.api_key_var.set(dados.get("api_key", ""))
                    self.modelo_ia_var.set(dados.get("modelo", "meta/llama-3.1-8b-instruct"))
            except: pass

    def setup_aba_busca(self):
        ctk.CTkLabel(self.tab_busca, text="🚀 Automação Bing", font=("Roboto", 24, "bold")).pack(pady=10)

        self.frame_modo = ctk.CTkFrame(self.tab_busca)
        self.frame_modo.pack(pady=10, fill="x", padx=20)
        
        ctk.CTkLabel(self.frame_modo, text="Modo de Navegação:", font=("Roboto", 12)).pack(side="left", padx=10)
        self.switch_mobile = ctk.CTkSwitch(self.frame_modo, text="MOBILE", variable=self.modo_mobile, 
                                          progress_color="#3498db", font=("Roboto", 12, "bold"))
        self.switch_mobile.pack(side="right", padx=10, pady=10)

        self.entry_qtd = ctk.CTkEntry(self.tab_busca, placeholder_text="Quantidade de buscas", height=35)
        self.entry_qtd.pack(pady=10, fill="x", padx=40)
        self.entry_qtd.insert(0, "30")

        self.btn_iniciar = ctk.CTkButton(self.tab_busca, text="INICIAR PROCESSO", command=self.start_thread, 
                                          fg_color="#27ae60", hover_color="#2ecc71", height=45, font=("Roboto", 16, "bold"))
        self.btn_iniciar.pack(pady=15, fill="x", padx=40)

        self.btn_parar = ctk.CTkButton(self.tab_busca, text="🛑 PARAR AGORA", command=self.parar_aplicacao, 
                                         fg_color="#c0392b", hover_color="#e74c3c")
        self.btn_parar.pack(pady=0, fill="x", padx=40)

        # Status do Cooldown / Contagem Regressiva
        self.status_tempo = ctk.CTkLabel(self.tab_busca, text="Próxima busca em: --s", font=("Roboto", 14, "italic"), text_color="#f1c40f")
        self.status_tempo.pack(pady=(15, 0))

        self.status_label = ctk.CTkLabel(self.tab_busca, text="Status: Pronto", text_color="#95a5a6")
        self.status_label.pack(pady=5)

        self.textbox = ctk.CTkTextbox(self.tab_busca, width=380, height=280, font=("Consolas", 12))
        self.textbox.pack(pady=10, padx=10)

    def setup_aba_config(self):
        ctk.CTkLabel(self.tab_config, text="Ajustes da API & Sistema", font=("Roboto", 16, "bold")).pack(pady=15)
        
        ctk.CTkLabel(self.tab_config, text="NVIDIA API Key:").pack(anchor="w", padx=40)
        self.entry_api = ctk.CTkEntry(self.tab_config, textvariable=self.api_key_var, show="*")
        self.entry_api.pack(pady=5, fill="x", padx=40)

        ctk.CTkLabel(self.tab_config, text="Nome do Modelo:").pack(anchor="w", padx=40)
        self.entry_modelo = ctk.CTkEntry(self.tab_config, textvariable=self.modelo_ia_var)
        self.entry_modelo.pack(pady=5, fill="x", padx=40)
        
        ctk.CTkLabel(self.tab_config, text="Tecla de Emergência:").pack(pady=(10,0))
        self.entry_tecla = ctk.CTkEntry(self.tab_config, textvariable=self.tecla_parar, width=100, justify="center")
        self.entry_tecla.pack(pady=5)

        self.btn_salvar = ctk.CTkButton(self.tab_config, text="💾 SALVAR CONFIGURAÇÕES", command=self.salvar_configuracoes)
        self.btn_salvar.pack(pady=20)

        ctk.CTkLabel(self.tab_config, text="").pack(expand=True) 
        
        creditos_frame = ctk.CTkFrame(self.tab_config, fg_color="transparent")
        creditos_frame.pack(pady=10)

        ctk.CTkLabel(creditos_frame, text="Desenvolvido por:", font=("Roboto", 10, "italic"), text_color="#7f8c8d").pack()
        ctk.CTkLabel(creditos_frame, text="Messihprx", font=("Roboto", 12, "bold"), text_color="#3498db").pack()
        ctk.CTkLabel(creditos_frame, text="v2.0 - 2026", font=("Roboto", 9), text_color="#7f8c8d").pack()

    def parar_aplicacao(self):
        self.rodando = False
        if self.driver:
            try: self.driver.quit()
            except: pass
            self.driver = None
        self.status_label.configure(text="Status: PARADO", text_color="#e74c3c")
        self.status_tempo.configure(text="Próxima busca em: --s")
        self.btn_iniciar.configure(state="normal")

    def iniciar_monitor_teclado(self):
        def monitor():
            while True:
                try:
                    if keyboard.is_pressed(self.tecla_parar.get().lower()):
                        if self.rodando: self.parar_aplicacao()
                    time.sleep(0.1)
                except: pass
        threading.Thread(target=monitor, daemon=True).start()

    def gerar_termo_ia(self, client_ia):
        try:
            completion = client_ia.chat.completions.create(
                model=self.modelo_ia_var.get(), 
                messages=[{"role":"user", "content":"Gere uma busca curta aleatória, use temas diversos, tente variar sem repetições.E MANDE APENAS O TEXTO. e lembrando, geres textos pequenos, de no máximo 5 palavras. NÃO COLOQUE ASPAS nem outros caracteres especiais."}],  
                max_tokens=20,
                temperature=0.9
            )
            texto_bruto = completion.choices[0].message.content.strip()
            termo_limpo = texto_bruto.split('\n')[0]
            return termo_limpo.replace('"', '').replace('.', '')
        except:
            temas = ["curiosidades", "história", "tecnologia", "ciência", "viagens"]
            return f"{random.choice(temas)} {random.randint(100,999)}"

    def loop_busca(self):
        minha_chave = self.api_key_var.get().strip()
        if not minha_chave:
            self.log("❌ ERRO: API Key não configurada!")
            return

        client_ia = OpenAI(base_url="https://integrate.api.nvidia.com/v1", api_key=minha_chave)

        self.log("Limpando processos...")
        os.system("taskkill /f /im msedge.exe >nul 2>&1")
        os.system("taskkill /f /im msedgedriver.exe >nul 2>&1")
        time.sleep(2)

        self.rodando = True
        self.btn_iniciar.configure(state="disabled")
        modo_nome = "MOBILE" if self.modo_mobile.get() else "DESKTOP"
        self.status_label.configure(text=f"Status: {modo_nome} ATIVO", text_color="#3498db")
        
        usuario = os.getlogin()
        user_data = f"C:\\Users\\{usuario}\\AppData\\Local\\Microsoft\\Edge\\User Data"
        
        edge_options = Options()
        edge_options.add_argument(f"user-data-dir={user_data}")
        edge_options.add_argument("profile-directory=Default")
        edge_options.add_argument("--remote-allow-origins=*")
        edge_options.add_argument("--disable-blink-features=AutomationControlled")
        
        if not self.modo_mobile.get():
            edge_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0")

        if self.modo_mobile.get():
            mobile_emulation = {
                "deviceMetrics": { "width": 390, "height": 844, "pixelRatio": 3.0 },
                "userAgent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1 Edg/122.0.0.0"
            }
            edge_options.add_experimental_option("mobileEmulation", mobile_emulation)

        try:
            self.driver = webdriver.Edge(options=edge_options)
            qtd = int(self.entry_qtd.get())

            for i in range(qtd):
                if not self.rodando: break
                
                termo = self.gerar_termo_ia(client_ia)
                self.log(f"[{i+1}/{qtd}] Digitando: {termo}")
                
                self.driver.get("https://www.bing.com")
                time.sleep(random.uniform(3, 5))
                
                try:
                    wait = WebDriverWait(self.driver, 10)
                    search_box = wait.until(EC.element_to_be_clickable((By.NAME, "q")))
                    
                    search_box.click()
                    time.sleep(0.5)
                    search_box.clear()
                    
                    for letra in termo:
                        if not self.rodando: break
                        search_box.send_keys(letra)
                        time.sleep(random.uniform(0.1, 0.25))
                    
                    time.sleep(0.7)
                    search_box.send_keys(Keys.ENTER)
                    
                except:
                    self.driver.get(f"https://www.bing.com/search?q={termo.replace(' ', '+')}")

                # Simulação Humana
                time.sleep(random.uniform(4, 7))
                self.driver.execute_script(f"window.scrollTo(0, {random.randint(400, 1000)});")
                
                # --- CONTAGEM REGRESSIVA NA TELA ---
                espera_total = random.randint(16, 24)
                for restante in range(espera_total, 0, -1):
                    if not self.rodando: break
                    self.status_tempo.configure(text=f"Próxima busca em: {restante}s", text_color="#f1c40f")
                    time.sleep(1)
                
                self.status_tempo.configure(text="Iniciando nova busca...", text_color="#2ecc71")

            self.log(f"✅ Ciclo finalizado com sucesso!")
            
        except Exception as e:
            self.log(f"❌ Erro: {str(e)[:40]}")
        
        self.parar_aplicacao()

    def start_thread(self):
        threading.Thread(target=self.loop_busca, daemon=True).start()

if __name__ == "__main__":
    app = AppBuscaIA()
    app.mainloop()