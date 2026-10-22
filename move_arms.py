cat > /home/nao/imitate/move_arms.py << 'EOF'
# -*- coding: utf-8 -*-
import os
import math
import time
import numpy as np
from naoqi import ALProxy

PATH = "/home/nao/imitate/buffer_angles/"
BUFFER_LIMIT = 10
NTH_LAST = 2
SPEED = 0.4

motion = ALProxy("ALMotion", "127.0.0.1", 9559)

NAMES = ["LShoulderPitch", "LShoulderRoll", "LElbowRoll",
         "RShoulderPitch", "RShoulderRoll", "RElbowRoll"]
LIMITS = [(-119.5, 119.5), (-18, 76), (-88.5, -2),
          (-119.5, 119.5), (-76, 18), (2, 88.5)]


def use_angles(angles):
    names, values = [], []
    for i, a in enumerate(angles):
        if np.isnan(a):
            continue
        deg = max(LIMITS[i][0], min(LIMITS[i][1], math.degrees(float(a))))
        names.append(NAMES[i])
        values.append(math.radians(deg))
    if names:
        motion.setAngles(names, values, SPEED)
    return values


def main():
    motion.setStiffnesses("LArm", 1.0)
    motion.setStiffnesses("RArm", 1.0)
    for f in os.listdir(PATH):
        os.remove(PATH + f)
    print("Listo. Ctrl+C para detener.")
    previous = ""
    try:
        while True:
            files = sorted(os.listdir(PATH))
            if len(files) > BUFFER_LIMIT:
                os.remove(PATH + files[0])
            if len(files) >= NTH_LAST:
                filename = files[-NTH_LAST]
                if filename != previous:
                    previous = filename
                    try:
                        angles = np.load(PATH + filename)
                    except Exception:
                        continue
                    if len(angles) != 6:
                        continue
                    use_angles(angles)
                    print(filename + " " + str([int(round(math.degrees(float(a)))) if not np.isnan(a) else None for a in angles]))
            time.sleep(0.02)
    except KeyboardInterrupt:
        print("Detenido.")
        motion.setStiffnesses("LArm", 0.0)
        motion.setStiffnesses("RArm", 0.0)

main()
EOF