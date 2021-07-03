from config import CONFIG

class BoxList():

    def __init__(self, gap_num, gap_offset, box_vector, camera):
        
        self.gap_num = gap_num
        self.gap_offset = gap_offset
        self.boxes = []
        self.x = None  # x position of box list
        self.gap_mid = None  # y position of the middle of the box list's gap

        for i in range(len(box_vector)):
            if box_vector[i] == 1:
                box = [CONFIG['WIDTH'] + camera, i * 60, gap_num, gap_offset]
                self.boxes.append(box)

        self.x = CONFIG['WIDTH'] + camera
        self.gap_mid = (gap_offset + gap_num / 2) * 60
