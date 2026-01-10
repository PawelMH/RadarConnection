import random
import numpy as np

class Decoder:
    def tlv_decode(self, type, value):
        #print(type)
        match type:
            case 1:
                return self.detected_points(value)
            case 2:
                return self.range_profile(value)
            case 3:
                return self.noise_profile(value)
            case 4:
                return self.azimuth_static_heatmap(value)
            case 5:
                return self.range_doppler_heatmap(value)
            case 6:
                return self.statistics(value)
            case _:
                raise(f"Invalid TLV Type of: {type}")

    def detected_points(self, value):
        # Read 4-byte header
        num_obj = int(np.frombuffer(value[0:2], dtype=np.uint16)[0])
        q_format_exp = int(np.frombuffer(value[2:4], dtype=np.uint16)[0])
        q_format = float(2.0 ** q_format_exp)

        data = []
        offset = 4  # Start after 4-byte header (numObj + qFormat)

        for i in range(num_obj):
            base = offset + 12 * i
            rangeIdx = int(np.frombuffer(value[base:base+2], dtype=np.uint16)[0])
            dopplerIdx = int(np.frombuffer(value[base+2:base+4], dtype=np.uint16)[0])
            peakVal = int(np.frombuffer(value[base+4:base+6], dtype=np.uint16)[0])
            x = float(np.frombuffer(value[base+6:base+8], dtype=np.int16)[0]) / q_format
            y = float(np.frombuffer(value[base+8:base+10], dtype=np.int16)[0]) / q_format
            z = float(np.frombuffer(value[base+10:base+12], dtype=np.int16)[0]) / q_format

            data.append([(rangeIdx, dopplerIdx, peakVal, x, y, z)])

        return data

    def range_profile(self,value):
        data = []
        for i in range(int(len(value)/2)):
            q9 = int(np.frombuffer(value[i*2:i*2 + 2], dtype=np.uint16)[0])
            data.append(q9)
        return data

    def noise_profile(self,value):
        return [random.randint(0,100)]

    def azimuth_static_heatmap(self,value):
        return [random.randint(0,100)]

    def range_doppler_heatmap(self,value):
        return [random.randint(0,100)]

    def statistics(self,value):
        return [random.randint(0,100)]