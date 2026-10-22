import os
import cv2
import numpy as np
import mediapipe as mp
import process_image

PATH = "buffer_images/"
SCALE = 3
LABELS = ["izq hombro-pitch", "izq hombro-roll", "izq codo",
          "der hombro-pitch", "der hombro-roll", "der codo"]
draw = mp.solutions.drawing_utils
conn = mp.solutions.pose.POSE_CONNECTIONS

print("Ventana abierta. Presiona 'q' sobre la ventana para salir.")
while True:
    files = sorted(os.listdir(PATH))
    if len(files) >= 4:
        try:
            img = np.load(PATH + files[-4])
        except Exception:
            img = None
        if img is not None:
            res, angles = process_image.analyze(img)
            if res.pose_landmarks is not None:
                draw.draw_landmarks(img, res.pose_landmarks, conn)
            img = cv2.resize(img, None, fx=SCALE, fy=SCALE)
            if res.pose_landmarks is None:
                cv2.putText(img, "NO SE DETECTA PERSONA", (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)
            for i, a in enumerate(angles):
                if np.isnan(a):
                    txt, color = LABELS[i] + ": no visible", (0, 0, 255)
                else:
                    txt, color = "%s: %d grados" % (LABELS[i], round(np.degrees(a))), (0, 255, 0)
                cv2.putText(img, txt, (10, 60 + 25 * i),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
            cv2.imshow("Lo que ve el NAO", img)
    if cv2.waitKey(30) & 0xFF == ord('q'):
        break
cv2.destroyAllWindows()
