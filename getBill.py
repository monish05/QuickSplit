from google.cloud import vision
import numpy as np
import cv2
from matplotlib import pyplot as plt
import re
import pandas as pd

class GetSplitDetails():
    def __init__(self, image_path):
        self.image_path = image_path
    

    def detect_text(self):
        path = self.image_path

        client = vision.ImageAnnotatorClient.from_service_account_file('gkey.json')

        with open(path, "rb") as image_file:
            content = image_file.read()

        image = vision.Image(content=content)

        response = client.text_detection(image=image)
    #     print(response)
        texts = response.text_annotations

        final = {}
        for text in texts:
            if text.description not in final:
                poly = []
                for i in text.bounding_poly.vertices:
                    poly.append([i.x, i.y])
                final[text.description] = [poly]
            else:
                poly = []
                for i in text.bounding_poly.vertices:
                    poly.append([i.x, i.y])
                final[text.description].append(poly)


        return final

    def arranged_list(self):
        output = self.detect_text()
        output.pop(list(output.keys())[0])
        final = []
        for i in output:
            if len(output[i]) == 1:
                yi1 = output[i][0][0][1]
                yi2 = output[i][0][1][1]
                yi3 = output[i][0][2][1]
                yi4 = output[i][0][2][1]

        #         print(yi1, yi2, yi3, yi4)
                something = []
                interval = 5
                for j in output:
                    if len(output[j]) == 1: 
                        yj1 = output[j][0][0][1]
                        yj2 = output[j][0][1][1]
                        yj3 = output[j][0][2][1]
                        yj4 = output[j][0][2][1]

                        if (yi1>= yj1-interval and yi1 <= yj1+interval) and (yi2>= yj2-interval and yi2 <= yj2+interval) and (yi3>= yj3-interval and yi3 <= yj3+interval) and (yi4>= yj4-interval and yi4 <= yj4+interval):
                            something.append(j)
                    else:
                        for q in output[j]:
                            yj1 = q[0][1]
                            yj2 = q[1][1]
                            yj3 = q[2][1]
                            yj4 = q[2][1]

                            if (yi1>= yj1-interval and yi1 <= yj1+interval) and (yi2>= yj2-interval and yi2 <= yj2+interval) and (yi3>= yj3-interval and yi3 <= yj3+interval) and (yi4>= yj4-interval and yi4 <= yj4+interval):
                                something.append(j)


        #         print(" ".join(something))

                if " ".join(something) not in final:
                    final.append(" ".join(something))

        return final

    def get_price_only(self):
        final = self.arranged_list()
        pattern = r'\d+\.\d+'
        matching_elements = [element for element in final if re.search(pattern, element)]

        modified_data = [re.sub(pattern, '', element) for element in matching_elements]

        extracted_numbers = [float(match) for line in final for match in re.findall(pattern, line)]

        items=dict()
        for i in range(0,len(modified_data)):
            items[modified_data[i]]=extracted_numbers[i]

        return items

    def get_price_and_quantity(self):
        items = self.get_price_only()
        new_final = {}
        for i in items:
            smallest = 99
            for j in i.split(" "):
                try:
                    if int(j) < smallest:
                        smallest = int(j)
                except:
                    pass

            if smallest == 99:
                smallest = 1

            new_final[i] = [smallest, items[i]]

        dict_list = []
        for i in new_final:
            dict_list.append([i, new_final[i][0], new_final[i][1]])
            
        final_df = pd.DataFrame(dict_list, columns = ['Name', 'Quantity', 'Total_Price'])

        return final_df
            
        
        