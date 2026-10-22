# Imitación de poses con NAO

Un NAO imita los movimientos de los brazos de una persona. La cámara del NAO captura imágenes, la compu detecta la pose con **MediaPipe** (sin GPU) y le devuelve al robot los ángulos de las articulaciones de los brazos.

Basado en [Grottoh/nao_imitate](https://github.com/Grottoh/nao_imitate), que usaba OpenPose en Windows. Este repo lo adapta a Ubuntu y reemplaza OpenPose por MediaPipe, con control 3D de brazos (`ShoulderPitch`, `ShoulderRoll` y `ElbowRoll`).

## Cómo funciona

```
Cámara NAO -> capture.py -> (SFTP) -> compu: MediaPipe -> ángulos -> (SFTP) -> move_arms.py -> brazos
```

Los dos lados se comunican por archivos `.npy` en carpetas buffer. Esto agrega algo de retraso (cerca de un segundo).

## Requisitos

- Ubuntu 22.04 (probado), Python 3.10 en la compu
- NAO con Python 2.7 y NAOqi (probado con un NAO V4)
- Compu y NAO en la misma red
- Internet **solo la primera vez**, para que MediaPipe descargue su modelo

## Instalación (compu)

```bash
git clone https://github.com/LiceaJE/Imitacion-_NAO.git
cd Imitacion-_NAO
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
mkdir -p buffer_images buffer_angles logs
```

Descarga el modelo de MediaPipe (una sola vez, con internet):

```bash
python3 -c "import mediapipe as mp; mp.solutions.pose.Pose(model_complexity=0)"
```

En `rl_external_processor.py`, cambia `path_main_int` a la ruta completa de esta carpeta (con `/` al final).

## Preparar el NAO

La IP se escucha presionando una vez el botón del pecho. Luego:

```bash
ssh nao@IP_DEL_NAO
mkdir -p /home/nao/imitate/buffer_images /home/nao/imitate/buffer_angles /home/nao/imitate/logs
exit
scp nao_scripts/capture.py nao_scripts/move_arms.py nao@IP_DEL_NAO:/home/nao/imitate/
```

Pon al NAO de pie (`StandInit`) y con espacio libre a los lados.

## Ejecución

Se necesitan 4 terminales, en este orden. En las de la compu, activa el venv (`source venv/bin/activate`).

| # | Dónde | Comando | Qué debe pasar |
|---|-------|---------|----------------|
| 1 | NAO (ssh) | `python /home/nao/imitate/capture.py` | Se queda corriendo sin imprimir |
| 2 | Compu | `NAO_IP=IP NAO_PASSWORD=clave python3 rl_external_processor.py` | Imprime `Retrieved file <image_...>` repetido |
| 3 | Compu | `NAO_IP=IP NAO_PASSWORD=clave python3 rl_external_processor.py send_angles` | Imprime `Retrieved image` y `Sent file <angles_...>` |
| 4 | NAO (ssh) | `python /home/nao/imitate/move_arms.py` | Imprime `Listo.` y mueve los brazos |

Párate de frente al NAO, a 1 o 1.5 m, con hombros, codos y muñecas visibles. Para detener, Ctrl+C en cada terminal (empieza por la 4).

## Ver lo que ve el NAO

Con las terminales 1 y 2 corriendo, en otra terminal de la compu:

```bash
python3 view_nao.py
```

Muestra la imagen del NAO con tu esqueleto dibujado y los ángulos calculados. Sirve para encuadrarte. Cierra con `q`. No lo uses al mismo tiempo que la terminal 3.

## Ajustes (al inicio de `process_image.py`)

| Variable | Para qué |
|----------|----------|
| `MIRROR_MODE` | `True`: tu brazo derecho mueve el izquierdo del NAO (espejo) |
| `FLIP_DEPTH` | `True` si adelante/atrás salen invertidos |
| `SMOOTHING` | Sube a 0.7 si el movimiento tiembla (más retraso) |
| `MIN_VISIBILITY` | Umbral para ignorar brazos poco visibles |

## Problemas frecuentes

- **`mediapipe has no attribute 'solutions'`**: instala la versión fijada (`pip install mediapipe==0.10.14`).
- **`Temporary failure in name resolution` al iniciar**: falta internet para descargar el modelo (ver instalación).
- **La terminal 2 imprime solo una vez**: quedaron archivos viejos en el buffer del NAO. Vacíalo con `rm /home/nao/imitate/buffer_images/*` y reinicia `capture.py`.
- **`Non-ASCII character` en el NAO**: Python 2 no acepta acentos sin `# -*- coding: utf-8 -*-` en la primera línea.
- **`REMOTE HOST IDENTIFICATION HAS CHANGED`**: borra la huella vieja con `ssh-keygen -R IP_DEL_NAO`.
- **El brazo no baja o se va hacia atrás**: ajusta `FLIP_DEPTH` y `MIRROR_MODE`.

## Limitaciones

- Con una sola cámara 2D, MediaPipe estima la profundidad y a veces falla.
- No se controla el giro del antebrazo (`ElbowYaw`).
- El NAO solo abre el hombro hasta cerca de 76°.

## Créditos

Proyecto original: [Grottoh/nao_imitate](https://github.com/Grottoh/nao_imitate). Ese repo no incluye licencia.
