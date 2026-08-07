from collections.abc import Sequence
from dataclasses import dataclass
from enum import IntEnum, StrEnum, auto
from math import (
    cos, sin, tan,
    acos, asin, atan,
    radians, degrees, pi,
    sqrt,
    copysign
    )

from build123d import *
from build123d.topology.utils import tuplify
# from build123d.build_commmon import validate_inputs

# Constants for indexing components of vectors.
R = 0       # Cylinder Radius
H = L = 1   # Cylinder Height/Length
X = 0
Y = 1
Z = 2

# Very big and very small length constants.
BIG = 10*M
EPS = 1*MC

# Type alias for vectors (tuples of floats) of various lengths.
VECTOR_MAX_LENGTH = 6
vector = [
    tuple[*[float]*i]
    for i in range(VECTOR_MAX_LENGTH + 1)
    ]

color = str | int | tuple[int | str, float | int]

# Alignment Constants
LEFT_FRONT_BOTTOM  = (Align.MIN,    Align.MIN,    Align.MIN)
LEFT_FRONT         = (Align.MIN,    Align.MIN,    Align.CENTER)
LEFT_FRONT_TOP     = (Align.MIN,    Align.MIN,    Align.MAX)
LEFT_BOTTOM        = (Align.MIN,    Align.CENTER, Align.MIN)
LEFT               = (Align.MIN,    Align.CENTER, Align.CENTER)
LEFT_TOP           = (Align.MIN,    Align.CENTER, Align.MAX)
LEFT_BACK_BOTTOM   = (Align.MIN,    Align.MAX,    Align.MIN)
LEFT_BACK          = (Align.MIN,    Align.MAX,    Align.CENTER)
LEFT_BACK_TOP      = (Align.MIN,    Align.MAX,    Align.MAX)
FRONT_BOTTOM       = (Align.CENTER, Align.MIN,    Align.MIN)
FRONT              = (Align.CENTER, Align.MIN,    Align.CENTER)
FRONT_TOP          = (Align.CENTER, Align.MIN,    Align.MAX)
BOTTOM             = (Align.CENTER, Align.CENTER, Align.MIN)
CENTER             = (Align.CENTER, Align.CENTER, Align.CENTER)
TOP                = (Align.CENTER, Align.CENTER, Align.MAX)
BACK_BOTTOM        = (Align.CENTER, Align.MAX,    Align.MIN)
BACK               = (Align.CENTER, Align.MAX,    Align.CENTER)
BACK_TOP           = (Align.CENTER, Align.MAX,    Align.MAX)
RIGHT_FRONT_BOTTOM = (Align.MAX,    Align.MIN,    Align.MIN)
RIGHT_FRONT        = (Align.MAX,    Align.MIN,    Align.CENTER)
RIGHT_FRONT_TOP    = (Align.MAX,    Align.MIN,    Align.MAX)
RIGHT_BOTTOM       = (Align.MAX,    Align.CENTER, Align.MIN)
RIGHT              = (Align.MAX,    Align.CENTER, Align.CENTER)
RIGHT_TOP          = (Align.MAX,    Align.CENTER, Align.MAX)
RIGHT_BACK_BOTTOM  = (Align.MAX,    Align.MAX,    Align.MIN)
RIGHT_BACK         = (Align.MAX,    Align.MAX,    Align.CENTER)
RIGHT_BACK_TOP     = (Align.MAX,    Align.MAX,    Align.MAX)

# Key spacing constants
@dataclass
class Spacing:
    MX = (19, 19)
    MX_INCH = (19.05, 19.05)
    CHOC = (18, 17)

def cosd(angle: float) -> float:
    return cos(radians(angle))

def sind(angle: float) -> float:
    return sin(radians(angle))

def tand(angle: float) -> float:
    return tan(radians(angle))

def acosd(x: float) -> float:
    return degrees(acos(x))

def asind(x: float) -> float:
    return degrees(asin(x))

def atand(x: float) -> float:
    return degrees(atan(x))

def sign(x):
    return copysign(1, x)

class bcolors(StrEnum):
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class Superellipse(BaseSketchObject):
    """Sketch Object: Superellipse

    Create an superellipse ("squircle") defined by width, height, and order.
    Args:
        width (float): superellipse width
        height (float): superellipse height
        order (float, optional): order of the superellipse. Defaults to 4
        point_count (int, optional): number of points to use for generating the
            superellipse. Defaults to 64
        rotation (float, optional): angle to rotate object. Defaults to 0
        align (Align | tuple[Align, Align], optional): align MIN, CENTER, or MAX
            of object. Defaults to (Align.CENTER, Align.CENTER)
        mode (Mode, optional): combination mode. Defaults to Mode.ADD
    """

    _applies_to = [BuildSketch._tag]

    def __init__(
        self,
        width: float,
        height: float,
        order: float = 4,
        point_count: int = 64,
        rotation: float = 0,
        align: Align | tuple[Align, Align] | None = (Align.CENTER, Align.CENTER),
        mode: Mode = Mode.ADD
    ):
        self.width = width
        self.height_ = height
        self.order = order
        self.point_count = point_count
        self.align = tuplify(align, 2)
        points: list[vector[2]] = []
        for i in range(point_count):
            t = 2*pi*i/point_count
            points.append((
                abs(cos(t))**(2/order) * width * copysign(1, cos(t)) / 2,
                abs(sin(t))**(2/order) * height * copysign(1, sin(t)) / 2,
            ))
        wire = Wire(Edge.make_spline(points, periodic=True)).close()
        face = Face(wire)
        super().__init__(face, rotation, align, mode)


if __name__ == "__main__":
    from ocp_vscode import show
    show(Superellipse(20, 10))