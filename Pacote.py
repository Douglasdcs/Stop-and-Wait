class Pacote:

    def __init__(self):
        self.num_seq = None             # Número de sequência do pacote
        self.data = None                # Dados do pacote
        self.sender_adress = None       # Tupla com porta e IP de origem
        self.receiver_adress = None     # Endereço de destino
        self.sended = False             # Situação
        self.received = False           # Ele está em qual lado
        self.sended_time = None         # Hora do envio
        self.received_time = None       # Hora de chagada
        self.last = False               # Flag que indica  fim da transmissão

    def get_num_seq(self):
        return self.num_seq

    def set_num_seq(self, num_seq):
        self.num_seq = num_seq

    def get_dados(self):
        return self.data

    def set_dados(self, data):
        self.data = data

    def get_sender_adress(self):
        return self.sender_adress

    def set_sender_adress(self, adress):
        self.sender_adress = adress

    def get_receiver_adress(self):
        return self.sender_adress

    def set_receiver_adress(self, adress):
        self.receiver_adress = adress

    def get_sended(self):
        return self.sended

    def set_sended(self, value):
        self.sended = value

    def get_received(self):
        return self.sended

    def set_received(self, value):
        self.received = value

    def get_sended_time(self):
        return self.sended_time

    def set_sended_time(self, time):
        self.sended_time = time

    def get_received_time(self):
        return self.received_time

    def set_received_time(self, time):
        self.received_time = time

    def get_last(self):
        return self.last

    def set_last(self, value):
        self.last = value

    def get_rtt(self):
        return self.received_time - self.sended_time
