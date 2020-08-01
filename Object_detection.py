import torch,cv2,random,os,time
from PIL import Image
import torch.nn as nn
from torch.autograd import Variable
import numpy as np
import pickle as pkl
import argparse
import threading, queue
from torch.multiprocessing import Pool, Process, set_start_method
from darknet import Darknet
from imutils.video import WebcamVideoStream,FPS
# from camera import write
import win32com.client as wincl       #### Python's Text-to-speech (tts) engine for windows, multiprocessing
speak = wincl.Dispatch("SAPI.SpVoice")    #### This initiates the tts engine

torch.multiprocessing.set_start_method('spawn', force=True)
from torchvision import transforms as trans
##  Setting up torch for gpu utilization
if torch.cuda.is_available():
    torch.backends.cudnn.enabled = True 
    torch.backends.cudnn.benchmark = True
    torch.backends.cudnn.deterministic = True
    torch.set_default_tensor_type('torch.cuda.FloatTensor')

def letterbox_image(img, inp_dim):
    '''resize image with unchanged aspect ratio using padding'''
    img_w, img_h = img.shape[1], img.shape[0]
    w, h = inp_dim
    new_w = int(img_w * min(w/img_w, h/img_h))
    new_h = int(img_h * min(w/img_w, h/img_h))
    resized_image = cv2.resize(img, (new_w,new_h), interpolation = cv2.INTER_CUBIC)
    canvas = np.full((inp_dim[1], inp_dim[0], 3), 128)
    canvas[(h-new_h)//2:(h-new_h)//2 + new_h,(w-new_w)//2:(w-new_w)//2 + new_w,  :] = resized_image
    
    return canvas

def load_classes(namesfile):
    fp = open(namesfile, "r")
    names = fp.read().split("\n")[:-1]
    return names

def prep_image(img, inp_dim):
    """
    Prepare image for inputting to the neural network.
    Returns a Variable
    """
    orig_im = img
    dim = orig_im.shape[1], orig_im.shape[0]
    img = (letterbox_image(orig_im, (inp_dim, inp_dim)))
    img_ = img[:, :, ::-1].transpose((2, 0, 1)).copy()
    img_ = torch.from_numpy(img_).float().div(255.0).unsqueeze(0)
    return img_, orig_im, dim



class ObjectDetection:
    def __init__(self, id): 
        # self.cap = cv2.VideoCapture(id)
        # self.cap = WebcamVideoStream(src = id).start()
        self.cfgfile = "cfg/yolov4.cfg"
        self.weightsfile = "yolov4.weights"
        self.confidence = float(0.09)
        self.nms_thesh = float(0.2)
        self.num_classes = 80
        self.classes = load_classes('data/coco.names')
        self.colors = pkl.load(open("pallete", "rb"))
        self.model = Darknet(self.cfgfile)
        self.CUDA = torch.cuda.is_available()
        self.model.load_weights(self.weightsfile)
        self.width = 1280 #640#1280
        self.height = 720 #360#720
        self.id = id
        self.transform = trans.Compose([
                    trans.ToTensor(),
                    trans.Normalize([0.5, 0.5, 0.5], [0.5, 0.5, 0.5])
                ])
        print("Loading network.....")
        if self.CUDA:
            self.model.cuda()
        print("Network successfully loaded")

        self.model.eval()

    def main(self):
        frame = cv2.imread(id)
        try:
            img, orig_im, dim = prep_image(frame, 160)
            
            im_dim = torch.FloatTensor(dim).repeat(1,2)
            if self.CUDA:                            #### If you have a gpu properly installed then it will run on the gpu
                im_dim = im_dim.cuda()
                img = img.cuda()
            frame = cv2.imread(self.id)
            


            output = self.model(img)
            
            from tool.utils import post_processing,plot_boxes_cv2
            bounding_boxes = post_processing(img,self.confidence, self.nms_thesh, output)
            frame = plot_boxes_cv2(frame, bounding_boxes[0], savename= None, class_names=self.classes, color = None, colors=self.colors)

        except:
            pass
        
        cv2.imwrite('IMG_0748-1.JPG',frame)
        torch.cuda.empty_cache()

            

if __name__ == "__main__":
    id = "IMG_0748.JPG"
    ObjectDetection(id).main()