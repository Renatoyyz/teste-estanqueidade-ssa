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
        self.CORTINA_LUZ = 10
        self.BOTAO_EMERGENCIA = 23
        self.BOT_ACIO_E = 22
        self.BOT_ACIO_D = 24
        try:
            import RPi.GPIO as GPIO
            self.GPIO = GPIO
        except ImportError:
            print("RPi.GPIO not found. Using fake GPIO.")
            self.GPIO = FakeRPiGPIO()

        self.GPIO.setmode(self.GPIO.BCM)
        self.GPIO.setwarnings(False)

        self.GPIO.setup(self.BOT_ACIO_E, self.GPIO.IN, pull_up_down=self.GPIO.PUD_UP)
        self.GPIO.setup(self.BOT_ACIO_D, self.GPIO.IN, pull_up_down=self.GPIO.PUD_UP)

        self.GPIO.setup(self.CORTINA_LUZ, self.GPIO.IN, pull_up_down=self.GPIO.PUD_UP)
        self.GPIO.setup(self.BOTAO_EMERGENCIA, self.GPIO.IN, pull_up_down=self.GPIO.PUD_UP)

    @property
    # off_app
    def bot_acio_e(self):
        return self.GPIO.input(self.BOT_ACIO_E)

    @property
    def bot_acio_d(self):
        return self.GPIO.input(self.BOT_ACIO_D)

    @property
    def bot_emergencia(self):
        return self.GPIO.input(self.BOTAO_EMERGENCIA)

    @property
    def cortina_luz(self):
        return self.GPIO.input(self.CORTINA_LUZ)
    
    
class IO_MODBUS:
    def __init__(self):
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

        # Repete-se os comandos em decimal com os devidos bytes de CRC
        # self._serial.flush()
        self.ser.write([adr,0x0f,0,0,0,16,2,out_val_l,out_val_h,parte_inferior,parte_superior])
        while self.ser.readable()==False:
            pass
        dados_recebidos = self.ser.read(8)
        try:
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
                return -1
        except:
            return -1 # Indica erro de alguma natureza....
        
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

            # Repete-se os comandos em decimal com os devidos bytes de CRC
            # self._serial.flush()
            self.ser.write([adr,2,0,0,0,16,parte_inferior, parte_superior])
            while self.ser.readable()==False:
                pass
            dados_recebidos = self.ser.read(7)

            try:
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
                    return -1
            except:
                return -1 # Indica erro de alguma natureza....


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

        # Repete-se os comandos em decimal com os devidos bytes de CRC
        # self._serial.flush()
        self.ser.write([adr,0x0f,0,0,0,16,2,out_val_l,out_val_h,parte_inferior,parte_superior])
        while self.ser.readable()==False:
            pass
        dados_recebidos = self.ser.read(8)
        try:
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
                return -1
        except:
            return -1 # Indica erro de alguma natureza....

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
        
        print(f"Entradas:\n1: {io.entradas_wp8026['in_1']}\n2: {io.entradas_wp8026['in_2']}\n3: {io.entradas_wp8026['in_3']}\n4: {io.entradas_wp8026['in_4']}\n5: {io.entradas_wp8026['in_5']}\n6: {io.entradas_wp8026['in_6']}\n7: {io.entradas_wp8026['in_7']}\n8: {io.entradas_wp8026['in_8']}\n")
        time.sleep(1)