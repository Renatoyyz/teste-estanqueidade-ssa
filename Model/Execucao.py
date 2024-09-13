from PyQt5.QtWidgets import QDialog, QApplication
from PyQt5.QtCore import Qt, QCoreApplication, QObject, pyqtSignal, QThread
import time

from View.tela_execucao import Ui_TelaExecucao
class AtualizacaoThread(QThread):
    sinal_atualizar = pyqtSignal(str, int, int)# Inicializa com a quantidade de variáveis que se deseja

    def __init__(self, instancia):
        super().__init__()
        self.instancia = instancia
        self._running = True

    def run(self):
        while self._running == True:
            try:
                self.sinal_atualizar.emit("",0,0)
                QThread.msleep(500)
            except Exception as e:
                print(f"Erro na Thread Atualizacao {e}")

    def iniciar(self):
        self._running = True
        self.start()

    def parar(self):
        self._running = False


class ExecucaoThread(QThread):
    sinal_atualizar = pyqtSignal(str, int, int)# Inicializa com a quantidade de variáveis que se deseja
    
    def __init__(self, instancia):
        super().__init__()
        self.instancia = instancia
        self._running = True
        self.invazao = False
        self.passou_nao_passou = False
        self.mensagem = ""

    def run(self):
        while self._running == True:
            try:
                if self.instancia._inicia_teste == True:
                    self.executa_teste()
                    self.sinal_atualizar.emit(self.mensagem,self.passou_nao_passou,self.invazao)
                    self.instancia._inicia_teste = False
                else:
                    self.invazao = False
                    self.passou_nao_passou = False
                    self.mensagem = ""
                QThread.msleep(500)
            except Exception as e:
                print(f"Erro na Thread Operacao {e}")
    
    def executa_teste(self):
        self.instancia.io.desliga_lateral()
        if self.timer_com_erro(1) == True:
            self.instancia.io.liga_principal()
            self.instancia.io.habilita_cortina_luz()
            if self.timer_com_erro(3.5) == True:
                 self.instancia.io.liga_lateral()
                 if self.timer_com_erro(4) == True:
                     self.instancia.io.start_ateq()
                     if self.check_ateq() == True:
                         self.mensagem = "Teste executado com sucesso."
                         self.passou_nao_passou = True
                     else:
                        self.mensagem = "Falha no teste.\nPressione o botão reset e descarte as 4 peças."
                        self.passou_nao_passou = False

    def check_ateq(self):
        cnt_ateq = 0
        ret = False
        while self.instancia.dado.TEMPO_ESPERA_ATEQ > cnt_ateq:
            print(f"cnt_ateq: {cnt_ateq}")
            cnt_ateq += 1
            QThread.msleep(1000)
            if self.instancia.io.io_rpi.passa_ateq == 0:
                ret = True
                break
            elif self.instancia.io.io_rpi.fail_ateq == 0:
                ret = False
                break
        return ret
                 


    def timer_com_erro(self, t):
        tempo = int(t*1000)

        for _ in range(tempo):
            if self.instancia.io.io_rpi.cortina_luz == 1:
                self.invazao = True
                self.mensagem = "Invazão detectada pela cortina de luz."
                return False
            QThread.msleep(1)
        return True

    def iniciar(self):
        self._running = True
        self.start()

    def parar(self):
        self._running = False

