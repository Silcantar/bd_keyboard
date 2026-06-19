from build123d import Align, Color

# Constants for indexing components of vectors.
X = 0
Y = 1
Z = 2

# Unit Conversion constants.
MICRON = UM = 0.001
MILLIMETER = MM = 1
METER = M = 1000
INCH = IN = 25.4
FOOT = FT = 304.8

# Very big and very small length constants.
BIG = 10*M
EPS = 1*UM

# Type alias for vectors (tuples of floats) of various lengths.
VECTOR_MAX_LENGTH = 4
vector = [tuple[[float]*i] for i in range(1, VECTOR_MAX_LENGTH+1)]

ColorLike: typing.TypeAlias = (
    str
    | tuple[str, float | int]
    | tuple[float | int, float | int, float | int]
    | tuple[ float | int, float | int, float | int, float | int ]
    | int
    | tuple[int, int]
    | Color
    # | Quantity_ColorRGBA
)

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

