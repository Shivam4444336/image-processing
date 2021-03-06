

import cv2
import numpy as np
import matplotlib.pyplot as plt
import tensorflow as tf
import random
import scipy
import os

class Task:
  def __init__(self,background_images_directory,threat_images_directory,output_directory_path):
    self.background_images_directory = background_images_directory
    self.threat_images_directory = threat_images_directory
    self.output_directory_path = output_directory_path
    self.scale_factor_relative_to_bag = 0.3
    list_of_background_images = os.listdir(background_images_directory)
    list_of_threat_images = os.listdir(threat_images_directory)
    self.iterator = zip(list_of_background_images,list_of_threat_images)
    self.background_binary_threshold = 225
  
  def execute(self):
    i=1
    for background,threat in self.iterator:
      threat_image = cv2.cvtColor(cv2.imread(self.threat_images_directory+'/'+threat),cv2.COLOR_BGR2RGB)
      background_image = cv2.cvtColor(cv2.imread(self.background_images_directory+'/'+background),cv2.COLOR_BGR2RGB)
      self.calculate_bounding_box_parameters_for_background(background_image)
      scaled_threat_object = self.process_and_scale_threat_image(threat_image)
      output_image = self.locate_threat_object(background_image,scaled_threat_object)
      cv2.imwrite(self.output_directory_path+'/'+'output_image_'+str(i)+'.png',cv2.cvtColor(output_image,cv2.COLOR_RGB2BGR))
      i+=1
  


  def locate_threat_object(self,background_image,scaled_threat_object):
    background_height = background_image.shape[0]
    background_width = background_image.shape[1]
    pad_height_size = background_height - scaled_threat_object.shape[0]
    pad_width_size = background_width - scaled_threat_object.shape[1]
    top_coordinate_height = self.bag_dim['y']
    top_coordinate_width = self.bag_dim['x']
    bag_height = self.bag_dim['h']
    bag_width = self.bag_dim['w']
    #calculate upper and down pad factor for height
    for upper_factor in range(top_coordinate_height+1,(top_coordinate_height+bag_height)-pad_height_size):
      down_factor = pad_height_size - upper_factor
      #calculate left and right pad factor for width
      for left_factor in range(top_coordinate_width+1,(top_coordinate_width+bag_width)-pad_width_size):
        right_factor = pad_width_size - left_factor
        located_threat_object = np.pad(scaled_threat_object,((upper_factor,down_factor),(left_factor,right_factor),(0,0)))
        reduced = np.max(located_threat_object,-1)
        mask = np.where(reduced != 0,1,0)
        background_mask = self.background_binary_1*mask
        if np.sum(mask) == np.sum(background_mask):
          break
        else:
          continue 
    #combine background image with threat image
    output_image = np.uint8(0.6*background_image) + np.uint8(0.4*located_threat_object)
    return output_image



  
  def calculate_bounding_box_parameters_for_background(self,background_image):
    
    #convert background image to binary
    background_gray = cv2.cvtColor(background_image, cv2.COLOR_BGR2GRAY)
    _,background_binary = cv2.threshold(background_gray,self.background_binary_threshold,255,cv2.THRESH_BINARY_INV)
    
    #this will be used while locating threat object inside background
    self.background_binary_1 = np.where(background_binary==255,1,0)

    #Apply closing operation to binary image to eliminate small contours
    kernel = np.ones((5,5),np.uint8)
    closed_background_binary = cv2.morphologyEx(background_binary, cv2.MORPH_CLOSE, kernel)

    #find contour of background image and bounding box parameters
    contours, _ = cv2.findContours(closed_background_binary, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
    contour_area = []
    for cnt in contours:
      contour_area.append(cv2.contourArea(cnt))
    largest_contour = contours[np.argmax(np.array(contour_area))]
    x_b,y_b,w_b,h_b = cv2.boundingRect(largest_contour)
    self.bag_dim = {'x':x_b,'y':y_b,'w':w_b,'h':h_b}
  
  def process_and_scale_threat_image(self,threat_image):

    #rotate threat image by 45 degree
    threat_image = scipy.ndimage.rotate(threat_image,45)

    #Convert threat image to binary image
    threat_gray = cv2.cvtColor(threat_image, cv2.COLOR_BGR2GRAY)
    threat_gray = np.where(threat_gray==0,255,threat_gray)
    _,threat_binary = cv2.threshold(threat_gray,245,255,cv2.THRESH_BINARY_INV)

    #Apply closing operation to binary image to eliminate small contours
    kernel = np.ones((5,5),np.uint8)
    closed_threat_binary = cv2.morphologyEx(threat_binary, cv2.MORPH_CLOSE, kernel)

    #find contour of threat image and bounding box parameters
    contours, _ = cv2.findContours(closed_threat_binary, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
    contour_area = []
    for cnt in contours:
      contour_area.append(cv2.contourArea(cnt))
    largest_contour = contours[np.argmax(np.array(contour_area))]
    x,y,w,h = cv2.boundingRect(largest_contour)

    #Extract threat object from threat image
    extracted_threat_object = threat_image[y:y+h,x:x+w]

    #scale threat object in background image
    masked_extracted_threat_object  = extracted_threat_object*np.expand_dims(np.where(closed_threat_binary[y:y+h,x:x+w]==255,1,0),-1)
    threat_width = masked_extracted_threat_object.shape[1]
    threat_height = masked_extracted_threat_object.shape[0]
    #scale height
    if self.bag_dim['h']/threat_height <= 1:
      scaled_threat_height = int(self.bag_dim['h']/threat_height*self.scale_factor_relative_to_bag*threat_height)
    else:
      scale = self.scale_factor_relative_to_bag/(threat_height/self.bag_dim['h'])
      scaled_threat_height = int(scale*threat_height)
    #scale width
    if self.bag_dim['w']/threat_width <= 1:
      scaled_threat_width = int(self.bag_dim['w']/threat_width*self.scale_factor_relative_to_bag*threat_width)
    else:
      scale = self.scale_factor_relative_to_bag/(threat_width/self.bag_dim['w'])
      scaled_threat_width = int(scale*threat_width)
    scaled_threat_object_tensor = tf.image.resize_with_pad(masked_extracted_threat_object,scaled_threat_height,scaled_threat_width)

    scaled_threat_object_numpy = scaled_threat_object_tensor.numpy().astype(np.uint8)

    return scaled_threat_object_numpy



  
'''
 To run this script provide below arguments in below Task constructor.
 first argument: Background image directory path
 second argument: Threat image directory path
 third argument: Output image directory path (create an empty directory for output images)

 On running this script, at the end of execution output will be saved to specified output directory.
'''
task_object = Task('/content/drive/MyDrive/Baggage AI/background_images','/content/drive/MyDrive/Baggage AI/threat_images','/content/drive/MyDrive/BaggageAIoutput')
task_object.execute()
