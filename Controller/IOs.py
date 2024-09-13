import time
import serial
import sys

class FakeRPiGPIO:
    BCM = "BCM"
    PUD_UP = "PUD_UP"
    IN = "IN"

    @staticmethod
    def setmode(mode):
        pass

    @staticmethod
    def setwarnings(state):
        pass

    @staticmethod
    def setup(pin, direction, pull_up_down=None):
        pass

    @staticmethod
    def input(pin):
        return 1  # Altere isso conforme necessário

class InOut:
    def __init__(self):
        self.PASS_ATEQ = 23
        self.FAIL_ATEQ = 22

        self.ACIO_DIREITO = 24
        self.ACIO_ESQUERDO = 10
        self.CORTINA_LUZ = 2
        self.SENSOR_OTICO = 3

        self.RE_DE = 17
        self.SERIAL_OUT = 0
        self.SERIAL_IN = 1
        
        try:
            import RPi.GPIO as GPIO
            self.GPIO = GPIO
        except ImportError:
            print("RPi.GPIO not found. Using fake GPIO.")
            self.GPIO = FakeRPiGPIO()

        self.GPIO.setmode(self.GPIO.BCM)
        self.GPIO.setwarnings(False)

        self.GPIO.setup(self.PASS_ATEQ, self.GPIO.IN, pull_up_down=self.GPIO.PUD_UP)
        self.GPIO.setup(self.FAIL_ATEQ, self.GPIO.IN, pull_up_down=self.GPIO.PUD_UP)

        self.GPIO.setup(self.ACIO_DIREITO, self.GPIO.IN, pull_up_down=self.GPIO.PUD_UP)
        self.GPIO.setup(self.ACIO_ESQUERDO, self.GPIO.IN, pull_up_down=self.GPIO.PUD_UP)
        self.GPIO.setup(self.CORTINA_LUZ, self.GPIO.IN, pull_up_down=self.GPIO.PUD_UP)
        self.GPIO.setup(self.SENSOR_OTICO, self.GPIO.IN, pull_up_down=self.GPIO.PUD_UP)


        self.GPIO.setup(self.RE_DE,self.GPIO.OUT)
        self.GPIO.output(self.RE_DE,1)

    @property
    def passa_ateq(self):
        return self.GPIO.input(self.PASS_ATEQ)

    @property
    def fail_ateq(self):
        return self.GPIO.input(self.FAIL_ATEQ)

    @property
    def botao_direito(self):
        return self.GPIO.input(self.ACIO_DIREITO)

    @property
    def botao_esquerdo(self):
        return self.GPIO.input(self.ACIO_ESQUERDO)

    @property
    def cortina_luz(self):
        return self.GPIO.input(self.CORTINA_LUZ)
    
    @property
    def sensor_otico(self):
        return self.GPIO.input(self.SENSOR_OTICO)
    
    def aciona_re_de(self, status):
        self.GPIO.output(self.RE_DE,status)
    
    
