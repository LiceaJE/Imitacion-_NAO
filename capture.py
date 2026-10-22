import os, time
import numpy as np
from naoqi import ALProxy

PATH = "/home/nao/imitate/buffer_images/"
video = ALProxy("ALVideoDevice", "127.0.0.1", 9559)
sub = video.subscribeCamera("imitate", 0, 1, 13, 10)  # cámara superior, 320x240, BGR, 10 fps
i = 0
try:
    while True:
        img = video.getImageRemote(sub)
        arr = np.frombuffer(img[6], dtype=np.uint8).reshape((img[1], img[0], 3))
        np.save(PATH + "image_{:06d}.npy".format(i), arr)
        old = PATH + "image_{:06d}.npy".format(i - 10)
        if os.path.exists(old):
            os.remove(old)
        i += 1
        time.sleep(0.1)
finally:
    video.unsubscribe(sub)