import cv2

cap = cv2.VideoCapture(0)
if cap.isOpened():
    ret, img = cap.read()
    if ret:
        cv2.imwrite('sample.jpg', img)

else:
    print("No camera!")

cap.release()
