# Steps explained in sequence:

## 1. Process threat and bag image:
- This step involves conversion of RGB image to binary image with a selected threshold for **contour detection**.
- Rotating threat object to 45 degrees.
- Morphological operation - **Closing** is applied to fill the holes in the binary image objects to eliminate small noisy contours.

## 2. Contour detection:
 - Contours are extracted to get the bounding box parameters for the bag and threat objects which are later used for cutting,scaling and locating threat object inside bag.
 - **Opencv contour detection algorithm** outputs list of contours in the form of numpy arrays.
 - Out of this largest contour is chosen as in this case it represents bag and threat objects.
 
 ## 3. Bounding box extraction:
 - After getting largest contour, using **OpenCv's cv2.rectangle()** function bounding box parameters: **height,width,top x coordinate,top y coordinate** for threat and bag are extracted.
 - Using this parameters, threat object is hashed from its image.
 
## 4. Scaling threat object:
- Threat object is scaled down with respect to bag so that it doesn't go out of it.
- First the scaled height and width of threat object relative to bag is calculated according below pseudo code.
```
  if bag.dim/threat_object.dim<=1
    scaled_threat_dim = int(bag.dim/threat_object.dim*scale_factor_relative_to_bag*threat_object.dim)
  else 
    scale = scale_factor_relative_to_bag/(threat_object.dim/bag.dim)
    scaled_threat_dim = int(scale*threat_object.dim)
```
- Then using **pad and resize fucntion** the threat object is scaled down with scaled threat dimensions without causing any change in aspect ratio of it.

## 5. Locating threat object:
- The scaled threat object is padded to the size of background image in such a way that it gets located inside the bag.
- Pad dimension for the scaled threat object is calculated according below expression.
```
   Pad dimension  = Bag image dimension - scaled threat object dimension.
```
- Then the range for upper,down,left,right pad factors are calculated after solving below mathematical expression.
```
   Pad factor(upper/left) + Pad factor(down/right) = Pad dimension --------- Eq-1
   Pad factor(upper/left) > top corner(x/y) --------- Eq-2
   Pad factor(down/right) < top corner(x/y) + bag dimension(height/width)  --------- Eq-3
   
   After solving above equation, we get;
   top corner(x/y) < Pad factor(upper/left) < (top corner(x/y) + bag dimension(height/width)) - Pad dimension  
```
- Then the above calcualted range is iterated till the threat object lies inside the bag. This is validated by below expression.
```
    binary mask of scaled and added threat object  = mask (Let's say) is derived -- (1)
    Then background image mask relative threat object is derived according to: binary_background_mask*mask
    Then sum of number of 1 is calculated and compared, if it is equal then its inside the bag else not.
```

## Combining bag and located threat image:
- They are comebined using below expression :
```
   output = 0.6*background_bag_image + 0.4*located_threat_image
```

