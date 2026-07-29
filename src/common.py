from collections.abc import Sequence
from dataclasses import dataclass
from enum import IntEnum, auto
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

class RectangleBlended(BaseSketchObject):
    """Sketch Object: Rectangle Blended

    Create a rectangle defined by width and height with Bezier blended corners.

    Args:
        width (float): rectangle width
        height (float): rectangle height
        radius (float): fillet pseudo-radius
        continuity (ContinuityLevel, optional): Desired geometric continuity at
            the join:
            - ContinuityLevel.C0: position match only (straight line)
            - ContinuityLevel.C1: match position and tangent direction (cubic
            Bézier)
            - ContinuityLevel.C2: match position, tangent, and curvature
            (quintic Bézier) Defaults to ContinuityLevel.C2.
        tangent_scalars (float, optional) : Scalar multiplier applied to the
            first derivatives at the start and end of the blend curve before
            computing control points. Useful for adjusting the pull/tension of
            the blend without altering the base curves. Defaults to sqrt(2).
        rotation (float, optional): angle to rotate object. Defaults to 0.
        align (Align | tuple[Align, Align], optional): align MIN, CENTER, or MAX
            of object. Defaults to (Align.CENTER, Align.CENTER).
        mode (Mode, optional): combination mode. Defaults to Mode.ADD.
    """

    _applies_to = [BuildSketch._tag]

    def __init__(
        self,
        width: float,
        height: float,
        radius: float,
        continuity: ContinuityLevel = ContinuityLevel.C2,
        tangent_scalar: float = sqrt(2),
        rotation: float = 0,
        align: Align | tuple[Align, Align] | None = (Align.CENTER, Align.CENTER),
        mode: Mode = Mode.ADD
    ):
        context: BuildSketch | None = BuildSketch._get_context(self)
        # validate_inputs(context, self)
        if width <= 2 * radius or height <= 2 * radius:
            raise ValueError("width and height must be > 2*radius")
        self.width = width
        self.rectangle_height = height
        self.radius = radius
        # self.align = tuplify(align, 2)
        w1 = width/2
        h1 = height/2
        w2 = width/2 - radius
        h2 = height/2 - radius
        point_pairs = (
            ((-w1, -h2), (-w1, h2)),
            ((-w2, h1), (w2, h1)),
            ((w1, h2), (w1, -h2)),
            ((w2, -h1), (-w2, -h1))
        )
        edges = [
            Edge.make_line(*point_pair)
            for point_pair in point_pairs
        ]
        outline = Sketch(edges)
        for i in range(-1, len(edges)-1):
            outline += BlendCurve(
                curve0=edges[i],
                curve1=edges[i+1],
                continuity=continuity,
                tangent_scalars=(tangent_scalar*radius,)*2
            )
        face = make_face(outline)
        super().__init__(face, rotation, align, mode)

class RectangleRoundedExt(BaseSketchObject):
    """Sketch Object: Rectangle Rounded

    Create a rectangle defined by width and height with filleted corners.

    Args:
        width (float): rectangle width
        height (float): rectangle height
        radius (float): fillet radius
        rotation (float, optional): angle to rotate object. Defaults to 0
        align (Align | tuple[Align, Align], optional): align MIN, CENTER, or MAX of object.
            Defaults to (Align.CENTER, Align.CENTER)
        mode (Mode, optional): combination mode. Defaults to Mode.ADD
    """

    _applies_to = [BuildSketch._tag]

    def __init__(
        self,
        width: float,
        height: float,
        radius: float | Sequence[float],
        rotation: float = 0,
        align: Align | tuple[Align, Align] | None = (Align.CENTER, Align.CENTER),
        mode: Mode = Mode.ADD,
    ):
        if isinstance(radius, Sequence):
            # Force the list of radii to have 4 items by looping and slicing it.
            self.radius = (radius * 4)[:4]
        else:
            self.radius = [radius] * 4
        for i in range(len(self.radius)):
            if self.radius[i] + self.radius[i-1] > min(width, height):
                raise ValueError("width and height must be > 2*radius")
        self.width = width
        self.rectangle_height = height
        self.align = tuplify(align, 2)

        quadrants = ((-1, -1), (-1, 1), (1, 1), (1, -1))
        corners: list[Face] = []
        for (quadrant, r) in zip(quadrants, self.radius):
            point = (quadrant[X]*(width/2-r), quadrant[Y]*(height/2-r))
            if r > 0:
                corners.append(
                    Pos(point)
                    * Circle(r)
                    )
            else:
                corners.append(Line((0, 0), point))
        face = make_hull([corner.edge() for corner in corners])
        super().__init__(face, rotation, align, mode)