class IO_MODBUS:
    def __init__(self, dado):
        self.dado = dado
        self._running = True
        self.io_rpi = InOut()
        self.ADR_1 = 1 # Endereço do WP8027 dos relés do lado esquerdo - 16 saídas
        self.ADR_2 = 2 # Endereço do WP8027 dos relés do lado direito - 16 saídas
        self.ADR_3 = 3 # Endereço do WP8027 de automações em geral - 16 saídas
        self.ADR_4 = 4 # Endereço do WP8026 de automações em geral - 16 entradas

        self.valor_saida_direito = 0
        self.valor_saida_esquerdo = 0
        self.valor_saida_geral = 0

        self.entradas_wp8026 = {
            "in_1": 0,
            "in_2": 0,
            "in_3": 0,
            "in_4": 0,
            "in_5": 0,
            "in_6": 0,
            "in_7": 0,
            "in_8": 0,
            "in_9": 0,
            "in_10": 0,
            "in_11": 0,
            "in_12": 0,
            "in_13": 0,
            "in_14": 0,
            "in_15": 0,
            "in_16": 0,
        }
        self.adr = self.ADR_1
        self.saida = 0
        self.on_off = 0
        self.cnt_entradas = 1

        self.ser = serial.Serial(
                                    port='/dev/ttyUSB0',  # Porta serial padrão no Raspberry Pi 4
                                    # port='/dev/ttyS0',  # Porta serial padrão no Raspberry Pi 4
                                    baudrate=9600,       # Taxa de baud
                                    bytesize=8,
                                    parity="N",
                                    stopbits=1,
                                    timeout=1,            # Timeout de leitura
                                    #xonxoff=False,         # Controle de fluxo por software (XON/XOFF)
                                    #rtscts=True
                                )
        
        # self.start()

    def crc16_modbus(self, data):
        crc = 0xFFFF
        for byte in data:
            crc ^= byte
            for _ in range(8):
                if (crc & 0x0001):
                    crc >>= 1
                    crc ^= 0xA001
                else:
                    crc >>= 1
        return crc

    def wp_8027(self, adr, out, on_off):
        dados_recebidos = None
        mask = 0
        if adr == self.ADR_1:
            mask = self.valor_saida_esquerdo
        elif adr == self.ADR_2:
            mask = self.valor_saida_direito
        elif adr == self.ADR_3:
            mask = self.valor_saida_geral
        elif adr == self.ADR_4:
            mask = self.valor_saida_geral2



        if (adr == self.ADR_1 or adr == self.ADR_2 or adr == self.ADR_3 or adr == self.ADR_4) and (on_off==1):  # Corrigindo a condição
            id_loc = hex(adr)[2:]
            id_loc = id_loc.zfill(2).upper()

            # Deslocando 1 para a esquerda pelo número de bits especificado em out
            if out < 9:
                out_loc = (1 << (out-1+8)) | (mask)
                mask = out_loc
                
                out_val_h = (out_loc) & 0xff
                out_val_l = (out_loc>>8) & 0xff
            else:
                out_loc = 1 << (out-1-8) | (mask)
                mask = out_loc

                out_val_h = (out_loc) & 0xff 
                out_val_l = (out_loc>>8) & 0xff

            if adr == self.ADR_1:
                self.valor_saida_esquerdo = mask
            elif adr == self.ADR_2:
                self.valor_saida_direito = mask
            elif adr == self.ADR_3:
                self.valor_saida_geral = mask
            elif adr == self.ADR_4:
                self.valor_saida_geral2 = mask

        elif (adr == self.ADR_1 or adr == self.ADR_2 or adr == self.ADR_3 or adr == self.ADR_4) and (on_off==0):
            id_loc = hex(adr)[2:]
            id_loc = id_loc.zfill(2).upper()
            out_loc = 0
            # Deslocando 1 para a esquerda pelo número de bits especificado em out
            if out < 9:
                out_loc = self.retorna_bit_desligar_0_8(adr,out)
                mask = out_loc
                
                out_val_h = (out_loc) & 0xff
                out_val_l = (out_loc>>8) & 0xff
            
            else:
                out_loc = self.retorna_bit_desligar_9_10(adr,out)
                mask = out_loc

                out_val_h = (out_loc) & 0xff 
                out_val_l = (out_loc>>8) & 0xff 

            if adr == self.ADR_1:
                self.valor_saida_esquerdo = mask
            elif adr == self.ADR_2:
                self.valor_saida_direito = mask
            elif adr == self.ADR_3:
                self.valor_saida_geral = mask 
            elif adr == self.ADR_4:
                self.valor_saida_geral2 = mask 

        # Invertendo a ordem dos bits
        # out_bin = out_bin[::-1]

        # Convertendo para hexadecimal com 4 dígitos
        out_hex = hex(out_loc)[2:].zfill(4).upper()

        hex_text = f"{id_loc}0f0000001002{out_hex}"
        bytes_hex = bytes.fromhex(hex_text)  # Transforma em hexa

        crc_result = self.crc16_modbus(bytes_hex) # Retorna o CRC

        parte_superior = (crc_result >> 8) & 0xFF  # Desloca 8 bits para a direita e aplica a máscara 0xFF
        parte_inferior = crc_result & 0xFF        # Aplica a máscara 0xFF diretamente

        for i in range(3):
            try:
                # Repete-se os comandos em decimal com os devidos bytes de CRC
                self.ser.write([adr,0x0f,0,0,0,16,2,out_val_l,out_val_h,parte_inferior,parte_superior])
                # self.ser.flush()
                start_time = time.time()

                while not self.ser.readable():
                    if time.time() - start_time > self.ser.timeout:
                        print("Timeout: Nenhuma resposta do escravo.")
                        break
                    time.sleep(0.1)  # Aguarde um curto período antes de verificar novamente

                dados_recebidos = self.ser.read(8)
                self.ser.flushInput()  # Limpa o buffer de entrada após a leitura
                if dados_recebidos != b'':
                    dados_recebidos = dados_recebidos.hex()
                    hex_text = dados_recebidos[0:2]+dados_recebidos[2:4]+dados_recebidos[4:6]+dados_recebidos[6:8]+dados_recebidos[8:10]+dados_recebidos[10:12]
                    bytes_hex = bytes.fromhex(hex_text) # Transforma em hexa
                    crc_result = self.crc16_modbus(bytes_hex) # Retorna o CRC

                    parte_superior = (crc_result >> 8) & 0xFF  # Desloca 8 bits para a direita e aplica a máscara 0xFF
                    parte_inferior = crc_result & 0xFF        # Aplica a máscara 0xFF diretamente

                    superior_crc = int(dados_recebidos[14:16],16) # Transforma de hexa para int
                    inferior_crc = int(dados_recebidos[12:14],16) # Transforma de hexa para int

                    if parte_superior == superior_crc and parte_inferior == inferior_crc:
                        dados_recebidos = dados_recebidos[14:16]
                        dados_recebidos = int(dados_recebidos,16)
                        return dados_recebidos
                    else:
                        if i > 1:
                            self.reset_serial()
                else:
                    if i > 1:
                        self.reset_serial()
            except Exception as e:
                print(f"Erro de comunicação: {e}")
                return -1 # Indica erro de alguma natureza....
        return -1
        
    def wp_8026(self, adr, input):
        dados_recebidos = None

        if adr == self.ADR_3:
            id_loc = hex(adr)[2:]
            id_loc = id_loc.zfill(2).upper()

            hex_text = f"{id_loc} 02 00 00 00 10"

            bytes_hex = bytes.fromhex(hex_text)  # Transforma em hexa

            crc_result = self.crc16_modbus(bytes_hex) # Retorna o CRC

            parte_superior = (crc_result >> 8) & 0xFF  # Desloca 8 bits para a direita e aplica a máscara 0xFF
            parte_inferior = crc_result & 0xFF        # Aplica a máscara 0xFF diretamente

            for i in range(3):
                try:
                    # Repete-se os comandos em decimal com os devidos bytes de CRC
                    self.ser.write([adr,2,0,0,0,16,parte_inferior, parte_superior])
                    # self.ser.flush()
                    start_time = time.time()
                    while not self.ser.readable():
                        if time.time() - start_time > self.ser.timeout:
                            print("Timeout: Nenhuma resposta do escravo.")
                            return -1
                        time.sleep(0.1)  # Aguarde um curto período antes de verificar novamente
                    dados_recebidos = self.ser.read(7)
                    self.ser.flushInput()  # Limpa o buffer de entrada após a leitura
                    if dados_recebidos != b'':
                        dados_recebidos = dados_recebidos.hex()
                        hex_text = dados_recebidos[0:2]+dados_recebidos[2:4]+dados_recebidos[4:6]+dados_recebidos[6:8]+dados_recebidos[8:10]
                        bytes_hex = bytes.fromhex(hex_text) # Transforma em hexa
                        crc_result = self.crc16_modbus(bytes_hex) # Retorna o CRC

                        parte_superior = (crc_result >> 8) & 0xFF  # Desloca 8 bits para a direita e aplica a máscara 0xFF
                        parte_inferior = crc_result & 0xFF        # Aplica a máscara 0xFF diretamente

                        superior_crc = int(dados_recebidos[12:14],16) # Transforma de hexa para int
                        inferior_crc = int(dados_recebidos[10:12],16) # Transforma de hexa para int

                        if parte_superior == superior_crc and parte_inferior == inferior_crc:
                            dados_recebidos = dados_recebidos[6:10]
                            dados_recebidos = int(dados_recebidos, 16)
                            # Separando em duas partes (0x01 e 0x00)
                            hex_part1 = dados_recebidos >> 8  # Primeiros 8 bits
                            hex_part2 = dados_recebidos & 0xFF  # Últimos 8 bits
                            result=0
                            if input < 9:
                                test = 0x01*( pow(2,input-1) )
                                result = ( (hex_part1 & (test))  )
                                result = result>>(input-1)
                                # if result > 2:
                                #     result=1
                            else:
                                test = 0x01*( pow(2,(input-8)-1) )
                                result = ( (hex_part2 & (test))  )
                                result = result>>((input-8)-1)

                            return result
                        else:
                            if i > 1:
                                self.reset_serial()
                            # return -1
                    else:
                        if i > 1:
                            self.reset_serial()
                    
                except:
                    print("Erro de comunicação")
                    return -1 # Indica erro de alguma natureza....
            return -1


        return 0
    
    def wp_8025(self, adr, out, on_off):
        dados_recebidos = None
        mask = 0
        if adr == self.ADR_1:
            mask = self.valor_saida_esquerdo
        elif adr == self.ADR_2:
            mask = self.valor_saida_direito
        elif adr == self.ADR_3:
            mask = self.valor_saida_geral

        if (adr == self.ADR_1 or adr == self.ADR_2 or adr == self.ADR_3) and (on_off==1):  # Corrigindo a condição
            id_loc = hex(adr)[2:]
            id_loc = id_loc.zfill(2).upper()

            # Deslocando 1 para a esquerda pelo número de bits especificado em out
            if out < 9:
                out_loc = (1 << (out-1+8)) | (mask)
                mask = out_loc
                
                out_val_h = (out_loc) & 0xff
                out_val_l = (out_loc>>8) & 0xff
            else:
                out_loc = 1 << (out-1-8) | (mask)
                mask = out_loc

                out_val_h = (out_loc) & 0xff 
                out_val_l = (out_loc>>8) & 0xff

            if adr == self.ADR_1:
                self.valor_saida_esquerdo = mask
            elif adr == self.ADR_2:
                self.valor_saida_direito = mask
            elif adr == self.ADR_3:
                self.valor_saida_geral = mask

        elif (adr == self.ADR_1 or adr == self.ADR_2 or adr == self.ADR_3) and (on_off==0):
            id_loc = hex(adr)[2:]
            id_loc = id_loc.zfill(2).upper()
            out_loc = 0
            # Deslocando 1 para a esquerda pelo número de bits especificado em out
            if out < 9:
                out_loc = self.retorna_bit_desligar_0_8(adr,out)
                mask = out_loc
                
                out_val_h = (out_loc) & 0xff
                out_val_l = (out_loc>>8) & 0xff
            
            else:
                out_loc = self.retorna_bit_desligar_9_10(adr,out)
                mask = out_loc

                out_val_h = (out_loc) & 0xff 
                out_val_l = (out_loc>>8) & 0xff 

            if adr == self.ADR_1:
                self.valor_saida_esquerdo = mask
            elif adr == self.ADR_2:
                self.valor_saida_direito = mask
            elif adr == self.ADR_3:
                self.valor_saida_geral = mask 

        # Invertendo a ordem dos bits
        # out_bin = out_bin[::-1]

        # Convertendo para hexadecimal com 4 dígitos
        out_hex = hex(out_loc)[2:].zfill(4).upper()

        hex_text = f"{id_loc}0f0000001002{out_hex}"
        bytes_hex = bytes.fromhex(hex_text)  # Transforma em hexa

        crc_result = self.crc16_modbus(bytes_hex) # Retorna o CRC

        parte_superior = (crc_result >> 8) & 0xFF  # Desloca 8 bits para a direita e aplica a máscara 0xFF
        parte_inferior = crc_result & 0xFF        # Aplica a máscara 0xFF diretamente

        try:
            self.ser.write([adr,0x0f,0,0,0,16,2,out_val_l,out_val_h,parte_inferior,parte_superior])
            while self.ser.readable()==False:
                pass
            for i in range(3):
                dados_recebidos = self.ser.read(8)
                if dados_recebidos != b'':
                    dados_recebidos = dados_recebidos.hex()
                    hex_text = dados_recebidos[0:2]+dados_recebidos[2:4]+dados_recebidos[4:6]+dados_recebidos[6:8]+dados_recebidos[8:10]+dados_recebidos[10:12]
                    bytes_hex = bytes.fromhex(hex_text) # Transforma em hexa
                    crc_result = self.crc16_modbus(bytes_hex) # Retorna o CRC

                    parte_superior = (crc_result >> 8) & 0xFF  # Desloca 8 bits para a direita e aplica a máscara 0xFF
                    parte_inferior = crc_result & 0xFF        # Aplica a máscara 0xFF diretamente

                    superior_crc = int(dados_recebidos[14:16],16) # Transforma de hexa para int
                    inferior_crc = int(dados_recebidos[12:14],16) # Transforma de hexa para int

                    if parte_superior == superior_crc and parte_inferior == inferior_crc:
                        dados_recebidos = dados_recebidos[14:16]
                        dados_recebidos = int(dados_recebidos,16)
                        # time.sleep(0.1)
                        return dados_recebidos
                    else:
                        if i > 1:
                            self.reset_serial()
                else:
                    if i > 1:
                        self.reset_serial()
        except Exception as e:
            print(f"Erro de comunicação: {e}")
            return -1 # Indica erro de alguma natureza....
            
    def desliga_lateral(self):
        self.wp_8025(self.dado.ADR_MOD1, 5, 0)
        self.wp_8025(self.dado.ADR_MOD1, 6, 0)
        self.wp_8025(self.dado.ADR_MOD1, 7, 0)
        self.wp_8025(self.dado.ADR_MOD1, 8, 0)
    
    def liga_lateral(self):
        self.wp_8025(self.dado.ADR_MOD1, 5, 1)
        self.wp_8025(self.dado.ADR_MOD1, 6, 1)
        self.wp_8025(self.dado.ADR_MOD1, 7, 1)
        self.wp_8025(self.dado.ADR_MOD1, 8, 1)

    def liga_principal(self):
        self.wp_8025(self.dado.ADR_MOD1, 1, 1)
        self.wp_8025(self.dado.ADR_MOD1, 2, 1)
        self.wp_8025(self.dado.ADR_MOD1, 3, 1)
        self.wp_8025(self.dado.ADR_MOD1, 4, 1)

    def desliga_principal(self):
        self.wp_8025(self.dado.ADR_MOD1, 1, 0)
        self.wp_8025(self.dado.ADR_MOD1, 2, 0)
        self.wp_8025(self.dado.ADR_MOD1, 3, 0)
        self.wp_8025(self.dado.ADR_MOD1, 4, 0)

    def desabilita_cortina_luz(self):
        self.wp_8025(self.dado.ADR_MOD2, 5, 1)

    def habilita_cortina_luz(self):
        self.wp_8025(self.dado.ADR_MOD2, 5, 0)

    def liga_marca(self):
        self.wp_8025(self.dado.ADR_MOD2, 8, 1)

    def desliga_marca(self):
        self.wp_8025(self.dado.ADR_MOD2, 8, 0)

    def aciona_marcacao(self):
        self.liga_marca()
        time.sleep(0.4)
        self.desliga_marca()
        self.sinaleiro_passou(1)
        self.sinaleiro_nao_passou(0)

    def sinaliza_nao_passou(self):
        self.sinaleiro_passou(0)
        self.sinaleiro_nao_passou(1)

    def desliga_sinalizacao(self):
        self.sinaleiro_passou(0)
        self.sinaleiro_nao_passou(0)

    def start_ateq(self):
        self.wp_8025(self.dado.ADR_MOD2, 2, 1)
        time.sleep(0.2)
        self.wp_8025(self.dado.ADR_MOD2, 2, 0)

    def sinaleiro_passou(self, liga_desliga):
        self.wp_8025(self.dado.ADR_MOD2, 3, liga_desliga)

    def sinaleiro_nao_passou(self, liga_desliga):
        self.wp_8025(self.dado.ADR_MOD2, 4, liga_desliga)

    def reset_serial(self):
        try:
            self.ser.close()
            time.sleep(0.5)  # Aguarda um curto período antes de reabrir a porta
            self.ser.open()
            self.ser.flushInput()  # Limpa o buffer de entrada após reabrir a porta
            print("Porta serial resetada com sucesso.")
        except Exception as e:
            print(f"Erro ao resetar a porta serial: {e}")

    def retorna_bit_desligar_0_8(self, adr, bit):
        out_loc = 0
        mask = 0

        if adr == self.ADR_1:
            mask = self.valor_saida_esquerdo
        elif adr == self.ADR_2:
            mask = self.valor_saida_direito
        elif adr == self.ADR_3:
            mask = self.valor_saida_geral

        if bit==1:
            out_loc = ( (1 << (bit-1+8)) | (mask) ) & 0xFEFF
        if bit==2:
            out_loc = ( (1 << (bit-1+8)) | (mask) ) & 0xFDFF
        if bit==3:
            out_loc = ( (1 << (bit-1+8)) | (mask) ) & 0xFBFF
        if bit==4:
            out_loc = ( (1 << (bit-1+8)) | (mask) ) & 0xF7FF
        if bit==5:
            out_loc = ( (1 << (bit-1+8)) | (mask) ) & 0xEFFF
        if bit==6:
            out_loc = ( (1 << (bit-1+8)) | (mask) ) & 0xDFFF
        if bit==7:
            out_loc = ( (1 << (bit-1+8)) | (mask) ) & 0xBFFF
        if bit==8:
            out_loc = ( (1 << (bit-1+8)) | (mask) ) & 0x7FFF  

        return out_loc   
    def retorna_bit_desligar_9_10(self, adr, bit):
        out_loc = 0
        mask = 0

        if adr == self.ADR_1:
            mask = self.valor_saida_esquerdo
        elif adr == self.ADR_2:
            mask = self.valor_saida_direito
        elif adr == self.ADR_3:
            mask = self.valor_saida_geral

        if bit==9:
            out_loc = ( (1 << (bit-1-8)) | (mask) ) & 0xFFFE
        if bit==10:
            out_loc = ( (1 << (bit-1-8)) | (mask) ) & 0xFFFD
        if bit==11:
            out_loc = ( (1 << (bit-1-8)) | (mask) ) & 0xFFFB
        if bit==12:
            out_loc = ( (1 << (bit-1-8)) | (mask) ) & 0xFFF7
        if bit==13:
            out_loc = ( (1 << (bit-1-8)) | (mask) ) & 0xFFEF
        if bit==14:
            out_loc = ( (1 << (bit-1-8)) | (mask) ) & 0xFFDF
        if bit==15:
            out_loc = ( (1 << (bit-1-8)) | (mask) ) & 0xFFBF
        if bit==16:
            out_loc = ( (1 << (bit-1-8)) | (mask) ) & 0xFF7F

        return out_loc 

if __name__ == '__main__':
    # import time
    io = IO_MODBUS()
    adr = 1

    # for i in range(1,17):
    #     io.wp_8027(adr,i,1)
    #     time.sleep(0.2)
    # for i in range(1,17):
    #     io.wp_8027(adr,i,0)
    #     time.sleep(0.2)
    cmd = ""
    while cmd != "q":
        adr = input("Digite o endereço do dispositivo.\n")
        cmd = input("Digite a saida que queira testar.\n")
        on_of = input("Digite 1 para ligar ou 0 para desligar.\n")
        try:

            io.wp_8025(int(adr),int(cmd),int(on_of))
            print(f"A saida {int(cmd)} foi acionada.")
        except:
            if cmd != "q":
                print("Digite um número válido.")
        
        # print(f"Entradas:\n1: {io.entradas_wp8026['in_1']}\n2: {io.entradas_wp8026['in_2']}\n3: {io.entradas_wp8026['in_3']}\n4: {io.entradas_wp8026['in_4']}\n5: {io.entradas_wp8026['in_5']}\n6: {io.entradas_wp8026['in_6']}\n7: {io.entradas_wp8026['in_7']}\n8: {io.entradas_wp8026['in_8']}\n")
        time.sleep(1)