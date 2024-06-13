import wave
import matplotlib.pyplot as plt
import struct
import numpy as np
import pyaudio

def swap_bits(number):
    msb = number >> 32
    lsb = number & ((1 << 32) - 1)
    swapped_num = (lsb << 32) | msb
    result = swapped_num ^ number
    return result

def entropy(labels, base=None):
    value, counts = np.unique(labels, return_counts=True)
    norm_counts = counts / counts.sum()
    base = 2 if base is None else base
    return -(norm_counts * np.log(norm_counts)/np.log(base)).sum()

def hist_input(A):
    r = []
    mask = 0b00000111
    for v in A:
        r.append(v & mask)
        
    r24 = []
    for i in range(0, len(r), 8):
        temp = r[i] << 21 | r[i+1] << 18 | r[i+2] << 15 | r[i+3] << 12 | r[i+4] << 9 | r[i+5] << 6 | r[i+6] << 3 | r[i+7]
        r24.append(temp)
        
    r_new = []
    for i in range(len(r24)):
        r_new.append(r24[i] & 0b111111110000000000000000 >> 16)
        r_new.append(r24[i] & 0b000000001111111100000000 >> 8)
        r_new.append(r24[i] & 0b000000000000000011111111)
        
    total_occurrences = len(r_new)
    hist, bins = np.histogram(r_new, bins=256, density=False)
    bin_widths = bins[1] - bins[0]
    hist = hist / total_occurrences
    
    # plt.bar(bins[:-1], hist, width=bin_widths)
    # plt.title("Histogram")
    # plt.xlabel("Value")
    # plt.ylabel("Probability")
    # plt.show()
    
    return r

def generate_random_data():
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 44100

    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK)

    print("Nagrywanie...")

    frames = []
    num_frames_to_record = 256000 // CHUNK

    for _ in range(num_frames_to_record):
        data = stream.read(CHUNK)
        frames.append(data)

    print("Nagrywanie zakończone.")

    stream.stop_stream()
    stream.close()
    p.terminate()

    audio_data = np.frombuffer(b''.join(frames), dtype=np.uint16)
    audio_data = np.frombuffer(audio_data, dtype=np.uint8)

    n = 256000 // 256 * 8
    A = [bits for bits in audio_data]

    if len(A) < 256000:
        raise ValueError("The audio file is too short")

    hist_input(A)

    entropy_value = entropy(A, base=2)
    #print('Entropy before processing:', entropy_value)

    r = []
    mask = 0b00000111
    for v in A:
        r.append(v & mask)

    x = [[0.141592, 0.653589, 0.793238, 0.462643, 0.383279, 0.502884, 0.197169, 0.399375]]
    c = 0

    def fT(x, alpha):
        if 0 <= x < 0.5:
            return alpha * x
        elif 0.5 <= x <= 1:
            return alpha * (1 - x)
        else:
            raise ValueError("x must be in range of [0, 1]")

    z = [0, 0, 0, 0, 0, 0, 0, 0]
    O = []
    y = 0

    while len(O) <= 256000:
        for i in range(8):
            t = len(x) - 1
            x[t][i] = ((0.071428571 * r[y]) + x[t][i]) * 0.666666667
            c += 1
        for t in range(2):
            for i in range(8):
                try:
                    x[t+1][i] = (1 - 0.1) * fT(x[t][i], 1) + 0.1/2 * (fT(x[t][(i+1)%8], 1)) + fT(x[t][(i-1)%8], 1)
                except:
                    x.append([0,0,0,0,0,0,0,0])
                    x[t+1][i] = (1 - 0.1) * fT(x[t][i], 1) + 0.1/2 * (fT(x[t][(i+1)%8], 1)) + fT(x[t][(i-1)%8], 1)
        for i in range(8):
            word = struct.pack('d', x[2][i])
            int_value = int.from_bytes(word, byteorder='big', signed=False)
            z[i] = int_value
            x[0][i] = x[2][i]
        for i in range(4):
            z[i] = int(z[i]) ^ swap_bits(int(z[i+4]))
        O.append(z[0] + z[1]*256 + z[2]*pow(2,16) + z[3]*pow(2,24))
        y += 1

    output = []
    for j in range(len(O) - 1):
        for i in range(0, 256, 8):
            byte = (O[j] >> (256 - (i + 8))) & 0xFF
            if byte != 0:
                output.append(byte)

    hist, bins = np.histogram(output, bins=256, density=True)
    bin_widths = bins[1] - bins[0]

    # plt.bar(bins[:-1], hist, width=bin_widths)
    # plt.title('Histogram')
    # plt.xlabel('Value')
    # plt.ylabel('Probability')
    # plt.show()

    entropy_value = entropy(output, base=2)
    #print('Entropy:', entropy_value)

    #print(len(output))
    with open('output4.txt', 'w') as file:
        file.write(str(output))

    with open('output4.bin', 'wb') as file:
        for byte in output:
            file.write(byte.to_bytes(1, byteorder='big'))

    return output

if __name__ == "__main__":
    generate_random_data()
