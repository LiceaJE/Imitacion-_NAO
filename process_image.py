import math
import time
import cv2
import numpy as np
import mediapipe as mp

MIRROR_MODE = True      # True: tu brazo derecho -> brazo izquierdo del NAO (como espejo)
FLIP_DEPTH = False      # Pon True si adelante/atras salen invertidos
MIN_VISIBILITY = 0.5    # Debajo de esto se ignora el brazo
SMOOTHING = 0.5         # 0 = sin suavizar, 0.8 = muy suave pero con mas retraso

_mp_pose = mp.solutions.pose
_L = _mp_pose.PoseLandmark
_pose = _mp_pose.Pose(model_complexity=0, smooth_landmarks=True,
                      min_detection_confidence=0.5, min_tracking_confidence=0.5)

ARM_POINTS = {"right": (_L.RIGHT_SHOULDER, _L.RIGHT_ELBOW, _L.RIGHT_WRIST),
              "left":  (_L.LEFT_SHOULDER,  _L.LEFT_ELBOW,  _L.LEFT_WRIST)}
OUT_SIGN = {"right": -1.0, "left": 1.0}  # hacia afuera del cuerpo en el eje x de la imagen

_last_pitch = {"left": 0.0, "right": 0.0}
_smoothed = [float("nan")] * 6


def _unit(v):
    n = np.linalg.norm(v)
    return v / n if n > 1e-6 else None


def _arm_to_nao(world, person_side):
    pts = [world[i] for i in ARM_POINTS[person_side]]
    if any(p.visibility < MIN_VISIBILITY for p in pts):
        return None
    sh, el, wr = pts

    def body(a, b):
        d = np.array([b.x - a.x, b.y - a.y, b.z - a.z])
        fwd = d[2] if FLIP_DEPTH else -d[2]
        return np.array([fwd, OUT_SIGN[person_side] * d[0], -d[1]])  # adelante, afuera, arriba

    upper = _unit(body(sh, el))
    fore = _unit(body(el, wr))
    if upper is None or fore is None:
        return None

    nao_side = "left" if (person_side == "right") == MIRROR_MODE else "right"
    fwd, out, up = upper
    uy = out if nao_side == "left" else -out

    roll = math.asin(max(-1.0, min(1.0, uy)))
    if math.cos(roll) > 0.35:
        pitch = math.atan2(-up, fwd)
        _last_pitch[nao_side] = pitch
    else:
        # Brazo casi en T: el pitch es inestable, se mantiene el ultimo valido
        pitch = _last_pitch[nao_side]

    bend = math.acos(max(-1.0, min(1.0, float(np.dot(upper, fore)))))
    elbow = -bend if nao_side == "left" else bend
    return nao_side, (pitch, roll, elbow)


def analyze(img):
    """Devuelve (resultado_mediapipe, [Lpitch, Lroll, Lcodo, Rpitch, Rroll, Rcodo]) en radianes.
    Los brazos que no se ven salen como nan."""
    res = _pose.process(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    raw = [float("nan")] * 6
    if res.pose_world_landmarks is not None:
        world = res.pose_world_landmarks.landmark
        for person_side in ("right", "left"):
            out = _arm_to_nao(world, person_side)
            if out:
                nao_side, vals = out
                base = 0 if nao_side == "left" else 3
                raw[base:base + 3] = list(vals)
    for i, v in enumerate(raw):
        if math.isnan(v):
            _smoothed[i] = float("nan")
        elif math.isnan(_smoothed[i]):
            _smoothed[i] = v
        else:
            _smoothed[i] = SMOOTHING * _smoothed[i] + (1 - SMOOTHING) * v
    return res, list(_smoothed)


def img_to_angle(img, opWrapper, file_index, log_time_start, log_opcomp, log_convangle):
    res, angles = analyze(img)
    t = time.time()
    log_opcomp.append((file_index, log_time_start, t, None))
    log_convangle.append((file_index, t, t, angles))
    return angles