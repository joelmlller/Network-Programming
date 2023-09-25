# Mike Brandin CPSC 3600 Section 91005 10/31/2021

from network_simulator import NetworkSimulator, Packet, EventEntity
from enum import Enum
from struct import pack, unpack, unpack_from

class GBNHost():

    # The __init__ method accepts:
    # - a reference to the simulator object
    # - the value for this entity (EntityType.A or EntityType.B)
    # - the interval for this entity's timer
    # - the size of the window used for the Go-Back-N algorithm
    def __init__(self, simulator, entity, timer_interval, window_size):
        
        # These are important state values that you will need to use in your code
        self.simulator = simulator
        self.entity = entity
        
        self.unACKed_buffer = {}
        self.app_layer_buffer = [] 

        self.last_ack = self.make_ACKpkt(-1)

        # Sender properties
        self.timer_interval = timer_interval        # The duration the timer lasts before triggering
        self.window_size = window_size              # The size of the seq/ack window
        self.window_base = 0                        # The last ACKed packet. This starts at 0 because no packets 
                                                    # have been ACKed
        self.next_seq_num = 0                       # The SEQ number that will be used next
        self.expected_seq_num = 0


    ###########################################################################################################
    ## Core Interface functions that are called by Simulator

    # This function implements the SENDING functionality. It should implement retransmit-on-timeout. 
    # Refer to the GBN sender flowchart for details about how this function should be implemented
    def receive_from_application_layer(self, payload):
        if (self.next_seq_num < (self.window_base + self.window_size)):
            self.unACKed_buffer[self.next_seq_num] = self.make_DATApkt(self.next_seq_num, payload)
            self.simulator.pass_to_network_layer(self.entity, self.unACKed_buffer[self.next_seq_num], False)
            if (self.window_base == self.next_seq_num):
                self.simulator.start_timer(self.entity, self.timer_interval)
            self.next_seq_num += 1
        else:
            self.app_layer_buffer.append(payload)


    # This function implements the RECEIVING functionality. This function will be more complex that
    # receive_from_application_layer(), it includes functionality from both the GBN Sender and GBN receiver
    # FSM's (both of these have events that trigger on receive_from_network_layer). You will need to handle 
    # data differently depending on if it is a packet containing data, or if it is an ACK.
    # Refer to the GBN receiver flowchart for details about how to implement responding to data pkts, and
    # refer to the GBN sender flowchart for details about how to implement responidng to ACKs
    def receive_from_network_layer(self, byte_data):
        try:
            header = unpack("!HiHI", byte_data[:12])
        except:
            self.simulator.pass_to_network_layer(self.entity, self.last_ack, True)
            return
        if (self.is_corrupt(byte_data)):
            self.simulator.pass_to_network_layer(self.entity, self.last_ack, True)
            return    
        elif (header[0] == 0): #received ack # not corrupt
            ack_num = header[1]
            if ack_num >= self.window_base:

                if self.window_base < ack_num:
                    i = self.window_base
                    while i <= ack_num and i in self.unACKed_buffer:
                        del self.unACKed_buffer[i]
                        i += 1

                self.window_base = ack_num + 1
                self.simulator.stop_timer(self.entity)

                if (self.window_base != self.next_seq_num):
                    self.simulator.start_timer(self.entity, self.timer_interval)
                while (len(self.app_layer_buffer) > 0 and self.next_seq_num < (self.window_base + self.window_size)):
                    payload = self.app_layer_buffer.pop()
                    self.unACKed_buffer[self.next_seq_num] = self.make_DATApkt(self.next_seq_num, payload)
                    self.simulator.pass_to_network_layer(self.entity, self.unACKed_buffer[self.next_seq_num], False)
                    if (self.window_base == self.next_seq_num):
                        self.simulator.start_timer(self.entity, self.timer_interval)
                    self.next_seq_num += 1
        else: #received data
            if (self.expected_seq_num == header[1]):
                if header[3] > 0:
                    try:
                        data = unpack("!%is"%header[3], byte_data[12:])[0].decode()
                    except:
                        self.simulator.pass_to_network_layer(self.entity, self.last_ack, True)
                        return
                self.simulator.pass_to_application_layer(self.entity, data)
                self.last_ack = self.make_ACKpkt(self.expected_seq_num)
                self.simulator.pass_to_network_layer(self.entity, self.last_ack, True)
                self.expected_seq_num += 1
            else:
                self.simulator.pass_to_network_layer(self.entity, self.last_ack, True)

    # This function is called by the simulator when a timer interrupt is triggered due to an ACK not being 
    # received in the expected time frame. All unACKHiHIed data should be resent, and the timer restarted
    def timer_interrupt(self):
        self.simulator.start_timer(self.entity, self.timer_interval) 
        for j in range(self.window_base, self.next_seq_num):
            self.simulator.pass_to_network_layer(self.entity, self.unACKed_buffer[j], False)
    # This function should check to determine if a given packet is corrupt. The packet parameter accepted
    # by this function should contain a byte array
    def is_corrupt(self, packet):
        if (self.compute_checksum(packet) == 0x0000):
            return False
        else:
            return True

    def compute_checksum(self, packet):
        if len (packet) % 2 == 1:
            packet = packet + bytes(1)
        
        summed_words = 0
        for i in range (0 , len(packet), 2) :
            word = packet [i] << 8 | packet [i+1]
            summed_words += word
            summed_words = (summed_words & 0xffff) + (summed_words >> 16)

        checksum = ~summed_words & 0xffff
        return checksum

    def make_ACKpkt(self, seq):

        format_string = '!HiHI'
        message = pack(format_string, 0, seq, 0, 0)
        checksum = self.compute_checksum(message)
        message = pack(format_string, 0, seq, checksum, 0)
        return message

    def make_DATApkt(self, seq, payload):

        format_string = '!HiHI' + str(len(payload.encode())) + 's' 
        message = pack(format_string, 128, seq, 0, len(payload.encode()), payload.encode())
        checksum = self.compute_checksum(message)
        message = pack(format_string, 128, seq, checksum, len(payload.encode()), payload.encode())
        return message