class Execucao(QDialog):
    def __init__(self, dado=None, io=None):
        super().__init__()

        self.io = io
        self.dado = dado
        self.mensagem = ""
        self._inicia_teste = False
        self.cnt_pecas_aprovadas = 0
        self.cnt_pecas_reprovadas = 0

        self.cnt_para_liberar_pecas_rerovadas = 0
        self.libera_contagem_pecas_reprovadas = False

        # Configuração da interface do usuário gerada pelo Qt Designer
        self.ui = Ui_TelaExecucao()
        self.ui.setupUi(self)

        # Remover a barra de título e ocultar os botões de maximizar e minimizar
        # self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.WindowState.WindowMaximized)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        
        # Maximizar a janela
        # self.showMaximized()
        if self.dado.full_scream == True:
            self.setWindowState(Qt.WindowState.WindowFullScreen)

        self.ui.btVoltar.clicked.connect(self.voltar)
        self.ui.btReset.clicked.connect(self.reset_sistema)    

        # Inicializar o atualizador em uma nova thread
        # Atualizador Thread
        self.atualizador = ExecucaoThread(self)
        self.atualizador.sinal_atualizar.connect(self.thread_execucao)
        self.atualizador.iniciar()

        self.visualuizador = AtualizacaoThread(self)
        self.visualuizador.sinal_atualizar.connect(self.thread_visualizacao)
        self.visualuizador.iniciar()

        QApplication.processEvents()  # Mantém a UI responsiva após iniciar as threads

        self.config()
    
    def thread_visualizacao(self, msg, passou_nao_passou, falha):
        # Se botões esquerdo e direito pressionados
        if self.io.io_rpi.botao_esquerdo == 0 and self.io.io_rpi.botao_direito == 0 and self._inicia_teste == False and self.libera_contagem_pecas_reprovadas == False:
            self.ui.txaInformacoes.setText("Executando Teste")
            self._inicia_teste = True # Inicia o teste
            self.io.desliga_sinalizacao()
        if self.libera_contagem_pecas_reprovadas == True and self.io.io_rpi.sensor_otico == 1:
            while self.io.io_rpi.sensor_otico == 1:
                time.sleep(0.5)
            self.cnt_para_liberar_pecas_rerovadas += 1
            if self.cnt_para_liberar_pecas_rerovadas >= 4:
                self.libera_contagem_pecas_reprovadas = False
                self.cnt_para_liberar_pecas_rerovadas = 0
                self.ui.txaInformacoes.setText("Máquina pronta.")
                # time.sleep(1)

    def thread_execucao(self,msg, passou_nao_passou, falha):
        self.mensagem = msg
        if msg != "":
            if passou_nao_passou == True and falha == False:
                self.io.aciona_marcacao()
                self.config()
                self.ui.txaInformacoes.setText(self.mensagem)
                self.muda_valor_pecas_aprovadas(4)
            elif passou_nao_passou == False and falha == False:
                # self.config()
                self.ui.txaInformacoes.setText(self.mensagem)
                self.muda_valor_pecas_reprovadas(4)
                self.io.sinaliza_nao_passou()
                self.libera_contagem_pecas_reprovadas = True # Libera a contagem de peças reprovadas
            elif falha == True:
                # self.config()
                self.ui.txaInformacoes.setText(self.mensagem)

    def muda_valor_pecas_aprovadas(self, valor):
        self.cnt_pecas_aprovadas += valor
        self.ui.lbNumPecasAprovadas.setText(f"<html><head/><body><p align=\"center\">{self.cnt_pecas_aprovadas}</p></body></html>")
        # self.ui.lbNumPecasReprovadas.setText(_translate("TelaExecucao", "<html><head/><body><p align=\"center\">0</p></body></html>"))

    def muda_valor_pecas_reprovadas(self, valor):
        self.cnt_pecas_reprovadas += valor
        self.ui.lbNumPecasReprovadas.setText(f"<html><head/><body><p align=\"center\">{self.cnt_pecas_reprovadas}</p></body></html>")
        # self.ui.lbNumPecasReprovadas.setText(_translate("TelaExecucao", "<html><head/><body><p align=\"center\">0</p></body

    def reset_sistema(self):
        # self.cnt_pecas_aprovadas = 0
        # self.cnt_pecas_reprovadas = 0
        self.ui.lbNumPecasAprovadas.setText(f"<html><head/><body><p align=\"center\">{self.cnt_pecas_aprovadas}</p></body></html>")
        self.ui.lbNumPecasReprovadas.setText(f"<html><head/><body><p align=\"center\">{self.cnt_pecas_reprovadas}</p></body></html>")
        self.config()

    def config(self):
        self.ui.lbNumPecasAprovadas.setText(f"<html><head/><body><p align=\"center\">{self.cnt_pecas_aprovadas}</p></body></html>")
        self.ui.lbNumPecasReprovadas.setText(f"<html><head/><body><p align=\"center\">{self.cnt_pecas_reprovadas}</p></body></html>")
        # self.mensagem = "Maquina pronta para iniciar o teste."
        # self.ui.txaInformacoes.setText(self.mensagem)
        self.io.desliga_lateral()
        time.sleep(1)
        self.io.desliga_principal()
        time.sleep(1)
        self.io.desabilita_cortina_luz()

    def voltar(self):
        self.close()

    def closeEvent(self, event):
        self.config()
        self.io.habilita_cortina_luz()
        self.atualizador.parar()  # Parar a thread do atualizador
        self.visualuizador.parar() # Parar a thread do visualizador
        event.accept()